from typing import List, Optional, Dict
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
import logging
import re
from eagle.agents.base import BasicWorkingMemoryState
from eagle.memory.shared.shared_objects_memory import SharedObjectsMemory
from eagle.agents.react_agent.base import (
    ReactPlanningAgent,
    ReactAgentState,
    ReactPlanningAgentConfigSchema,
    process_graph_stream,
    get_vision_context
)
from eagle.agents.specialists.coding.prompts import prompts_generator
from eagle.utils.restricted_python_utils import SafePythonCompiler
from datetime import datetime, timezone

# Auxiliar functions

def _treat_results(results):
    # Se for tupla e foi retornada diretamente (não embutida)
    if isinstance(results, tuple) and not (len(results) == 1):
        return list(results)  # múltiplos retornos
    else:
        return [results] 
    
def _print_code_error_explanation(code_with_error: str, e: Exception) -> Dict[str, str]:
    # From the exception 'e', use regexp to get the line number after <inline>:
    try:
        if isinstance(e.args[0], str):
            inline_detected = re.findall(r"File \"<inline>\", line (\d+)", e.args[0])
        else:
            inline_detected = ''
    except Exception as b:
        raise b #TODO: Remove this line later, it's just for debugging
    if len(inline_detected) > 0:
        line_number = int(inline_detected[0])
        # get the line of code that raised the error
        line_of_code = code_with_error.split("\n")[line_number - 1]
        # get the error message
        error_message = str(e).split(re.findall(r"File .+, line .*", e.args[0])[-1])[-1]
    else:
        line_of_code = "Could not extract line number from error message. Look at the error message for more details."
        error_message = str(e)
    return f"""
**Code with error:**
```python
{code_with_error}
```
**Line of code that raised the error:**
```python
{line_of_code}
```
**Error message:**
```
{error_message}
```
"""

# Agent config schema
class SafePythonCompilerConfigSchema(BaseModel):
    safe_import_modules: List[str] = Field(default_factory=list, description="List of allowed modules for import.")
    forbidden_modules: List[str] = Field(default_factory=list, description="List of forbidden modules.")
    max_for: int = Field(default=100, description="Maximum number of iterations allowed in a for loop.")
    exec_timeout: int = Field(default=100, description="Maximum execution timeout in seconds.")
    execution_trials: int = Field(default=3, description="Number of execution trials before giving up.")

class CodingReactPlanningAgentConfigSchema(ReactPlanningAgentConfigSchema):
    compiler_configs: SafePythonCompilerConfigSchema = Field(
        default_factory=SafePythonCompilerConfigSchema,
        description="Configuration for the SafePythonCompiler."
    )

    class Config:
        arbitrary_types_allowed = True


# State definitions
class CodingWorkingMemoryState(BasicWorkingMemoryState):
    object_ids: List[str] = Field(default_factory=list, description="List of object IDs relevant to the code generation.")
    previous_error_explanation: Optional[str] = Field(default=None, description="Explanation of the previous error, if any.")
    id_existing_code: Optional[str] = Field(default=None, description="ID of the an existing code to be used, if any.")
    coding_trials: int = Field(default=0, description="Number of coding trials attempted before giving up.")

# Nodes definitions
def coding_observe_node(state: CodingWorkingMemoryState, config: RunnableConfig, store):
    logging.info("Executing coding observe_node")
    node_callback_manager = config.get("configurable").get("observe_node_callback_manager")
    node_callback_manager.on_observe_node_start(state, config)
    observe_node_llm = config.get("configurable").get("observe_node_llm")
    observe_node_prompt_language = config.get("configurable").get("observe_node_llm_prompt_language", "pt-br")
    observe_node_has_vision = config.get("configurable").get("observe_node_has_vision", False)
    observe_node_llm_use_structured_output = config.get("configurable").get("observe_node_llm_use_structured_output", False)
    compiler_config = config.get("configurable").get("compiler_configs")

    shared_memory: SharedObjectsMemory = store.get_memory("shared_objects")
    if not shared_memory:
        raise ValueError("Shared memory not found. Please ensure the shared memory is initialized.")
    chat_id = config.get("configurable").get("chat_id")
    shared_memory_configs = config.get("configurable").get("observe_shared_objects_config")

    
    prompt_data = prompts_generator.generate_prompt(
        prompt_name="observe",
        language=observe_node_prompt_language,
        use_structured_output=observe_node_llm_use_structured_output,
        llm=observe_node_llm if observe_node_llm else None
    )

    prompt = prompt_data["prompt"]
    output_parser = prompt_data["output_parser"]

    tools = config.get("configurable").get("observe_tools", [])

    important_guidelines = config.get("configurable").get("observe_important_guidelines")
    
    window_size = min(config.get("configurable").get("chat_history_window_size"), len(state.messages))
    
    message = None
    inputs = {
        "messages": state.messages[-window_size:],
        "observation": state.observation,
        "plan": state.plan,
        "tools_interactions": {}
    }
    while not isinstance(message, AIMessage):
        # Fetch object summary
        last_memories_metadata = shared_memory.get_last_memories_metadata(chat_id=chat_id, k=shared_memory_configs['k'])
        object_ids = [metadata.object_id for metadata in last_memories_metadata]
        objects_summary = shared_memory.generate_summary_from_object_ids(
            chat_id=chat_id, object_ids=object_ids, language=shared_memory_configs['language']
        )
        vision_context = None
        if observe_node_has_vision and objects_summary:
            vision_context = get_vision_context(
                node_prompt_language=observe_node_prompt_language,
                node_llm=observe_node_llm,
                node_prompt_use_structured_output=observe_node_llm_use_structured_output,
                shared_memory=shared_memory,
                config=config,
                messages=state.messages[-window_size:],
                plan=state.plan,
                observation=state.observation,
                objects_summary=objects_summary,
                important_guidelines=important_guidelines
            )
        
        prompt_partial = prompt.partial(
            agent_name=config.get("configurable").get("agent_name"),
            agent_description=config.get("configurable").get("agent_description"),
            observation=state.observation,
            messages=state.messages[-window_size:],
            plan=state.plan,
            allowed_libraries=compiler_config['safe_import_modules'],
            objects_summary=objects_summary,
            important_guidelines=important_guidelines,
            tools_interactions=inputs.get("tools_interactions", {})
        )

        rendered_messages = prompt_partial.format_messages()

        if vision_context:
            rendered_messages.append(vision_context)

        graph = create_react_agent(
            model=observe_node_llm,
            prompt=ChatPromptTemplate.from_messages(rendered_messages),
            tools=tools,
            state_schema=ReactAgentState
        )
        inputs, message = process_graph_stream(graph, inputs, config)

    response = output_parser.parse(message)

    if response.action == "nothing":
        return {
            "node_from": "observe_node",
            "i_need_a_feedback": False,
            "execution_is_complete": True,
            "messages": [AIMessage(content=response.message, name=config.get("configurable").get("agent_name"))],
        }
    elif response.action == "think":
        return {
            "node_from": "observe_node",
            "i_need_a_feedback": False,
            "execution_is_complete": False,
            "observation": response.message,
            "object_ids": response.object_ids,
        }
    else:
        raise ValueError(f"Invalid action in observe_node response: {response.action}")


def coding_plan_node(state: CodingWorkingMemoryState, config: RunnableConfig, store):
    logging.info("Executing coding plan_node")
    node_callback_manager = config.get("configurable").get("plan_node_callback_manager")
    node_callback_manager.on_plan_node_start(state, config)
    plan_node_llm = config.get("configurable").get("plan_node_llm")
    plan_node_prompt_language = config.get("configurable").get("plan_node_llm_prompt_language", "pt-br")
    plan_node_has_vision = config.get("configurable").get("plan_node_has_vision", False)
    plan_node_llm_use_structured_output = config.get("configurable").get("plan_node_llm_use_structured_output", False)
    compiler_config = config.get("configurable").get("compiler_configs")
    chat_id = config.get("configurable").get("chat_id")

    shared_memory: SharedObjectsMemory = store.get_memory("shared_objects")

    if not shared_memory:
        raise ValueError("Shared memory not found. Please ensure the shared memory is initialized.")
    
    shared_memory_configs = config.get("configurable").get("plan_shared_objects_config")

    prompt_data = prompts_generator.generate_prompt(
        prompt_name="plan",
        language=plan_node_prompt_language,
        use_structured_output=plan_node_llm_use_structured_output,
        llm=plan_node_llm if plan_node_llm else None
    )
    
    prompt = prompt_data["prompt"]
    output_parser = prompt_data["output_parser"]

    tools = config.get("configurable").get("planning_tools", [])

    important_guidelines = config.get("configurable").get("plan_important_guidelines")

    window_size = min(config.get("configurable").get("chat_history_window_size"), len(state.messages))

    message = None
    inputs = {
        "messages": state.messages[-window_size:],
        "observation": state.observation,
        "plan": state.plan,
        "tools_interactions": {}
    }
    while not isinstance(message, AIMessage):
        # Fetch object summary
        last_memories_metadata = shared_memory.get_last_memories_metadata(chat_id=chat_id, k=shared_memory_configs['k'])
        object_ids = [metadata.object_id for metadata in last_memories_metadata]
        objects_summary = shared_memory.generate_summary_from_object_ids(
            chat_id=chat_id, object_ids=object_ids, language=shared_memory_configs['language']
        )
        vision_context = None
        if plan_node_has_vision and objects_summary:
            vision_context = get_vision_context(
                node_prompt_language=plan_node_prompt_language,
                node_llm=plan_node_llm,
                node_prompt_use_structured_output=plan_node_llm_use_structured_output,
                shared_memory=shared_memory,
                config=config,
                messages=state.messages[-window_size:],
                plan=state.plan,
                observation=state.observation,
                objects_summary=objects_summary,
                important_guidelines=important_guidelines
            )

        prompt_partial = prompt.partial(
            agent_name=config.get("configurable").get("agent_name"),
            agent_description=config.get("configurable").get("agent_description"),
            messages=state.messages[-window_size:],
            observation=state.observation,
            plan=state.plan,
            allowed_libraries=compiler_config['safe_import_modules'],
            objects_summary=objects_summary,  # Use generated summary
            previous_error_explanation=state.previous_error_explanation,
            important_guidelines=important_guidelines,
            tools_interactions=inputs.get("tools_interactions", {})
        )

        rendered_messages = prompt_partial.format_messages()

        if vision_context:
            rendered_messages.append(vision_context)

        graph = create_react_agent(
            model=plan_node_llm,
            prompt=ChatPromptTemplate.from_messages(rendered_messages),
            tools=tools,
            state_schema=ReactAgentState
        )
        inputs, message = process_graph_stream(graph, inputs, config)

    response = output_parser.parse(message)

    if response.action == "execute":
        return {
            "node_from": "plan_node",
            "i_need_a_feedback": False,
            "execution_is_complete": False,
            "my_plan_is_complete": True,
            "plan": response.message,
            "object_ids": response.input_object_ids,
            "id_existing_code": response.id_existing_code,
        }
    elif response.action == "nothing":
        return {
            "node_from": "plan_node",
            "i_need_a_feedback": False,
            "execution_is_complete": False,
            "my_plan_is_complete": False,
            "observation": response.message,
        }
    else:
        raise ValueError(f"Invalid action in plan_node response: {response.action}")

def coding_execute_node(state: CodingWorkingMemoryState, config: RunnableConfig, store):
    logging.info("Executing coding execute_node")
    node_callback_manager = config.get("configurable").get("execute_node_callback_manager")
    node_callback_manager.on_execute_node_start(state, config)
    execute_node_llm = config.get("configurable").get("execute_node_llm")
    execute_node_prompt_language = config.get("configurable").get("execute_node_llm_prompt_language", "pt-br")
    execute_node_has_vision = config.get("configurable").get("execute_node_has_vision", False)
    execute_node_llm_use_structured_output = config.get("configurable").get("execute_node_llm_use_structured_output", False)
    shared_memory: SharedObjectsMemory = store.get_memory("shared_objects")
    if not shared_memory:
        raise ValueError("Shared memory not found. Please ensure the shared memory is initialized.")
    chat_id = config.get("configurable").get("chat_id")
    shared_memory_configs = config.get("configurable").get("execute_shared_objects_config")
    compiler_config = config.get("configurable").get("compiler_configs")

    existing_code = None if not state.id_existing_code else shared_memory.get_memory(chat_id=chat_id, object_id=state.id_existing_code).object
    max_execution_trials = compiler_config['execution_trials'] if existing_code is None else 1
    execution_trials = 0

    important_guidelines = config.get("configurable").get("execute_important_guidelines")

    while execution_trials < max_execution_trials:
        
        window_size = min(config.get("configurable").get("chat_history_window_size"), len(state.messages))

        message = None
        inputs = {
            "messages": state.messages[-window_size:],
            "observation": state.observation,
            "plan": state.plan,
            "tools_interactions": {}
        }
        while not isinstance(message, AIMessage):
            # Fetch object summary
            last_memories_metadata = shared_memory.get_last_memories_metadata(chat_id=chat_id, k=shared_memory_configs['k'])
            object_ids = [metadata.object_id for metadata in last_memories_metadata]
            must_cite_objects_summary = ""
            must_cite_object_ids = []
            if state.interaction_initial_datetime:
                for metadata in last_memories_metadata:
                    if datetime.fromtimestamp(metadata.created_at/1000).astimezone(timezone.utc) >= state.interaction_initial_datetime:
                        must_cite_object_ids.append(metadata.object_id)
            
            all_objects_summary = shared_memory.generate_summary_from_object_ids(
                chat_id=chat_id, object_ids=object_ids, language=shared_memory_configs['language']
            )
            objects_summary = shared_memory.generate_summary_from_object_ids(
                chat_id=chat_id, object_ids=list(set(object_ids)-set(must_cite_object_ids)), language=shared_memory_configs['language']
            )
            must_cite_objects_summary = shared_memory.generate_summary_from_object_ids(
                chat_id=chat_id, object_ids=must_cite_object_ids, language=shared_memory_configs['language']
            )
            vision_context = None
            if execute_node_has_vision and objects_summary:
                vision_context = get_vision_context(
                    node_prompt_language=execute_node_prompt_language,
                    node_llm=execute_node_llm,
                    node_prompt_use_structured_output=execute_node_llm_use_structured_output,
                    shared_memory=shared_memory,
                    config=config,
                    messages=state.messages[-window_size:],
                    plan=state.plan,
                    observation=state.observation,
                    objects_summary=all_objects_summary,
                    important_guidelines=important_guidelines
                )
            if existing_code:
                prompt_data = prompts_generator.generate_prompt(
                    prompt_name="execute_with_existing_code",
                    language=execute_node_prompt_language,
                    use_structured_output=execute_node_llm_use_structured_output,
                    llm=execute_node_llm if execute_node_llm else None
                )
                prompt_partial = prompt_data["prompt"].partial(
                    agent_name=config.get("configurable").get("agent_name"),
                    agent_description=config.get("configurable").get("agent_description"),
                    messages=state.messages[-window_size:],
                    allowed_libraries=compiler_config['safe_import_modules'],
                    existing_code=existing_code,
                    observation=state.observation,
                    plan=state.plan,
                    objects_summary=objects_summary,
                    must_cite_objects_summary=must_cite_objects_summary,
                    previous_error_explanation=state.previous_error_explanation,
                    important_guidelines=important_guidelines,
                    tools_interactions=inputs.get("tools_interactions", {})
                )
            else:
                prompt_data = prompts_generator.generate_prompt(
                    prompt_name="execute",
                    language=execute_node_prompt_language,
                    use_structured_output=execute_node_llm_use_structured_output,
                    llm=execute_node_llm if execute_node_llm else None
                )
                prompt_partial = prompt_data["prompt"].partial(
                    agent_name=config.get("configurable").get("agent_name"),
                    agent_description=config.get("configurable").get("agent_description"),
                    messages=state.messages[-window_size:],
                    allowed_libraries=compiler_config['safe_import_modules'],
                    observation=state.observation,
                    plan=state.plan,
                    objects_summary=objects_summary,
                    must_cite_objects_summary=must_cite_objects_summary,
                    previous_error_explanation=state.previous_error_explanation,
                    important_guidelines=important_guidelines,
                    tools_interactions=inputs.get("tools_interactions", {})
                )
            
            output_parser = prompt_data["output_parser"]

            tools = config.get("configurable").get("executing_tools", [])
            rendered_messages = prompt_partial.format_messages()

            if vision_context:
                rendered_messages.append(vision_context)

            graph = create_react_agent(
                model=execute_node_llm,
                prompt=ChatPromptTemplate.from_messages(rendered_messages),
                tools=tools,
                state_schema=ReactAgentState
            )
            inputs, message = process_graph_stream(graph, inputs, config)
        
        response = output_parser.parse(message)

        compiler = SafePythonCompiler(
            safe_import_modules=compiler_config['safe_import_modules'],
            forbidden_modules=compiler_config['forbidden_modules'],
            max_for=compiler_config['max_for'],
            exec_timeout=compiler_config['exec_timeout']
        )

        objects_for_input = [shared_memory.get_memory(chat_id=chat_id, object_id=obj_id).object for obj_id in state.object_ids]
  
        if existing_code:
            code_to_use = existing_code
        else:
            code_to_use = response.code

        try:
            function_name = code_to_use.split("def")[1].split("(")[0].strip()
            compiler.compile(code_to_use)
            execution_result = compiler.exec(function_name, objects_for_input, **response.kwargs)
        except Exception as e:
            if state.previous_error_explanation is None:
                state.previous_error_explanation = _print_code_error_explanation(code_to_use, e)
            else:
                state.previous_error_explanation += "\n\n ---------- new code trial ------------ \n\n" + _print_code_error_explanation(code_to_use, e)
            execution_trials += 1
            logging.error(f"Code execution failed: {str(e)}")
            continue
            
        shared_memory: SharedObjectsMemory = store.get_memory("shared_objects")
        # Storing the function
        if existing_code is None:
            function_id = shared_memory.put_memory(
                chat_id=chat_id,
                object_name=function_name,
                obj=code_to_use,
                description=response.generic_description,
                object_type="python-callable",
            )
        else:
            function_id = state.id_existing_code
        _execution_results = _treat_results(execution_result)
        for i in range(len(response.generated_objects_description)):
            try:
                obj_result = _execution_results[i]
            except IndexError:
                logging.warning(f"Not enough results returned from the function. Expected {len(response.generated_objects_description)}, got {len(_execution_results)}.")
                break
            _name = response.generated_objects_description[i].name
            _description = response.generated_objects_description[i].description
            shared_memory.put_memory(
                chat_id=chat_id,
                object_name=_name,
                obj=obj_result,
                description=_description,
                object_type=type(obj_result).__name__,
                function_generator=function_id,
                objects_args=state.object_ids,
                function_generator_kwargs=response.kwargs
            )
        
        if response.new_code_needed != "":
            return {
                "node_from": "execute_node",
                "i_need_a_feedback": False,
                "execution_is_complete": False,
                "observation": response.new_code_needed,
                "object_ids": [],
                "plan": "",
                "previous_error_explanation": ""
            }
        else:
            return {
                "node_from": "execute_node",
                "i_need_a_feedback": False,
                "execution_is_complete": True,
                "messages": [AIMessage(content=response.message, name=config.get("configurable").get("agent_name"))],
                "observation": "",
                "plan": "",
                "object_ids": [],
                "previous_error_explanation": ""
            }

    return {
        "node_from": "execute_node",
        "i_need_a_feedback": False,
        "execution_is_complete": False,
        "observation": "",
        "previous_error_explanation": state.previous_error_explanation,
        "coding_trials": state.coding_trials + 1,
    }

def route_after_execute_node(state: CodingWorkingMemoryState, config: RunnableConfig, store):
        if state.i_need_a_feedback:
            logging.info("I need a feedback, proceeding to solve it.")
            return "ask_for_feedback"

        if state.execution_is_complete:
            logging.info("Execution is complete, proceeding to end node.")
            return "end"
        else:
            logging.info("Execution not complete, returning to observe node.")
            return "plan"
    

class CodingReactPlanningAgent(ReactPlanningAgent):
    """
    Specialized ReactPlanningAgent for coding tasks.
    """

    OBSERVE_NODE = coding_observe_node
    PLAN_NODE = coding_plan_node
    EXECUTE_NODE = coding_execute_node
    ROUTE_AFTER_EXECUTE_NODE = route_after_execute_node
    WORKING_MEMORY_STATE = CodingWorkingMemoryState
    CONFIG_SCHEMA = CodingReactPlanningAgentConfigSchema
