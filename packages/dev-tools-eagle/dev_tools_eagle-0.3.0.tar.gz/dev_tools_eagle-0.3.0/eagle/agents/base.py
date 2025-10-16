import logging
from typing import Annotated, List, Optional
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from langchain_core.runnables import RunnableConfig
from langgraph.types import interrupt
from langgraph.checkpoint.memory import InMemorySaver
from datetime import datetime, timezone
import uuid

logging.basicConfig(level=logging.INFO)

from langgraph.graph.message import add_messages

# Basic working memory
class BasicWorkingMemoryState(BaseModel):
    messages: Annotated[List, add_messages] = Field(default_factory=list, description="List of messages")
    node_from: str = Field(default="", description="Node from which the state originated")
    observation: str = Field(default="", description="Observation data")
    i_need_a_feedback: bool = Field(default=False, description="Indicates if feedback is needed")
    need_a_feedback_description: str = Field(default="", description="Description of the feedback needed")
    my_plan_is_complete: bool = Field(default=False, description="Indicates if the plan is complete")
    plan: str = Field(default="", description="Plan details")
    execution_is_complete: bool = Field(default=False, description="Indicates if execution is complete")
    interaction_initial_datetime: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Initial datetime of the interaction.")

# Memoris Dicts

class AgentMemories:

    def __init__(self):
        self._memories = {}

    def add_memory(self, name, memory):
        self._memories[name] = memory

    def get_memory(self, name):
        return self._memories.get(name)

    def remove_memory(self, name):
        if name in self._memories:
            del self._memories[name]

    def clear_memories(self):
        self._memories.clear()

# Basic nodes

def basic_observe_node(state: BasicWorkingMemoryState, config: RunnableConfig, store):
    logging.info("Executing observe node")
    logging.info(f"Number of messages in state: {len(state.get('messages', []))}")
    logging.info(f"Agent id: {config.get('configurable', {}).get('agent_id', None)}")
    logging.info("There is a conversation memory!" if store.get_memory('conversation_history') else "There is no conversation memory!")
    logging.info("There is a possible plans and tools memory!" if store.get_memory('possible_plans_and_tools') else "There is no possible plans and tools memory!")
    
    return {
        "node_from": "observe_node"
    }

def basic_route_after_observe(state: BasicWorkingMemoryState, config: RunnableConfig, store):

    if state.i_need_a_feedback:
        logging.info("I need a feedback, proceeding to solve it.")
        return "ask_for_feedback"
    elif state.execution_is_complete:
        logging.info("Execution is complete, proceeding to end node.")
        return "end"
    else:
        logging.info("I don't need a feedback, proceeding to plan.")
        return "plan"

def basic_plan_node(state: BasicWorkingMemoryState, config: RunnableConfig, store):
    
    # Get agent_id from config
    agent_id = config.get('configurable', {}).get('agent_id', None)
    if agent_id is None:
        raise ValueError("agent_id is required in the config")
    
    logging.info("Executing plan node")

    # Check for any possible plans and tools in the memory
    possible_plans_and_tools_memory = store.get_memory("possible_plans_and_tools")
    possible_plans = possible_plans_and_tools_memory.search_memories(agent_id, limit=1)
    if possible_plans:
        logging.info(f"Found possible plans: {possible_plans}")

    return {
        "node_from": "plan_node"
    }

def basic_route_after_plan(state: BasicWorkingMemoryState, config: RunnableConfig, store):

    if state.i_need_a_feedback:
        logging.info("I need a feedback, proceeding to solve it.")
        return "ask_for_feedback"

    if state.my_plan_is_complete:
        logging.info("Plan is complete, proceeding to execute node.")
        return "execute"
    else:
        logging.info("Plan is not complete, returning to observe node.")
        return "observe"

def basic_execute_node(state: BasicWorkingMemoryState, config: RunnableConfig, store):
    
    # Get chat_id from config
    chat_id = config.get('configurable', {}).get('chat_id', None)
    if chat_id is None:
        raise ValueError("chat_id is required in the config")

    logging.info("Executing execute node")
    user_message = state.messages[-1]  # Get the last message from the state
    logging.info(f"Last message: {user_message}")
    
    # Response example

    response = {
        "role": "assistant",
        "content": f"This is a response from the execute node for the message '{user_message.content}'."
    }
    
    # persist the last message to the conversation memory
    conversation_history_memory = store.get_memory("conversation_history")
    conversation_history_memory.put_memory(chat_id, str(uuid.uuid4()), [{"role": "user", "content": user_message.content}, response], user_message.content)

    return {
        "messages": [response],
        "node_from": "execute_node"
    }

def basic_route_after_execute(state: BasicWorkingMemoryState, config: RunnableConfig, store):

    if state.i_need_a_feedback:
        logging.info("I need a feedback, proceeding to solve it.")
        return "ask_for_feedback"

    if state.execution_is_complete:
        logging.info("Execution is complete, proceeding to end node.")
        return "end"
    else:
        logging.info("Execution not complete, returning to observe node.")
        return "observe"
    
def basic_ask_for_feedback_node(state: BasicWorkingMemoryState, config: RunnableConfig, store):
    logging.info("Asking for a feedback")
    feedback = interrupt(state.need_a_feedback_description)
    if feedback in ["siga", "continue", "go ahead"]:
        return {
            "i_need_a_feedback": False,
            "need_a_feedback_description": ""
        }
    elif feedback in ["pare", "stop", "wait"]:
        return {
            "i_need_a_feedback": False,
            "need_a_feedback_description": ""
        }

def basic_route_after_feedback(state: BasicWorkingMemoryState, config: RunnableConfig, store):
    if state.node_from == "observe_node":
        logging.info("Feedback was given for observe node.")
        return "observe"
    elif state.node_from == "plan_node":
        logging.info("Feedback was given for plan node.")
        return "plan"
    elif state.node_from == "execute_node":
        logging.info("Feedback was given for execute node.")
        return "execute"
    else:
        raise ValueError("Invalid node_from value in state after a FEEDBACK execution. Expected 'observe_node', 'plan_node', or 'execute_node'.")

# Config Schema
class BasicAgentConfigurableSchema(BaseModel):
    thread_id: str = Field(default="1", description="Thread ID for the agent")

class BasicAgentMemoryConfigSchema(BaseModel):
    store_class: str = Field(..., description="Class of the memory store")
    embedding_model_name: str = Field(..., description="Name of the embedding model")

class BasicAgentConfigSchema(BaseModel):
    configurable: BasicAgentConfigurableSchema = Field(
        default_factory=BasicAgentConfigurableSchema, 
        description="Configurable schema for the agent"
    )
    agent_id: Optional[str] = Field(default=None, description="Unique identifier for the agent")
    chat_id: Optional[str] = Field(default=None, description="Chat ID associated with the agent")
    agent_name: str = Field(default=None, description="Name of the agent")
    agent_description: str = Field(default=None, description="Description of the agent")
    conversation_store_params: Optional[BasicAgentMemoryConfigSchema] = Field(default=None, description="Parameters for conversation memory store")
    possible_plans_and_tools_store_params: Optional[BasicAgentMemoryConfigSchema] = Field(default=None, description="Parameters for possible plans and tools memory store")

class BasicAgent:

    AGENT_TYPE = "basic"
    OBSERVE_NODE = basic_observe_node
    ROUTE_AFTER_OBSERVE_NODE = basic_route_after_observe
    PLAN_NODE = basic_plan_node
    ROUTE_AFTER_PLAN_NODE = basic_route_after_plan
    EXECUTE_NODE = basic_execute_node
    ROUTE_AFTER_EXECUTE_NODE = basic_route_after_execute
    ASK_FOR_FEEDBACK_NODE = basic_ask_for_feedback_node
    ROUTE_AFTER_FEEDBACK_NODE = basic_route_after_feedback
    CHECKPOINTER = InMemorySaver()
    CONFIG_SCHEMA = BasicAgentConfigSchema
    WORKING_MEMORY_STATE = BasicWorkingMemoryState

    def __init__(self, name: str = '', description: str = ''):
        self._name = name
        self._description = description
        self._memories = AgentMemories()

    def load_memory(self, memory_name: str, memory_object: object):

        self._memories.add_memory(memory_name, memory_object)

    def compile(self):

        # Initialize state graph
        self._graph_builder = StateGraph(self.WORKING_MEMORY_STATE, config_schema=self.CONFIG_SCHEMA)

        # Create the graph
        self._graph_builder.add_node("observe_node", self.OBSERVE_NODE.__func__)
        self._graph_builder.add_node("plan_node", self.PLAN_NODE.__func__)
        self._graph_builder.add_node("execute_node", self.EXECUTE_NODE.__func__)
        self._graph_builder.add_node("ask_for_feedback_node", self.ASK_FOR_FEEDBACK_NODE.__func__)

        # Adding direct edges between nodes
        self._graph_builder.add_edge(START, "observe_node")

        # Adding conditional edges between nodes
        self._graph_builder.add_conditional_edges(
            "observe_node",
            self.ROUTE_AFTER_OBSERVE_NODE.__func__,
            {
                "ask_for_feedback": "ask_for_feedback_node",
                "plan": "plan_node",
                "end": END
            }
        )
        self._graph_builder.add_conditional_edges(
            "plan_node",
            self.ROUTE_AFTER_PLAN_NODE.__func__,
            {
                "ask_for_feedback": "ask_for_feedback_node",
                "execute": "execute_node",
                "observe": "observe_node"
            }
        )
        self._graph_builder.add_conditional_edges(
            "execute_node",
            self.ROUTE_AFTER_EXECUTE_NODE.__func__,
            {
                "ask_for_feedback": "ask_for_feedback_node",
                "observe": "observe_node",
                "plan": "plan_node",
                "end": END
            }
        )
        self._graph_builder.add_conditional_edges(
            "ask_for_feedback_node",
            self.ROUTE_AFTER_FEEDBACK_NODE.__func__,
            {
                "observe": "observe_node",
                "plan": "plan_node",
                "execute": "execute_node"
            }
        )
       
        # compile the graph
        self._compiled_graph = self._graph_builder.compile(checkpointer=self.CHECKPOINTER, store=self.memories)
    
    def _initialize_state(self, state: dict) -> dict:
        """
        Ensure all fields in the state are initialized with default values
        from WORKING_MEMORY_STATE, including nested fields.

        Args:
            state (dict): The input state.

        Returns:
            BasicWorkingMemoryState: The initialized state.
        """
        return self.WORKING_MEMORY_STATE(**state).model_dump()

    def _initialize_config(self, config: dict) -> dict:
        """
        Ensure all fields in the config are initialized with default values
        from CONFIG_SCHEMA, including nested fields.

        Args:
            config (dict): The input config.

        Returns:
            RunnableConfig: The initialized config.
        """
        return self.CONFIG_SCHEMA(**config).model_dump()

    def use_event_and_value(self, event, value):
        logging.info(f"Event: {event} / Value: {value}")
        # Here you can implement what to do with the event and value

    def run(self, state: BasicWorkingMemoryState, config: BasicAgentConfigSchema, stream_mode="update"):
        
        # Ensure the config is initialized
        config = self._initialize_config(config)

        # Setting name and description to config
        if self.name:
            config['agent_name'] = self.name
        if self.description:
            config['agent_description'] = self.description
        
        self._config = config

        # compile graph
        self.compile()
        
        # Ensure the state is fully initialized
        state = self._initialize_state(state)
        for event in self._compiled_graph.stream(state, self._config, stream_mode=stream_mode):
            for value in event.values():
                self.use_event_and_value(event, value)

    ## Agent's name
    @property
    def name(self):
        return self._name
    
    @name.setter
    def name(self, name):
        self._name = name

    ## Agent's description
    @property
    def description(self):
        return self._description
    
    @description.setter
    def description(self, description):
        self._description = description

    ## Agent's memories
    @property
    def memories(self):
        return self._memories
    
    @memories.setter
    def memories(self, memories):
        raise ValueError("Memories cannot be set directly. Use the add_memory method instead.")

    # state snapshot
    @property
    def state_snapshot(self):
        return self._compiled_graph.get_state(self._config)