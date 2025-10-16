from eagle.agents.base import BasicAgent
from eagle.chat_schemas.base import BasicChatState, BasicChatSchema
from langchain_core.runnables import RunnableConfig
from pydantic import Field

# Enrich the state with the next speaker
class ReportChatState(BasicChatState):
    participant: str = Field(default="", description="Name of the next participant to speak.")

class ReportChatSchema(BasicChatSchema):
    """
    A subclass of BasicChatSchema to implement a report schema model.
    The supervisor acts as the moderator, and other agents are participants.
    """

    WORKING_MEMORY_STATE = ReportChatState

    def __init__(self, moderator: BasicAgent):
        super().__init__(moderator)
    
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
            
            # config mapping
            supervisor_config = config.get("configurable").get("agent_configs").get(self._supervisor.name)

            # state mapping
            supervisor_state = {
                "messages_with_requester": state.messages_with_requester,
                "messages_with_agents":state.messages_with_agents,
                "participants": state.participants,
                "interaction_initial_datetime": state.interaction_initial_datetime,
            }

            # run the 
            supervisor.run(supervisor_state, supervisor_config)

            # update state with agent response
            agent_snapshot = supervisor.state_snapshot

            if agent_snapshot.values["flow_direction"] == "agents":
                return {
                    "flow_direction": "agents",
                    "messages_with_agents": agent_snapshot.values["messages_with_agents"],
                    "participant": agent_snapshot.values["participant"]
                }
            elif agent_snapshot.values["flow_direction"] == "requester":
                return {
                    "flow_direction": "requester",
                    "messages_with_requester": agent_snapshot.values["messages_with_requester"],
                }
            else:
                raise ValueError("Invalid flow direction from supervisor node in chat schema.")
            
        return supervisor_node

    def next_participant_node(self, state: ReportChatState, config: RunnableConfig) -> str:

        """
        Get the next agent node based on the 'participant' key in the state.
        """
        # Get the agent name from the state
        next_participant_name = state.participant
        
        # Get the callable name for the agent node
        return next_participant_name

    def add_multiagent_edges(self):
        """
        Add edges between the nodes in the multi-agent subgraph to model a report schema.
        The supervisor directs to the agent node specified by the 'participant' key in the state,
        and the agent node returns to the supervisor.
        """
        # Get supervisor callable_name
        supervisor_callable_name = self._set_node_callable_name(self._supervisor.name)

        # Add conditional edge from supervisor to the agent specified in 'participant'
        self._graph_builder.add_conditional_edges(
            "next_agent_node",
            self.next_participant_node,
            {agent_name: f"{self._set_node_callable_name(agent_name)}_node" for agent_name in self._multiagent_index.keys() if agent_name != self._supervisor.name}
        )

        # Add edge from each agent node back to the supervisor
        for agent_name in self._multiagent_index.keys():
            if agent_name != self._supervisor.name:
                callable_name = self._set_node_callable_name(agent_name)
                self._graph_builder.add_edge(
                    f"{callable_name}_node", f"{supervisor_callable_name}_node"
                )

