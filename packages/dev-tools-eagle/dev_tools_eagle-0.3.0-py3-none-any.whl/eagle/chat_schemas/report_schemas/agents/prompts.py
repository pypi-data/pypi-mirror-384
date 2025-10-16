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
from typing import Optional

# Gemeral prompts
YOU_ARE_IN_A_CONVERSATION_WITH_A_REQUESTER_AND_AGENTS_STR_PT_BR = """
Você coordena duas conversas: uma com o **DEMANDANTE** e outra com os **PARTICIPANTES**.
{%- if messages_with_requester %}
Abaixo, sua conversa com o **DEMANDANTE**:
-----------------------------------------------
{%- for message in messages_with_requester %}
{{ message.name }}: {{ message.content }}
{%- endfor %}
-----------------------------------------------
{%- else %}
Nenhuma mensagem trocada com o demandante ainda.
{%- endif %}
{%- if messages_with_agents %}
Abaixo, as mensagens trocadas entre os **PARTICIPANTES**:
-----------------------------------------------------
{%- for message in messages_with_agents %}
{{ message.name }}: {{ message.content }}
{%- endfor %}
-----------------------------------------------------
{%- else %}
Nenhuma mensagem trocada entre os participantes ainda.
{%- endif %}
"""

YOU_ARE_IN_A_CONVERSATION_WITH_A_REQUESTER_AND_AGENTS_STR_EN = """
You are coordinating two conversations: one with the **REQUESTER** and another with the **PARTICIPANTS**.
{%- if messages_with_requester %}
Below is your conversation with the **REQUESTER**:
-----------------------------------------------
{%- for message in messages_with_requester %}
{{ message.name }}: {{ message.content }}
{%- endfor %}
-----------------------------------------------
{%- else %}
No messages exchanged with the requester yet.
{%- endif %}
{%- if messages_with_agents %}
Below are the messages exchanged between the **PARTICIPANTS**:
-----------------------------------------------------
{%- for message in messages_with_agents %}
{{ message.name }}: {{ message.content }}
{%- endfor %}
-----------------------------------------------------
{%- else %}
No messages exchanged between the participants yet.
{%- endif %}
"""

THESE_ARE_THE_SOME_PARTICIPANTS_STR_PT_BR = """
{%- if participants %}
Abaixo, uma descrição dos **PARTICIPANTES**:
-----------------------------------------------------
{%- for participant in participants %}
Nome: {{ participant.name }}
Descrição: {{ participant.description }}


{%- endfor %}
-----------------------------------------------------
{%- endif %}
"""

THESE_ARE_THE_SOME_PARTICIPANTS_STR_EN = """
{%- if participants %}
Below is a description of the **PARTICIPANTS**:
-----------------------------------------------------
{%- for participant in participants %}
Name: {{ participant.name }}
Description: {{ participant.description }}


{%- endfor %}
-----------------------------------------------------
{%- endif %}
"""

MUST_CITE_OBJECTS_SUMMARY_STR_PT_BR = """
{%- if must_cite_objects_summary %}
Caso você decisa ENCERRAR parar a conversa com os **PARTICIPANTES** e dirigir-se para o **DEMANDANTE**, os seguintes objetos devem ser citados na resposta, com os respectivos IDs:
--------------- Objetos a serem citados-----------------
{{ must_cite_objects_summary }}
--------------------------------------------------------
{%- endif %}
"""

MUST_CITE_OBJECTS_SUMMARY_STR_EN = """
{%- if must_cite_objects_summary %}
If you decide to END the the conversation with the **PARTICIPANTS** and direct it to the **REQUESTER**, the following objects must be cited in the response, with their respective IDs:
--------------- Objects to be cited-----------------
{{ must_cite_objects_summary }}
--------------------------------------------------------
{%- endif %}
"""

# Prompt strings
OBSERVE_A_REPORTE_STR_PT_BR = YOU_ARE_IN_A_CONVERSATION_WITH_A_REQUESTER_AND_AGENTS_STR_PT_BR + \
    PLAN_STR_PT_BR + \
    OBSERVATION_STR_PT_BR + \
    OBJECTS_SUMMARY_STR_PT_BR + \
    MUST_CITE_OBJECTS_SUMMARY_STR_PT_BR + \
    TOOLS_INTERACTIONS_STR_PT_BR + \
    THESE_ARE_THE_SOME_PARTICIPANTS_STR_PT_BR + \
    IMPORTANT_GUIDELINES_STR_PT_BR + \
"""
Agora, decida o que fazer a seguir. Você pode escolher entre as seguintes opções:
1. Caso as demandas do DEMANDANTE ainda não tenham sido atendidas **E APENAS CASO TENHAM RELAÇÃO COM UM OU MAIS DOS PARTICIPANTES**, você pode continuar conversando com os **PARTICIPANTES**. Para isso, escolha um dos **PARTICIPANTES** (jamais o **DEMANDANTE**) e faça uma pergunta ou solicitação a ele. Nesse caso, o retorno em json deve ter a seguinte estrutura:
{
    "acao": "continuar_com_participantes",
    "participante": <nome EXATO do **PARTICIPANTE** escolhido e JAMAIS o nome do **DEMANDANTE**>,
    "mensagem": <Mensagem a ser enviada ao **PARTICIPANTE**. Deixe uma string vazia caso não seja necessário enviar uma mensagem específica e baste passar a vez para esse participante.>
}

2. Caso as demandas do DEMANDANTE tenham sido atendidas **OU NÃO TENHAM RELAÇÂO COM QUALQUER DOS PARTICIPANTES** e você já possa responder diretamente por si mesmo, você pode dirigir-se diretamente ao **DEMANDANTE**. Nesse caso, o retorno em json deve ter a seguinte estrutura:
{
    "acao": "continuar_com_demandante",
    "mensagem": <Mensagem a ser enviada ao **DEMANDANTE** com o resumo, principais pontos e conclusões da conversa com os participantes, caso essa conversa tenha acontecido, ou uma resposta direta caso não tenha havido conversa com os participantes.
}

RESPOSTA:
"""

OBSERVE_A_REPORT_STR_EN = YOU_ARE_IN_A_CONVERSATION_WITH_A_REQUESTER_AND_AGENTS_STR_EN + \
    PLAN_STR_EN + \
    OBSERVATION_STR_EN + \
    OBJECTS_SUMMARY_STR_EN + \
    MUST_CITE_OBJECTS_SUMMARY_STR_EN + \
    TOOLS_INTERACTIONS_STR_EN + \
    THESE_ARE_THE_SOME_PARTICIPANTS_STR_EN + \
    IMPORTANT_GUIDELINES_STR_EN + \
"""
Now, decide what to do next. You can choose between the following options:
1. If the REQUESTER's demands have not yet been met, **AND ONLY IF THEY RELATE TO ONE OR MORE OF THE PARTICIPANTS**, you can continue conversing with the PARTICIPANTS. To do this, choose one of the PARTICIPANTS (never the REQUESTER) and ask them a question or make a request. In this case, the return in json must have the following structure:
{
    "action": "continue_with_participants",
    "participant": <EXACT name of the chosen PARTICIPANT and NEVER the name of the REQUESTER>,
    "message": <Message to be sent to the PARTICIPANT. Leave an empty string if no specific message is needed and just pass the turn to that participant.>
}

2. If the REQUESTER's demands have been met **OR DO NOT RELATE TO ANY OF THE PARTICIPANTS** and you can respond directly on your own, you can address the REQUESTER directly. In this case, the return in json must have the following structure:
{
    "action": "continue_with_requester",
    "message": <Message to be sent to the REQUESTER with the summary, main points and conclusions of the conversation with the participants, if this conversation has taken place, or a direct response if no conversation with the participants has occurred.>
}

RESPONSE:
"""

# Prompts
OBSERVE_A_REPORTE_PROMPT_PT_BR = ChatPromptTemplate.from_messages(
    [

        SYSTEM_PROMPT_TUPLE_PT_BR,
        HumanMessagePromptTemplate.from_template(
            template=OBSERVE_A_REPORTE_STR_PT_BR,
            template_format="jinja2"
        ),
    ]
)

OBSERVE_A_REPORT_PROMPT_EN = ChatPromptTemplate.from_messages(
    [
        SYSTEM_PROMPT_TUPLE_EN,
        HumanMessagePromptTemplate.from_template(
            template=OBSERVE_A_REPORT_STR_EN,
            template_format="jinja2"
        ),
    ]
)

NODE_VISION_PROMPT_PT_BR = ChatPromptTemplate.from_messages(
    [
        SYSTEM_PROMPT_TUPLE_PT_BR,
        HumanMessagePromptTemplate.from_template(
            template=YOU_ARE_IN_A_CONVERSATION_WITH_A_REQUESTER_AND_AGENTS_STR_PT_BR + NODE_VISION_PROMPT_STR_PT_BR,
            template_format="jinja2"
        ),
    ]
)

NODE_VISION_PROMPT_EN = ChatPromptTemplate.from_messages(
    [
        SYSTEM_PROMPT_TUPLE_EN,
        HumanMessagePromptTemplate.from_template(
            template=YOU_ARE_IN_A_CONVERSATION_WITH_A_REQUESTER_AND_AGENTS_STR_EN + NODE_VISION_PROMPT_STR_EN,
            template_format="jinja2"
        ),
    ]
)

# Schemas
class ObserveReportPromptOutputSchemaEN(BaseModel):
    action: str = Field(description="Action to be taken by the agent. Can be 'continue_with_participants' or 'continue_with_requester'.")
    participant: Optional[str] = Field(default="", description="Name of the chosen participant, required if action is 'continue_with_participants'.")
    message: str = Field(description="Message to be sent to the participant or requester.")

class ObserveReportePromptOutputSchemaPT_BR(BaseModel):
    acao: str = Field(description="Ação a ser tomada pelo agente. Pode ser 'continuar_com_participantes' ou 'continuar_com_demandante'.")
    participante: Optional[str] = Field(default="", description="Nome do participante escolhido, necessário se a ação for 'continuar_com_participantes'.")
    mensagem: str = Field(description="Mensagem a ser enviada ao participante ou demandante.")

# Output Parsers
class ObserveReportPromptOutputParser(EagleJsonOutputParser):
    """Custom output parser for the observe report prompt. Language: pt-br."""

    CONVERTION_SCHEMA: ClassVar[dict] = {
        "pt-br": {
            "class_for_parsing": ObserveReportePromptOutputSchemaPT_BR,
            "convertion_schema": {
                "acao": {
                    "target_key": "action",
                    "value_mapping": {
                        "continuar_com_participantes": "continue_with_participants",
                        "continuar_com_demandante": "continue_with_requester"
                    }
                },
                "participante": {
                    "target_key": "participant",
                    "value_mapping": {}  # No value mapping needed for this key
                },
                "mensagem": {
                    "target_key": "message",
                    "value_mapping": {}  # No value mapping needed for this key
                }
            }
        },
        "en": {
            "class_for_parsing": ObserveReportPromptOutputSchemaEN,
            "convertion_schema": {
                "action": {
                    "target_key": "action",
                    "value_mapping": {
                        "continue_with_participants": "continue_with_participants",
                        "continue_with_requester": "continue_with_requester"
                    }
                },
                "participant": {
                    "target_key": "participant",
                    "value_mapping": {}  # No value mapping needed for this key
                },
                "message": {
                    "target_key": "message",
                    "value_mapping": {}  # No value mapping needed for this key
                }
            }
        },
    }

    TARGET_SCHEMA: BaseModel = ObserveReportPromptOutputSchemaEN

# Prompts dictionary
_PROMPTS_DICT = {
    "observe_report": {
        "output_parser": ObserveReportPromptOutputParser,
        "languages": {
            "pt-br": OBSERVE_A_REPORTE_PROMPT_PT_BR,
            "en": OBSERVE_A_REPORT_PROMPT_EN,
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

# Initialize the PromptGenerator with the prompts dictionary
prompt_generator = PromptGenerator(prompts_dict=_PROMPTS_DICT)