from eagle.utils.output import convert_schema
from eagle.utils.prompt_utils import PromptGenerator, EagleJsonOutputParser
from eagle.agents.react_agent.prompts import (
    OBJECTS_SUMMARY_STR_EN,
    OBJECTS_SUMMARY_STR_PT_BR,
    OBSERVATION_STR_PT_BR,
    OBSERVATION_STR_EN,
    PLAN_STR_PT_BR,
    PLAN_STR_EN,
    TOOLS_INTERACTIONS_STR_PT_BR,
    TOOLS_INTERACTIONS_STR_EN,
    SYSTEM_PROMPT_TUPLE_PT_BR,
    SYSTEM_PROMPT_TUPLE_EN,
    IMPORTANT_GUIDELINES_STR_PT_BR,
    IMPORTANT_GUIDELINES_STR_EN,
    NODE_VISION_PROMPT_STR_PT_BR,
    NODE_VISION_PROMPT_STR_EN,
    NodeVisionPromptOutputParser
)
from pydantic import BaseModel, Field
from typing import ClassVar
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate

# --- MUDANÇA: Os blocos de texto genéricos são os mesmos do Report ---
# Mantemos a estrutura de apresentação do contexto para o LLM.
from eagle.chat_schemas.report_schemas.agents.prompts import (
    YOU_ARE_IN_A_CONVERSATION_WITH_A_REQUESTER_AND_AGENTS_STR_PT_BR,
    YOU_ARE_IN_A_CONVERSATION_WITH_A_REQUESTER_AND_AGENTS_STR_EN,
    THESE_ARE_THE_SOME_PARTICIPANTS_STR_PT_BR,
    THESE_ARE_THE_SOME_PARTICIPANTS_STR_EN,
    MUST_CITE_OBJECTS_SUMMARY_STR_PT_BR,
    MUST_CITE_OBJECTS_SUMMARY_STR_EN
)


# --- MUDANÇA: Novo prompt de instrução para o esquema Relay ---
OBSERVE_A_RELAY_STR_PT_BR = YOU_ARE_IN_A_CONVERSATION_WITH_A_REQUESTER_AND_AGENTS_STR_PT_BR + \
    PLAN_STR_PT_BR + \
    OBSERVATION_STR_PT_BR + \
    OBJECTS_SUMMARY_STR_PT_BR + \
    MUST_CITE_OBJECTS_SUMMARY_STR_PT_BR + \
    TOOLS_INTERACTIONS_STR_PT_BR + \
    THESE_ARE_THE_SOME_PARTICIPANTS_STR_PT_BR + \
    IMPORTANT_GUIDELINES_STR_PT_BR + \
"""
Você está coordenando uma interação em ciclo entre os participantes.
{%- if messages_with_requester %}
Aqui está sua conversa com o DEMANDANTE:
-----------------------------------------------
{%- for message in messages_with_requester %}
{{ message.name }}: {{ message.content }}
{%- endfor %}
-----------------------------------------------
{%- else %}
Nenhuma mensagem com o demandante ainda.
{%- endif %}
{%- if messages_with_agents %}
Aqui estão as mensagens trocadas entre os PARTICIPANTES:
-----------------------------------------------------
{%- for message in messages_with_agents %}
{{ message.name }}: {{ message.content }}
{%- endfor %}
-----------------------------------------------------
{%- else %}
Nenhuma mensagem trocada entre os participantes ainda.
{%- endif %}

Agora, decida o que fazer a seguir. Você pode escolher entre:
1. **Continuar o ciclo**, se acredita que os participantes podem aprimorar ou complementar os resultados.
2. **Encerrar**, caso os resultados estejam satisfatórios para responder ao demandante.

Se decidir **continuar**, a estrutura da resposta em JSON deve ser:
{
    "acao": "continuar_relay",
    "mensagem": <Mensagem opcional a ser enviada aos participantes, ou string vazia se não houver>
}

Se decidir **encerrar**, a estrutura da resposta em JSON deve ser:
{
    "acao": "encerrar_relay",
    "mensagem": <Mensagem de encerramento, resumo ou resposta final ao demandante>
}

RESPOSTA:
"""

OBSERVE_A_RELAY_STR_EN = YOU_ARE_IN_A_CONVERSATION_WITH_A_REQUESTER_AND_AGENTS_STR_EN + \
    PLAN_STR_EN + \
    OBSERVATION_STR_EN + \
    OBJECTS_SUMMARY_STR_EN + \
    MUST_CITE_OBJECTS_SUMMARY_STR_EN + \
    TOOLS_INTERACTIONS_STR_EN + \
    THESE_ARE_THE_SOME_PARTICIPANTS_STR_EN + \
    IMPORTANT_GUIDELINES_STR_EN + \
"""
You are coordinating a cyclic interaction among participants.
{%- if messages_with_requester %}
Here is your conversation with the REQUESTER:
-----------------------------------------------
{%- for message in messages_with_requester %}
{{ message.name }}: {{ message.content }}
{%- endfor %}
-----------------------------------------------
{%- else %}
No messages with the requester yet.
{%- endif %}
{%- if messages_with_agents %}
Here are the messages exchanged among PARTICIPANTS:
-----------------------------------------------------
{%- for message in messages_with_agents %}
{{ message.name }}: {{ message.content }}
{%- endfor %}
-----------------------------------------------------
{%- else %}
No messages exchanged among the participants yet.
{%- endif %}

Now, decide what to do next. You can choose between:
1. **Continue the relay cycle** if not all of the participants have provided their input yet.
2. **End the relay** if all of the participants have provided their input.

If you decide to **continue**, your response in JSON must be:
{
    "action": "continue_relay",
    "message": <Optional message to send to participants, or an empty string if no message>
}

If you decide to **end**, your response in JSON must be:
{
    "action": "end_relay",
    "message": <Final message, summary, or answer to the requester>
}

RESPONSE:
"""

# Prompts
OBSERVE_A_RELAY_PROMPT_PT_BR = ChatPromptTemplate.from_messages(
    [
        SYSTEM_PROMPT_TUPLE_PT_BR,
        HumanMessagePromptTemplate.from_template(
            template=OBSERVE_A_RELAY_STR_PT_BR,
            template_format="jinja2"
        ),
    ]
)

OBSERVE_A_RELAY_PROMPT_EN = ChatPromptTemplate.from_messages(
    [
        SYSTEM_PROMPT_TUPLE_EN,
        HumanMessagePromptTemplate.from_template(
            template=OBSERVE_A_RELAY_STR_EN,
            template_format="jinja2"
        ),
    ]
)

# A parte de visão é genérica e pode ser reaproveitada
NODE_VISION_PROMPT_PT_BR = ChatPromptTemplate.from_messages(
    [SYSTEM_PROMPT_TUPLE_PT_BR, HumanMessagePromptTemplate.from_template(template=YOU_ARE_IN_A_CONVERSATION_WITH_A_REQUESTER_AND_AGENTS_STR_PT_BR + NODE_VISION_PROMPT_STR_PT_BR, template_format="jinja2")])
NODE_VISION_PROMPT_EN = ChatPromptTemplate.from_messages(
    [SYSTEM_PROMPT_TUPLE_EN, HumanMessagePromptTemplate.from_template(template=YOU_ARE_IN_A_CONVERSATION_WITH_A_REQUESTER_AND_AGENTS_STR_EN + NODE_VISION_PROMPT_STR_EN, template_format="jinja2")])


# --- MUDANÇA: Novo Schema de Saída, mais simples ---
class ObserveRelayPromptOutputSchemaEN(BaseModel):
    action: str = Field(description="Action to be taken. Can be 'continue_relay' to start a new cycle, or 'end_relay' to end.")
    message: str = Field(description="Message to be sent to the participants or the requester.")

class ObserveRelayPromptOutputSchemaPT_BR(BaseModel):
    acao: str = Field(description="Ação a ser tomada. Pode ser 'continuar_relay' para iniciar novo ciclo, ou 'encerrar_relay' para encerrar.")
    mensagem: str = Field(description="Mensagem a ser enviada aos participantes ou ao demandante.")


# --- MUDANÇA: Novo Parser para o Schema simplificado ---
class ObserveRelayPromptOutputParser(EagleJsonOutputParser):
    """Parser para o prompt do supervisor do esquema Relay."""

    CONVERTION_SCHEMA: ClassVar[dict] = {
        "pt-br": {
            "class_for_parsing": ObserveRelayPromptOutputSchemaPT_BR,
            "convertion_schema": {
                "acao": {
                    "target_key": "action",
                    "value_mapping": {
                        "continuar_relay": "continue_relay", "encerrar_relay": "end_relay",
                    }
                },
                "mensagem": {"target_key": "message", "value_mapping": {}}
            }
        },
        "en": {
            "class_for_parsing": ObserveRelayPromptOutputSchemaEN,
            "convertion_schema": {
                "action": {
                    "target_key": "action",
                    "value_mapping": {
                        "continue_relay": "continue_relay", "end_relay": "end_relay",
                    }
                },
                "message": {"target_key": "message", "value_mapping": {}}
            }
        },
    }

    TARGET_SCHEMA: BaseModel = ObserveRelayPromptOutputSchemaEN


# --- MUDANÇA: Novo dicionário de prompts para o Relay ---
_PROMPTS_DICT = {
    "observe_relay": {
        "output_parser": ObserveRelayPromptOutputParser,
        "languages": {
            "pt-br": OBSERVE_A_RELAY_PROMPT_PT_BR,
            "en": OBSERVE_A_RELAY_PROMPT_EN,
        },
    },
    "node_vision": {
        "output_parser": NodeVisionPromptOutputParser,
        "languages": {
            "pt-br": NODE_VISION_PROMPT_PT_BR,
            "en": NODE_VISION_PROMPT_EN,
        },
    },
}

prompt_generator = PromptGenerator(prompts_dict=_PROMPTS_DICT)
