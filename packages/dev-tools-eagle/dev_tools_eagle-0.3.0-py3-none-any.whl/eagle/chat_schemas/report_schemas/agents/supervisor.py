from eagle.agents.react_agent.base import ReactPlanningAgent, ReactAgentState, process_graph_stream
from eagle.chat_schemas.base import BasicChatSupervisorWorkingMemoryState
from eagle.memory.shared.shared_objects_memory import SharedObjectsMemory
from eagle.chat_schemas.report_schemas.agents.prompts import prompt_generator
from eagle.utils.image_utils import object_to_image_url
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from pydantic import Field
from datetime import datetime, timezone

class ReportModeratorReactAgentState(ReactAgentState):

    messages_with_requester: list = []
    messages_with_agents: list = []
    participants: list = []

class ReportModeratorSimpleAgentWorkingMemoryState(BasicChatSupervisorWorkingMemoryState):
    participant: str = Field(default="", description="Name of the next participant to speak.")

# Vision function
def get_vision_context(
        node_prompt_language,
        node_llm,
        node_prompt_use_structured_output,
        shared_memory: SharedObjectsMemory,
        config,
        messages_with_requester,
        messages_with_agents,
        plan,
        observation,
        objects_summary,
        important_guidelines
    ):

    prompt_data = prompt_generator.generate_prompt(
        prompt_name="node_vision",
        language=node_prompt_language,
        llm=node_llm,
        use_structured_output=node_prompt_use_structured_output,
    )

    prompt = prompt_data["prompt"]
    output_parser = prompt_data["output_parser"]

    message = None
    while not isinstance(message, AIMessage):
        graph = create_react_agent(
        model=node_llm,
            prompt=prompt.partial(
                agent_name=config.get("configurable").get("agent_name"),
                agent_description=config.get("configurable").get("agent_description"),
                messages_with_requester=messages_with_requester,
                messages_with_agents=messages_with_agents,
                observation=observation,
                plan=plan,
                objects_summary=objects_summary,
                important_guidelines=important_guidelines,
            ),
            tools=[],
            state_schema=ReactAgentState,
        )
        inputs = {
            "messages": messages_with_requester,
            "observation": observation,
            "plan": plan,
            "tools_interactions": {}
        }
        inputs, message = process_graph_stream(graph, inputs, config)
    
    if message.type == "ai":
        response = output_parser.parse(message)
    else:
        raise ValueError(f"Expected AI message but got: {message.__class__}")
    
    chat_id = config.get("configurable").get("chat_id")

    shared_objects = [shared_memory.get_memory(chat_id, _id) for _id in response.ids if shared_memory.get_memory(chat_id, _id) is not None]

    context_list = []
    for shared_object in shared_objects:
        b64_url = object_to_image_url(shared_object.object, format="JPEG")
        if b64_url:
            context_list.append(
                {
                    "type": "text",
                    "text": f"Image ID: {shared_object.metadata.object_id}\nImage Name: {shared_object.metadata.name}\nImage Description: {shared_object.metadata.description}"
                }
            )
            context_list.append(
                {
                    "type": "image_url",
                    "image_url": {"url": b64_url}
                }
            )
    
    if context_list:
        return HumanMessage(
            content=context_list
        )
    else:
        return None

def observe_node(state: ReportModeratorSimpleAgentWorkingMemoryState, config: RunnableConfig, store) -> ReportModeratorSimpleAgentWorkingMemoryState:
    """
    Process the observation phase, make a decision, and update the state.
    """
    node_callback_manager = config.get("configurable").get("observe_node_callback_manager")
    node_callback_manager.on_observe_node_start(state, config)
    observe_node_llm = config.get("configurable").get("observe_node_llm")
    observe_node_prompt_language = config.get("configurable").get("observe_node_llm_prompt_language")
    observe_node_has_vision = config.get("configurable").get("observe_node_has_vision", False)
    observe_node_llm_use_structured_output = config.get("configurable").get("observe_node_llm_use_structured_output", False)
    prompt_data = prompt_generator.generate_prompt(
        prompt_name="observe_report",
        language=observe_node_prompt_language,
        use_structured_output=observe_node_llm_use_structured_output,
        llm=observe_node_llm if observe_node_llm else None
    )
    
    prompt = prompt_data["prompt"]
    output_parser = prompt_data["output_parser"]
    
    chat_id = config.get("configurable").get("chat_id")

    shared_memory_configs = config.get("configurable").get("execute_shared_objects_config")
    shared_memory: SharedObjectsMemory = store.get_memory("shared_objects")

    
    tools = config.get("configurable").get("executing_tools", [])

    important_guidelines = config.get("configurable").get("observe_important_guidelines")

    window_size = min(config.get("configurable").get("chat_history_window_size"), len(state.messages_with_requester))

    # Process the graph with the inputs
    message = None
    inputs = {
        "messages": [state.messages_with_requester[-1]],
        "messages_with_requester": state.messages_with_requester[-window_size:],
        "messages_with_agents": state.messages_with_agents,
        "participants": state.participants,
        "plan": state.plan,
        "observation": state.observation,
        "tools_interactions": {}
    }
    while not isinstance(message, AIMessage):
        # Fetch object summary
        objects_summary = ""
        must_cite_objects_summary = ""

        if shared_memory:
            last_memories_metadata = shared_memory.get_last_memories_metadata(chat_id=chat_id, k=shared_memory_configs['k'])
            object_ids = [metadata.object_id for metadata in last_memories_metadata]
            must_cite_object_ids = []
            if state.interaction_initial_datetime:
                for metadata in last_memories_metadata:
                    if datetime.fromtimestamp(metadata.created_at / 1000).astimezone(timezone.utc) >= state.interaction_initial_datetime:
                        must_cite_object_ids.append(metadata.object_id)
            objects_summary = shared_memory.generate_summary_from_object_ids(
                chat_id=chat_id, object_ids=list(set(object_ids)-set(must_cite_object_ids)), language=shared_memory_configs['language']
            )
            must_cite_objects_summary = shared_memory.generate_summary_from_object_ids(
                chat_id=chat_id, object_ids=must_cite_object_ids, language=shared_memory_configs['language']
            )
            vision_context = None
            if observe_node_has_vision and objects_summary:
                vision_context = get_vision_context(
                    node_prompt_language=observe_node_prompt_language,
                    node_llm=observe_node_llm,
                    node_prompt_use_structured_output=observe_node_llm_use_structured_output,
                    shared_memory=shared_memory,
                    config=config,
                    messages_with_requester=state.messages_with_requester[-window_size:],
                    messages_with_agents=state.messages_with_agents,
                    plan=state.plan,
                    observation=state.observation,
                    objects_summary=objects_summary,
                    important_guidelines=important_guidelines
                )
        else:
            vision_context = None
                    
        prompt_partial = prompt.partial(
            agent_name=config.get("configurable").get("agent_name"),
            agent_description=config.get("configurable").get("agent_description"),
            messages_with_requester=state.messages_with_requester[-window_size:],
            messages_with_agents=state.messages_with_agents,
            observation=state.observation,
            plan=state.plan,
            participants=state.participants,
            objects_summary=objects_summary,
            must_cite_objects_summary=must_cite_objects_summary,
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
            state_schema=ReportModeratorReactAgentState
        )
        inputs, message = process_graph_stream(graph, inputs, config)

    # Access the 'role' attribute directly instead of using subscript notation
    if message.type == "ai":
        response = output_parser.parse(message)
    else:
        raise ValueError(f"Expected AI message but got: {message.__class__}")
    
    if response.action == "continue_with_requester":
        return {
            "execution_is_complete": True,
            "messages_with_requester": [
                AIMessage(content=response.message, name=config.get("configurable").get("agent_name"))
            ],
            "flow_direction": "requester"
        }
    elif response.action == "continue_with_participants":
        if response.message:
            messages_with_agents = [
                AIMessage(content=response.message, name=config.get("configurable").get("agent_name")) 
            ]
        else:
            messages_with_agents = []
        return {
            "execution_is_complete": True,
            "messages_with_agents": messages_with_agents,
            "flow_direction": "agents",
            "participant": response.participant
        }
    else:
        raise ValueError(f"Invalid action in response: {response.action}")

class ReportModeratorSimpleAgent(ReactPlanningAgent):
    """
    A subclass of ReactPlanningAgent to implement a report schema moderator agent.
    The agent is responsible for managing the flow of the report and ensuring that each participant has a chance to speak.
    """

    AGENT_TYPE = "report_moderator"
    WORKING_MEMORY_STATE = ReportModeratorSimpleAgentWorkingMemoryState
    OBSERVE_NODE = observe_node
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)