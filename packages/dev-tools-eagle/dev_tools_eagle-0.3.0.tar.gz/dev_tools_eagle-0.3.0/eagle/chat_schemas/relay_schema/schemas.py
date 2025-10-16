from eagle.chat_schemas.base import BasicChatSchema, BasicChatState
from eagle.agents.base import BasicAgent
from langchain_core.runnables import RunnableConfig
from langgraph.graph import START, END
from pydantic import Field
from typing import List

class RelayChatState(BasicChatState):
    current_participant_index: int = Field(default=0, description="Index do participante atual no ciclo.")

class RelayChatSchema(BasicChatSchema):
    """
    Implementa um esquema de conversa circular (Relay) que herda a estrutura e o ciclo de vida do BasicChatSchema.
    """

    WORKING_MEMORY_STATE = RelayChatState

    def __init__(self, moderator: BasicAgent):
        super().__init__(moderator)
    

    def supervisor_agent_node_generator(self) -> callable:
        def supervisor_node(state: RelayChatState, config: RunnableConfig, store) -> RelayChatState:
            supervisor = self._multiagent_index[self._supervisor.name]
            supervisor_config = config.get("configurable").get("agent_configs").get(self._supervisor.name)

            supervisor_state = {
                "messages_with_requester": state.messages_with_requester,
                "messages_with_agents": state.messages_with_agents,
                "participants": state.participants,
                "interaction_initial_datetime": state.interaction_initial_datetime,
            }

            supervisor.run(supervisor_state, supervisor_config)

            agent_snapshot = supervisor.state_snapshot

            if agent_snapshot.values["flow_direction"] == "agents":
                return {
                    "flow_direction": "agents",
                    "messages_with_agents": agent_snapshot.values["messages_with_agents"],
                    # Reinicia o ciclo ao decidir por uma nova rodada
                    "current_participant_index": 0
                }
            elif agent_snapshot.values["flow_direction"] == "requester":
                return {
                    "flow_direction": "requester",
                    "messages_with_requester": agent_snapshot.values["messages_with_requester"],
                }
            else:
                raise ValueError("Invalid flow direction from supervisor node in chat schema.")
            
        return supervisor_node

    # --- MUDANÇA: Lógica de arestas reescrita para o modelo da base.py ---
    def add_multiagent_edges(self):
        supervisor_callable_name = self._set_node_callable_name(self._supervisor.name)

        participants = [k for k in self._multiagent_index.keys() if k != self._supervisor.name]
        participants = [f"{self._set_node_callable_name(p)}_node" for p in participants]

        self._graph_builder.add_conditional_edges(f"{supervisor_callable_name}_node", 
                                                  self.after_supervisor_node,
                                                  {
                                                      "agents": participants[0],
                                                      "end": END
                                                  })

        for agent_name in self._multiagent_index.keys():
            if agent_name != self._supervisor.name:

                # Adiciona arestas sequenciais entre os participantes
                for i in range(len(participants) - 1):
                    self._graph_builder.add_edge(participants[i], participants[i + 1])

                # Opcional: fecha o ciclo para o supervisor, se necessário
                self._graph_builder.add_edge(participants[-1], f"{supervisor_callable_name}_node")
    
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

        self._graph_builder.add_edge(START, f"{supervisor_callable_name}_node")
        """ self._graph_builder.add_conditional_edges(
            f"{supervisor_callable_name}_node",
            self.after_supervisor_node,
            {   
                "end": END,
            }
        ) """

        self.add_multiagent_edges()

        self._compiled_graph = self._graph_builder.compile(checkpointer=self.CHECKPOINTER)