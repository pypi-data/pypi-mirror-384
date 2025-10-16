from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from pydantic import BaseModel, Field
from eagle.utils.prompt_utils import PromptGenerator, EagleJsonOutputParser
from typing import ClassVar, List

# Schemas
## Node Vision Output Schemas
class NodeVisionPromptOutputSchemaEN(BaseModel):
    ids: List[str] = Field(
        description="IDs of objects you want to visualize as image."
    )

class NodeVisionPromptOutputSchemaPT_BR(BaseModel):
    ids: List[str] = Field(
        description="IDs dos objetos que você quer visualizar como imagem."
    )

## Specific Node Output Schemas
class ObserveNodeFinalUserPromptOutputSchemaEN(BaseModel):
    action: str = Field(description="Ação a ser tomada pelo agente. Pode ser 'nothing', 'answer' ou 'think'.")
    message: str = Field(description="Mensagem a ser retornada pelo agente. Pode ser uma resposta direta ou um raciocínio interno.")

class ObserveNodeFinalUserPromptOutputSchemaPT_BR(BaseModel):
    acao: str = Field(description="Ação a ser tomada pelo agente. Pode ser 'nada', 'responder' ou 'pensar'.")
    mensagem: str = Field(description="Mensagem a ser retornada pelo agente. Pode ser uma resposta direta ou um raciocínio interno.")

class PlanNodeFinalUserPromptOutputSchemaEN(BaseModel):
    action: str = Field(description="Action to be taken by the agent. Can be 'execute' or 'nothing'.")
    message: str = Field(description="Message to be returned by the agent. Can be a plan or internal reasoning.")

class PlanNodeFinalUserPromptOutputSchemaPT_BR(BaseModel):
    acao: str = Field(description="Ação a ser tomada pelo agente. Pode ser 'executar' ou 'nada'.")
    mensagem: str = Field(description="Mensagem a ser retornada pelo agente. Pode ser um plano ou um raciocínio interno.")

class ExecuteNodeFinalUserPromptOutputSchemaEN(BaseModel):
    action: str = Field(description="Action to be taken by the agent. Can be 'success' or 'failure'.")
    message: str = Field(description="Message to be returned by the agent. Can describe the result or the reason for failure.")

class ExecuteNodeFinalUserPromptOutputSchemaPT_BR(BaseModel):
    acao: str = Field(description="Ação a ser tomada pelo agente. Pode ser 'sucesso' ou 'falha'.")
    mensagem: str = Field(description="Mensagem a ser retornada pelo agente. Pode descrever o resultado ou o motivo da falha.")

# Output Parsers
## Node vision output parsers
class NodeVisionPromptOutputParser(EagleJsonOutputParser):

    CONVERTION_SCHEMA: ClassVar[dict] = {
        "pt-br": {
            "class_for_parsing": NodeVisionPromptOutputSchemaPT_BR,
            "convertion_schema": {
                "ids": {
                    "target_key": "ids",
                    "value_mapping": {}
                }
            }
        },
        "en": {
            "class_for_parsing": NodeVisionPromptOutputSchemaEN,
            "convertion_schema": {
                "ids": {
                    "target_key": "ids",
                    "value_mapping": {}
                }
            }
        }
    }

    TARGET_SCHEMA: BaseModel = NodeVisionPromptOutputSchemaEN

## Node specific output parsers
class ObserveNodeFinalUserPromptOutputParser(EagleJsonOutputParser):
    """Custom output parser for the observe node final user prompt. Language: pt-br."""

    CONVERTION_SCHEMA: ClassVar[dict] = {
        "pt-br": {
            "class_for_parsing": ObserveNodeFinalUserPromptOutputSchemaPT_BR,
            "convertion_schema": {
                "acao": {
                    "target_key": "action",
                    "value_mapping": {
                        "nada": "nothing",
                        "responder": "answer",
                        "pensar": "think"
                    }
                },
                "mensagem": {
                    "target_key": "message",
                    "value_mapping": {}  # No value mapping needed for this key
                }
            }
        },
        "en": {
            "class_for_parsing": ObserveNodeFinalUserPromptOutputSchemaEN,
            "convertion_schema": {
                "action": {
                    "target_key": "action",
                    "value_mapping": {
                        "nothing": "nothing",
                        "answer": "answer",
                        "think": "think"
                    }
                },
                "message": {
                    "target_key": "message",
                    "value_mapping": {}  # No value mapping needed for this key
                }
            }
        },
    }

    TARGET_SCHEMA: BaseModel =ObserveNodeFinalUserPromptOutputSchemaEN

class PlanNodeFinalUserPromptOutputParser(EagleJsonOutputParser):
    """Custom output parser for the plan node final user prompt. Language: pt-br."""

    CONVERTION_SCHEMA: ClassVar[dict] = {
        "pt-br": {
            "class_for_parsing": PlanNodeFinalUserPromptOutputSchemaPT_BR,
            "convertion_schema": {
                "acao": {
                    "target_key": "action",
                    "value_mapping": {
                        "executar": "execute",
                        "nada": "nothing"
                    }
                },
                "mensagem": {
                    "target_key": "message",
                    "value_mapping": {}  # No value mapping needed for this key
                }
            }
        },
        "en": {
            "class_for_parsing": PlanNodeFinalUserPromptOutputSchemaEN,
            "convertion_schema": {
                "action": {
                    "target_key": "action",
                    "value_mapping": {
                        "execute": "execute",
                        "nothing": "nothing"
                    }
                },
                "message": {
                    "target_key": "message",
                    "value_mapping": {}  # No value mapping needed for this key
                }
            }
        },
    }
    
    TARGET_SCHEMA: BaseModel =PlanNodeFinalUserPromptOutputSchemaEN

class ExecuteNodeFinalUserPromptOutputParser(EagleJsonOutputParser):
    """Custom output parser for the execute node final user prompt. Language: pt-br."""

    CONVERTION_SCHEMA: ClassVar[dict] = {
        "pt-br": {
            "class_for_parsing": ExecuteNodeFinalUserPromptOutputSchemaPT_BR,
            "convertion_schema": {
                "acao": {
                    "target_key": "action",
                    "value_mapping": {
                        "sucesso": "success",
                        "falha": "failure"
                    }
                },
                "mensagem": {
                    "target_key": "message",
                    "value_mapping": {}  # No value mapping needed for this key
                }
            }
        },
        "en": {
            "class_for_parsing": ExecuteNodeFinalUserPromptOutputSchemaEN,
            "convertion_schema": {
                "action": {
                    "target_key": "action",
                    "value_mapping": {
                        "success": "success",
                        "failure": "failure"
                    }
                },
                "message": {
                    "target_key": "message",
                    "value_mapping": {}  # No value mapping needed for this key
                }
            }
        },
    }

    TARGET_SCHEMA: BaseModel = ExecuteNodeFinalUserPromptOutputSchemaEN

# General prompt strings

## PT_BR

OBJECTS_SUMMARY_STR_PT_BR = """
{%- if objects_summary %}
Abaixo está um resumo dos últimos objetos criados e as relações entre eles:
------------------ Sumário de Objetos ------------------
{{ objects_summary }}
--------------------------------------------------------
{%- endif %}
"""

MUST_CITE_OBJECTS_SUMMARY_STR_PT_BR = """
{%- if must_cite_objects_summary %}
Os seguintes objetos devem ser citados na resposta, com os respectivos IDs:
--------------- Objetos a serem citados-----------------
{{ must_cite_objects_summary }}
--------------------------------------------------------
{%- endif %}
"""

PLAN_STR_PT_BR = """
{%- if plan %}
Você recentemente pensou em um plano para resolver isso. Aqui está o plano que você anotou:
----------------------- Plano --------------------------
{{ plan }}
--------------------------------------------------------
{%- endif %}
"""

OBSERVATION_STR_PT_BR = """
{%- if observation %}
Há pouco, você anotou a seguinte observação:
-------------------- Observação ------------------------
{{ observation }}
--------------------------------------------------------
{%- endif %}
"""

TOOLS_INTERACTIONS_STR_PT_BR = """
{%- if tools_interactions %}
Suas últimas interações com ferramentas foram as seguintes:
------------- Interações com Ferramentas --------------
{%- for interaction in tools_interactions.values() %}
{%- if interaction['response'] %}
-----
Foi chamada a ferramenta "{{ interaction['call']['name']}}" com os seguintes parâmetros:
{{ interaction['call']['args'] }}
... com a resposta:
{{ interaction['response'] }}
-----
{%- endif %}
{%- endfor %}
--------------------------------------------------------
{%- endif %}
"""

IMPORTANT_GUIDELINES_STR_PT_BR = """
{%- if important_guidelines %}
-------------- Diretrizes Importantes -----------------
{{ important_guidelines }}
-------------------------------------------------------
{%- endif %}
"""

## EN
OBJECTS_SUMMARY_STR_EN = """
{%- if objects_summary %}
Below is a summary of the last created objects and the relationships between them:
------------------ Objects Summary ------------------
{{ objects_summary }}
-----------------------------------------------------
{%- endif %}
"""

MUST_CITE_OBJECTS_SUMMARY_STR_EN = """
{%- if must_cite_objects_summary %}
The following objects must be cited in the response, with their respective IDs:
--------------- Objects to be cited -----------------
{{ must_cite_objects_summary }}
-----------------------------------------------------
{%- endif %}
"""

PLAN_STR_EN = """
{%- if plan %}
You recently thought of a plan to solve this. Here is the plan you noted:
----------------------- Plan ------------------------
{{ plan }}
-----------------------------------------------------
{%- endif %}
"""

OBSERVATION_STR_EN = """
{%- if observation %}
You noted the following observation a moment ago:
-------------------- Observation --------------------
{{ observation }}
-----------------------------------------------------
{%- endif %}
"""

TOOLS_INTERACTIONS_STR_EN = """
{%- if tools_interactions %}
Your last interactions with tools were as follows:
------------- Tool Interactions --------------------
{%- for interaction in tools_interactions.values() %}
{%- if interaction['response'] %}
-----
Called tool "{{ interaction['call']['name']}}" with the following parameters:
{{ interaction['call']['args'] }}
... with the response:
{{ interaction['response'] }}
-----
{%- endif %}
{%- endfor %}
-----------------------------------------------------
{%- endif %}
"""

IMPORTANT_GUIDELINES_STR_EN = """
{%- if important_guidelines %}
-------------- Important Guidelines -----------------
{{ important_guidelines }}
------------------------------------------------------
{%- endif %}
"""

# Prompt strings
YOU_ARE_IN_A_CONVERSATION_STR_PT_BR = """
Você está participando de uma conversa. O estado atual da conversa é o seguinte:
-----------------------------------------------------
{%- for message in messages %}
{{ message.name }}: {{ message.content }}
{%- endfor %}
-----------------------------------------------------
"""

YOU_ARE_IN_A_CONVERSATION_STR_EN = """
You are participating in a conversation. The current state of the conversation is as follows:
-----------------------------------------------------
{%- for message in messages %}
{{ message.name }}: {{ message.content }}
{%- endfor %}
-----------------------------------------------------
"""

OBSERVE_NODE_PROMPT_STR_PT_BR = """
Observe essa conversa e pense na tua especialidade.
""" + \
    PLAN_STR_PT_BR + \
    OBSERVATION_STR_PT_BR + \
    OBJECTS_SUMMARY_STR_PT_BR + \
    TOOLS_INTERACTIONS_STR_PT_BR + \
    IMPORTANT_GUIDELINES_STR_PT_BR + \
"""
Agora, retorne com uma das seguintes saídas:

1. Se você não tem ABSOLUTAMENTE nada a dizer ou nada a contribuir à conversa, retorne um json com a seguinte estrutura:
{
    "acao": "nada",
    "mensagem": <Sua mensagem aqui.>
}
2. Se você tem CERTEZA ABSOLUTA que tem algo a responder diretamente, sem antes tentar raciocinar mais profundamente e fazer um planejamento, avaliando possíveis ferramentas úteis etc, retorne retorne um json com a seguinte estrutura:
{
    "acao": "responder",
    "mensagem": <Sua resposta direta aqui.>
}

3. Se você acha que tem algo a responder, mas não tem CERTEZA ABSOLUTA e precisa antes raciocinar mais profundamente, retorne retorne um json com a seguinte estrutura:
{
    "acao": "pensar",
    "mensagem": <Anote aqui suas ideias, raciocínios internos, perguntas e reflexões sobre o que você poderia fazer para ajudar a resolver essa conversa. Sempre dirija-se a si mesmo nesses pensamentos, nunca endereçando uma pergunta ao usuário.>
}

RESPOSTA:
"""

NODE_VISION_PROMPT_STR_PT_BR = """
Observe essa conversa e pense na tua especialidade.
"""+ \
    PLAN_STR_PT_BR + \
    OBSERVATION_STR_PT_BR + \
    OBJECTS_SUMMARY_STR_PT_BR + \
    IMPORTANT_GUIDELINES_STR_PT_BR + \
"""
Determine quais dos objetos citados você considera **REALMENTE** importantes visualizar como imagem para entender melhor o contexto.
Tua resposta deve ter o seguinte formato json:
{
    "ids": [...ids dos objetos REALMENTE IMPORTANTES a serem visualizados como imagem para melhor contextualização.]
}

RESPOSTA:
"""

OBSERVE_NODE_PROMPT_STR_EN = """
Observe this conversation and consider your expertise.
""" + \
    PLAN_STR_EN + \
    OBSERVATION_STR_EN + \
    OBJECTS_SUMMARY_STR_EN + \
    TOOLS_INTERACTIONS_STR_EN + \
    IMPORTANT_GUIDELINES_STR_EN + \
"""
Now, return with one of the following outputs:

1. If you have ABSOLUTELY nothing to say or nothing to contribute to the conversation, OR if you need to ask something, return a JSON with the following structure:
{
    "action": "nothing",
    "message": <Your message or question here.>
}

2. If you are ABSOLUTELY CERTAIN that you have something to respond directly, without first reasoning more deeply and planning, evaluating possible useful tools, etc., return a JSON with the following structure:
{
    "action": "answer",
    "message": <Your direct response here.>
}

3. If you think you have something to respond, it should be a good idea to reason more deeply first and enrich your response. If you agree, return a JSON with the following structure:
{
    "action": "think",
    "message": <Write here your ideas, internal reasoning, questions, and reflections on what you could do to help resolve this conversation. Always address yourself in these thoughts, never directing a question to the user.>
}

RESPONSE:
"""

PLAN_NODE_PROMPT_STR_PT_BR = """
Observando essa conversa e pensando na tua especialidade, você deve fazer um planejamento para resolver o problema apresentado. Caso tenha ferramentas úteis para isso, você pode utilizá-las quantas vezes precisar até ter um plano suficiente para prosseguir.
""" + \
    PLAN_STR_PT_BR + \
    OBSERVATION_STR_PT_BR + \
    OBJECTS_SUMMARY_STR_PT_BR + \
    TOOLS_INTERACTIONS_STR_PT_BR + \
    IMPORTANT_GUIDELINES_STR_PT_BR + \
"""
Agora, retorne com uma das seguintes saídas:
1. Caso tenha pensado em um plano, retorne um json com a seguinte estrutura:
{
    "acao": "executar",
    "mensagem": <Escreva aqui seu PLANO para prosseguir.>
}
O PLANO deve ter o formato de to-do list, com passos numerados, se houver mais de um passo, indicando o que já foi feito e o que falta fazer. Siga EXATAMENTE o padrão abaixo:
```
1. Descrição do passo 1... (ok), se já foi feito, (pendente), se falta fazer, (problemático), se há um problema que impede a execução do passo.
2. Descrição do passo 2... (ok), se já foi feito, (pendente), se falta fazer, (problemático), se há um problema que impede a execução do passo.
... etc.

Problemas:
1. Descrição detalhada do problema do passo 1, se marcado como problemático.
2. Descrição detalhada do problema do passo 2, se marcado como problemático.
... etc.
```

2. Caso não tenha realmente conseguido pensar em um plano, retorne um json com a seguinte estrutura:
{
    "acao": "nada",
    "mensagem": <Coloque aqui suas ideias, raciocínios internos, perguntas e reflexões sobre o que você poderia fazer para ajudar a resolver essa conversa. Sempre dirija-se a si mesmo nesses pensamentos, nunca endereçando uma pergunta ao usuário.>
}

RESPOSTA:
"""

PLAN_NODE_PROMPT_STR_EN = """
Observing this conversation and considering your expertise, you must create a plan to solve the presented problem. If you have useful tools for this, you can use them as many times as needed until you have a sufficient plan to proceed.
""" + \
    PLAN_STR_EN + \
    OBSERVATION_STR_EN + \
    OBJECTS_SUMMARY_STR_EN + \
    TOOLS_INTERACTIONS_STR_EN + \
    IMPORTANT_GUIDELINES_STR_EN + \
"""
Now, return with one of the following outputs:
1. If you have thought of a plan, return a JSON with the following structure:
{
    "action": "execute",
    "message": <write here your PLAN to proceed, its steps, if any, and the tools you will use, if any. In this plan, do not mention the tools used to make the present plan.>
}
The PLAN should be in the format of a to-do list, with numbered steps, if there is more than one step, indicating what has already been done and what remains to be done. Follow EXACTLY the pattern below:
```
1. Description of step 1... (ok), if it has already been done, (pending), if it remains to be done, (problematic), if there is a problem that prevents the execution of the step.
2. Description of step 2... (ok), if it has already been done, (pending), if it remains to be done, (problematic), if there is a problem that prevents the execution of the step.
... etc.

Problems:
1. Detailed description of the problem of step 1, if marked as problematic.
2. Detailed description of the problem of step 2, if marked as problematic.
... etc.
```

2. If you have not really managed to think of a plan, return a JSON with the following structure:
{
    "action": "nothing",
    "message": <Write here your ideas, internal reasoning, questions, and reflections on what you could do to help resolve this conversation. Always address yourself in these thoughts, never directing a question to the user.>
}

RESPONSE:
"""

EXECUTE_NODE_PROMPT_STR_PT_BR = """
Observando essa conversa e pensando na tua especialidade, você deve responder à conversa. Caso tenha ferramentas úteis para isso, você pode utilizá-las para conseguir responder à conversa.
Não as utilize repetidamente com os mesmos parâmetros de entrada, a não ser que a resposta da ferramenta indique que houve um erro que uma repetição poderia corrigir e, mesmo assim, não utilize mais do que duas vezes a mesma ferramenta com os mesmos parâmetros.
""" + \
    PLAN_STR_PT_BR + \
    OBSERVATION_STR_PT_BR + \
    OBJECTS_SUMMARY_STR_PT_BR + \
    MUST_CITE_OBJECTS_SUMMARY_STR_PT_BR + \
    TOOLS_INTERACTIONS_STR_PT_BR + \
    IMPORTANT_GUIDELINES_STR_PT_BR + \
"""
Agora, retorne com uma das seguintes saídas:
1. Caso possa responder à conversa, retorne um json com a seguinte estrutura:
{   
    "acao": "sucesso",
    "mensagem": <Sua resposta aqui.>
}

2. Caso tenha observado alguma impossibilidade de responder, retorne um json com a seguinte estrutura:
{
    "acao": "falha",
    "mensagem": <Descreva aqui, em detalhes, os motivos da falha, o que um novo plano deveria levar em conta e o que, da resposta, já foi concluído (inclua em detalhes a informação já obtida), mesmo que incompletamente.>
}

RESPOSTA:
"""

EXECUTE_NODE_PROMPT_STR_EN = """
Observing this conversation and considering your expertise, you must respond to the conversation.
Do not use the same tool repeatedly with the same input parameters, unless the tool's response indicates that there was an error that a repetition could fix and, even then, do not use the same tool more than twice with the same parameters.
""" + \
    PLAN_STR_EN + \
    OBSERVATION_STR_EN + \
    OBJECTS_SUMMARY_STR_EN + \
    MUST_CITE_OBJECTS_SUMMARY_STR_EN + \
    TOOLS_INTERACTIONS_STR_EN + \
    IMPORTANT_GUIDELINES_STR_EN + \
"""
Now, return with one of the following outputs:
1. If you can respond to the conversation, return a JSON with the following structure:
{
    "action": "success",
    "message": <Your response here.>
}
2. If you have observed any impossibility to respond, return a JSON with the following structure:
{
    "action": "failure",
    "message": <Describe here, in detail, the reasons for the failure, what a new plan should take into account, and what, from the response, has already been concluded (include in details the information already obtained), even if incompletely.>
}

RESPONSE:
"""

NODE_VISION_PROMPT_STR_EN = """
Observe this conversation and consider your expertise.
""" + \
    PLAN_STR_EN + \
    OBSERVATION_STR_EN + \
    OBJECTS_SUMMARY_STR_EN + \
    IMPORTANT_GUIDELINES_STR_EN + \
"""
Determine which of the mentioned objects you consider REALLY important to visualize as an image to better understand the context.
Your response should have the following JSON format:
{
    "ids": [...ids of the REALLY IMPORTANT objects to be visualized as an image for better contextualization.]
}
RESPONSE:
"""

# Prompts

SYSTEM_PROMPT_TUPLE_PT_BR = ("system", "Seus dados:\nNome: {agent_name}\nDescrição: {agent_description}")
SYSTEM_PROMPT_TUPLE_EN = ("system", "Your data:\nName: {agent_name}\nDescription: {agent_description}")

OBSERVE_NODE_PROMPT_PT_BR = ChatPromptTemplate.from_messages(
    [
        SYSTEM_PROMPT_TUPLE_PT_BR,
        HumanMessagePromptTemplate.from_template(
            template=YOU_ARE_IN_A_CONVERSATION_STR_PT_BR + OBSERVE_NODE_PROMPT_STR_PT_BR,
            template_format="jinja2"
        ),
    ]
)

OBSERVE_NODE_PROMPT_EN = ChatPromptTemplate.from_messages(
    [
        SYSTEM_PROMPT_TUPLE_EN,
        HumanMessagePromptTemplate.from_template(
            template=YOU_ARE_IN_A_CONVERSATION_STR_EN + OBSERVE_NODE_PROMPT_STR_EN,
            template_format="jinja2"
        ),
    ]
)

PLAN_NODE_PROMPT_PT_BR = ChatPromptTemplate.from_messages(
    [
        SYSTEM_PROMPT_TUPLE_PT_BR,
        HumanMessagePromptTemplate.from_template(
            template=YOU_ARE_IN_A_CONVERSATION_STR_PT_BR + PLAN_NODE_PROMPT_STR_PT_BR,
            template_format="jinja2"
        ),
    ]
)

PLAN_NODE_PROMPT_EN = ChatPromptTemplate.from_messages(
    [
        SYSTEM_PROMPT_TUPLE_EN,
        HumanMessagePromptTemplate.from_template(
            template=YOU_ARE_IN_A_CONVERSATION_STR_EN + PLAN_NODE_PROMPT_STR_EN,
            template_format="jinja2"
        ),
    ]
)

EXECUTE_NODE_PROMPT_PT_BR = ChatPromptTemplate.from_messages(
    [
        SYSTEM_PROMPT_TUPLE_PT_BR,
        HumanMessagePromptTemplate.from_template(
            template=YOU_ARE_IN_A_CONVERSATION_STR_PT_BR + EXECUTE_NODE_PROMPT_STR_PT_BR,
            template_format="jinja2"
        ),
    ]
)

EXECUTE_NODE_PROMPT_EN = ChatPromptTemplate.from_messages(
    [
        SYSTEM_PROMPT_TUPLE_EN,
        HumanMessagePromptTemplate.from_template(
            template=YOU_ARE_IN_A_CONVERSATION_STR_EN + EXECUTE_NODE_PROMPT_STR_EN,
            template_format="jinja2"
        ),
    ]
)

NODE_VISION_PROMPT_PT_BR = ChatPromptTemplate.from_messages(
    [
        SYSTEM_PROMPT_TUPLE_PT_BR,
        HumanMessagePromptTemplate.from_template(
            template=YOU_ARE_IN_A_CONVERSATION_STR_PT_BR + NODE_VISION_PROMPT_STR_PT_BR,
            template_format="jinja2"
        ),
    ]
)

NODE_VISION_PROMPT_EN = ChatPromptTemplate.from_messages(
    [
        SYSTEM_PROMPT_TUPLE_EN,
        HumanMessagePromptTemplate.from_template(
            template=YOU_ARE_IN_A_CONVERSATION_STR_EN + NODE_VISION_PROMPT_STR_EN,
            template_format="jinja2"
        ),
    ]
)

_PROMPTS_DICT = {
    "observe": {
        "output_parser": ObserveNodeFinalUserPromptOutputParser,
        "languages": {
            "pt-br": OBSERVE_NODE_PROMPT_PT_BR,
            "en": OBSERVE_NODE_PROMPT_EN,
        },
    },
    "plan": {
        "output_parser": PlanNodeFinalUserPromptOutputParser,
        "languages": {
            "pt-br": PLAN_NODE_PROMPT_PT_BR,
            "en": PLAN_NODE_PROMPT_EN,
        },
    },
    "execute": {
        "output_parser": ExecuteNodeFinalUserPromptOutputParser,
        "languages": {
            "pt-br": EXECUTE_NODE_PROMPT_PT_BR,
            "en": EXECUTE_NODE_PROMPT_EN,
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