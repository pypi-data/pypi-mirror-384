from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph
from typing import Annotated, List, Dict, Any
from langgraph.graph.message import add_messages
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
from eagle.agents.base import BasicAgent, BasicWorkingMemoryState
from eagle.agents.react_agent.base import  ReactPlanningAgentConfigSchema
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import logging

# Callback Manager for Chats
class ChatStateCallbackManager:
    def __init__(self):
        self.callbacks = {
            "on_supervisor_end": [],
            "on_agent_end": []
        }

    def register_callback(self, event_type, callback_fn):
        """Permite registrar callbacks adicionais antes de rodar o app."""
        self.callbacks[event_type].append(callback_fn)

    def on_supervisor_end(self, state, config):
        for callback in self.callbacks["on_supervisor_end"]:
            callback(state, config)

    def on_agent_end(self, state, config):
        for callback in self.callbacks["on_agent_end"]:
            callback(state, config)

# States
class Participant(BaseModel):
    name: str = Field(default="", description="Name of the participant")
    description: str = Field(default="", description="Description of the participant")

class BasicChatState(BaseModel):
    """
    State schema for the chat graph.
    """
    messages_with_requester: Annotated[List, Field(default_factory=list), add_messages] = Field(
        default_factory=list, description="Messages exchanged with the requester"
    )
    messages_with_agents: Annotated[List, Field(default_factory=list), add_messages] = Field(
        default_factory=list, description="Messages exchanged with agents"
    )
    participants: List[Participant] = Field(default_factory=list, description="Names of the agents in the conversation")
    flow_direction: str = Field(default="requester", description="Direction of the conversation flow")
    interaction_initial_datetime: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Initial datetime of the interaction.")

class BasicChatSupervisorWorkingMemoryState(BasicWorkingMemoryState):
    messages_with_requester: Annotated[List, Field(default_factory=list), add_messages] = Field(
        default_factory=list, description="Messages exchanged with the requester"
    )
    messages_with_agents: Annotated[List, Field(default_factory=list), add_messages] = Field(
        default_factory=list, description="Messages exchanged with agents"
    )
    participants: List[Participant] = Field(default_factory=list, description="Names of the agents in the conversation")
    flow_direction: str = Field(default="requester", description="Direction of the conversation flow")

# Config schemas
class BasicChatConfigurableSchema(BaseModel):
    thread_id: str = Field(default="1", description="Thread ID for the chat")

class BasicChatConfigSchema(BaseModel):
    configurable: BasicChatConfigurableSchema = Field(default_factory=BasicChatConfigurableSchema, description="Configurable schema for the chat")
    chat_id: str = Field(default=None, description="Unique identifier for the chat")
    chat_name: str = Field(default=None, description="Name of the chat")
    chat_description: str = Field(default=None, description="Description of the chat")
    agent_configs: Dict[str, Any] = Field(
        ..., description="Configuration for agents participating in the chat"
    )
    callback_manager: ChatStateCallbackManager = Field(
        default=ChatStateCallbackManager(),
        description="Callback manager for the chat."
    )

    def model_dump(self, *args, **kwargs):
        data = super().model_dump(*args, **kwargs)
        # Serialize LLM objects to dictionaries
        for field_name in ['agent_configs']:
            data[field_name] = getattr(self, field_name)
        return data

    class Config:
        arbitrary_types_allowed = True

# Node functions

class BasicChatSchema:
    """
    Class to define a LangGraph-based graph for multi-agent conversation models.
    """

    CHECKPOINTER = InMemorySaver()
    CONFIG_SCHEMA = BasicChatConfigSchema
    WORKING_MEMORY_STATE = BasicChatState

    def __init__(self, supervisor: BasicAgent):
        self._graph_builder = StateGraph(self.WORKING_MEMORY_STATE, config_schema=self.CONFIG_SCHEMA)
        self._compiled_graph = None
        self._supervisor = supervisor
        self._multiagent_index = {
            self._supervisor.name: self._supervisor
        }

    def _set_node_callable_name(self, node_name: str):

        callable_name = node_name.lower().replace(" ", "_").replace("-", "_")

        return callable_name

    def add_agent(self, agent: BasicAgent):
        """
        Add an agent to the multi-agent index.
        """
        self._multiagent_index[agent.name] = agent
    
    def after_supervisor_node(self, state: BasicChatState, config: RunnableConfig, store) -> BasicChatState:
        """
        Function to handle actions after supervisor interaction.
        """
        # Get the callback manager from config
        callback_manager = config.get("configurable").get("callback_manager")
        callback_manager.on_supervisor_end(state, config)
        flow_direction = state.flow_direction
        if flow_direction is None:
            raise ValueError("Flow direction is not set in the state.")
        if flow_direction == "agents":
            return "agents"
        elif flow_direction == "requester":
            return "end"
    
    def supervisor_agent_node_generator(self) -> callable:
        """
        Function to generate a callable for the supervisor agent.
        """
        def supervisor_node(state: BasicChatState, config: RunnableConfig, store) -> BasicChatState:
            """
            Function to handle interaction with the supervisor agent.
            """
            # Logic for supervisor interaction
            supervisor = self._multiagent_index[self._supervisor.name]
            
            # state mapping
            supervisor_state = {
                "messages_with_requester": state.messages_with_requester,
                "participants": state.participants,
                "interaction_initial_datetime": state.interaction_initial_datetime,
            }

            # config mapping
            supervisor_config = config.get("configurable").get("agent_configs").get(self._supervisor.name)

            # run the 
            supervisor.run(supervisor_state, supervisor_config)

            # update state with agent response
            agent_snapshot = supervisor.state_snapshot

            if agent_snapshot.values["flow_direction"] == "agents":
                return {
                    "flow_direction": "agents",
                    "messages_with_agents": agent_snapshot.values["messages_with_agents"],
                }
            elif agent_snapshot["flow_direction"] == "requester":
                return {
                    "flow_direction": "requester",
                    "messages_with_requester": agent_snapshot.values["messages_with_requester"],
                }
            else:
                raise ValueError("Invalid flow direction from supervisor node in chat schema.")
            
        return supervisor_node

    def multiagent_agent_node_generator(self, agent_name: str) -> callable:
        """
        Function to generate a callable for each agent in the multi-agent index.
        """
        def agent_node(state: BasicChatState, config: RunnableConfig, store) -> BasicChatState:
            """
            Function to handle interaction with a specific agent.
            """
            # Get the callback manager from config
            callback_manager = config.get("configurable").get("callback_manager")
            
            # Logic for agent interaction
            agent = self._multiagent_index[agent_name]
            
            # state mapping
            agent_state = {
                "messages": state.messages_with_agents,
                "interaction_initial_datetime": state.interaction_initial_datetime,
            }

            # config mapping
            agent_config = config.get("configurable").get("agent_configs")[agent_name]

            # run the 
            agent.run(agent_state, agent_config)

            callback_manager.on_agent_end(state, config)

            # update state with agent response
            agent_snapshot = agent.state_snapshot

            return {
                "messages_with_agents": agent_snapshot.values["messages"],
            }
            
        return agent_node
    
    def add_multiagent_edges(self):
        """
        Add edges between the nodes in the multi-agent subgraph depending on the logic of the conversation.
        """
        raise NotImplementedError("This method should be implemented in subclasses.")

    def next_agent_node(self, state, config):

        return {}

    def compile(self):
        """
        Build the graph structure for the chat schema.
        """

        # Add all agent nodes to the graph
        for agent_name in self._multiagent_index.keys():
            if agent_name != self._supervisor.name:
                callable_name = self._set_node_callable_name(agent_name)
                self._graph_builder.add_node(
                    f"{callable_name}_node",
                    self.multiagent_agent_node_generator(agent_name),
                )
        
        # Add the supervisor node to the graph
        # Get supervisor callable_name
        supervisor_callable_name = self._set_node_callable_name(self._supervisor.name)
        self._graph_builder.add_node(
            f"{supervisor_callable_name}_node",
            self.supervisor_agent_node_generator(),
        )

        # Add next agent node
        self._graph_builder.add_node(
            "next_agent_node",
            self.next_agent_node
        )


        self._graph_builder.add_edge(START, f"{supervisor_callable_name}_node")
        self._graph_builder.add_conditional_edges(
            f"{supervisor_callable_name}_node",
            self.after_supervisor_node,
            {   
                "agents": "next_agent_node",
                "end": END,
            }
        )

        self.add_multiagent_edges()

        self._compiled_graph = self._graph_builder.compile(checkpointer=self.CHECKPOINTER)

    def _initialize_config(self, config: dict) -> RunnableConfig:
        """
        Ensure all fields in the config are initialized with default values
        from CONFIG_SCHEMA, including nested fields.

        Args:
            config (dict): The input config.

        Returns:
            RunnableConfig: The initialized config.
        """
        return self.CONFIG_SCHEMA(**config).model_dump()

    def _initialize_state(self, state: dict) -> dict:
        """
        Ensure all fields in the state are initialized with default values
        from WORKING_MEMORY_STATE, including nested fields.

        Args:
            state (dict): The input state.

        Returns:
            BasicChatState: The initialized state.
        """
        state['participants'] = [
            Participant(name=agent.name, description=agent.description) for agent in self._multiagent_index.values() if agent.name != self._supervisor.name
        ]
        return self.WORKING_MEMORY_STATE(**state).model_dump()

    def use_event_and_value(self, event, value):
        logging.info(f"Event: {event} / Value: {value}")
        # Here you can implement what to do with the event and value

    def run(self, state: BasicChatState, config: RunnableConfig, store, stream_mode="update") -> BasicChatState:
        """
        Run the conversation model with the given state and config.
        """
        # Ensure the config is initialized
        config = self._initialize_config(config)
        self._config = config

        if not self._compiled_graph:
            self.compile()

        state = self._initialize_state(state)
        for event in self._compiled_graph.stream(state, self._config, stream_mode=stream_mode):
            for value in event.values():
                self.use_event_and_value(event, value)

    # Properties
    # state snapshot
    @property
    def state_snapshot(self):
        return self._compiled_graph.get_state(self._config)
