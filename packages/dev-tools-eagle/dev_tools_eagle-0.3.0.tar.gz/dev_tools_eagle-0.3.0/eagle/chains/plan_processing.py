from eagle.utils.prompt_utils import EagleJsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableSequence, RunnablePassthrough, RunnableLambda
from langchain_core.language_models.base import BaseLanguageModel
from pydantic import BaseModel, Field
from typing import ClassVar, List
from operator import itemgetter

# Schemas for individual plans
class PlanSchemaEN(BaseModel):
    question: str = Field(description="The question derived from the text.")
    plan: str = Field(description="The corresponding plan to address the question.")

class PlanSchemaPT_BR(BaseModel):
    pergunta: str = Field(description="A pergunta derivada do texto.")
    plano: str = Field(description="O plano correspondente para responder à pergunta.")

# Schemas for the list of plans
class PlanProcessingOutputSchemaEN(BaseModel):
    plans: List[PlanSchemaEN] = Field(
        description="A list of plans, each containing a 'question' and a corresponding 'plan'."
    )

class PlanProcessingOutputSchemaPT_BR(BaseModel):
    planos: List[PlanSchemaPT_BR] = Field(
        description="Uma lista de planos, cada um contendo uma 'pergunta' e um 'plano' correspondente."
    )

# Schemas for plan checking output
class PlanCheckingOutputSchemaEN(BaseModel):
    questions_to_remove: List[str] = Field(
        description="List of questions to be removed, if any."
    )
    plans_to_add: List[PlanSchemaEN] = Field(
        description="List of plans to be added, if any."
    )

class PlanCheckingOutputSchemaPT_BR(BaseModel):
    perguntas_a_remover: List[str] = Field(
        description="Lista de perguntas a serem removidas, se houver."
    )
    planos_a_adicionar: List[PlanSchemaPT_BR] = Field(
        description="Lista de planos a serem adicionados, se houver."
    )

# Output Parsers
class PlanProcessingOutputParser(EagleJsonOutputParser):
    """Custom output parser for the plan processing chain."""

    CONVERTION_SCHEMA: ClassVar[dict] = {
        "pt-br": {
            "class_for_parsing": PlanProcessingOutputSchemaPT_BR,
            "convertion_schema": {
                "planos": {
                    "target_key": "plans",
                    "value_mapping": {
                        "pergunta": {
                            "target_key": "question",
                            "value_mapping": {}
                        },
                        "plano": {
                            "target_key": "plan",
                            "value_mapping": {}
                        }
                    }
                }
            }
        },
        "en": {
            "class_for_parsing": PlanProcessingOutputSchemaEN,
            "convertion_schema": {
                "plans": {
                    "target_key": "plans",
                    "value_mapping": {
                        "question": {
                            "target_key": "question",
                            "value_mapping": {}
                        },
                        "plan": {
                            "target_key": "plan",
                            "value_mapping": {}
                        }
                    }
                }
            }
        },
    }

    TARGET_SCHEMA: BaseModel = PlanProcessingOutputSchemaEN

class PlanCheckingOutputParser(EagleJsonOutputParser):
    """Custom output parser for the plan checking chain."""

    CONVERTION_SCHEMA: ClassVar[dict] = {
        "pt-br": {
            "class_for_parsing": PlanCheckingOutputSchemaPT_BR,
            "convertion_schema": {
                "perguntas_a_remover": {
                    "target_key": "questions_to_remove",
                    "value_mapping": {}
                },
                "planos_a_adicionar": {
                    "target_key": "plans_to_add",
                    "value_mapping": {
                        "pergunta": {
                            "target_key": "question",
                            "value_mapping": {}
                        },
                        "plano": {
                            "target_key": "plan",
                            "value_mapping": {}
                        }
                    }
                }
            }
        },
        "en": {
            "class_for_parsing": PlanCheckingOutputSchemaEN,
            "convertion_schema": {
               "questions_to_remove": {
                    "target_key": "questions_to_remove",
                    "value_mapping": {}
                },
                "plans_to_add": {
                    "target_key": "plans_to_add",
                    "value_mapping": {
                        "question": {
                            "target_key": "question",
                            "value_mapping": {}
                        },
                        "plan": {
                            "target_key": "plan",
                            "value_mapping": {}
                        }
                    }
                }
            }
        },
    }

    TARGET_SCHEMA: BaseModel = PlanCheckingOutputSchemaEN

# Prompts
PLAN_PROCESSING_PROMPT_STR_EN = """
Read the text below:
---------------- Source of knowledge -----------------
{{text}}
------------------------------------------------------

Now, based only on the content of the Source of Knowledge text, you need to extract questions and plans that would solve the situations present in those questions.
Important guidelines:
1 - Explore the possibilities well, creating varied questions and plans to maximize the extraction of knowledge from the Source of Knowledge text.
2 - In writing the steps of the plan, include the DETAILS of the knowledge present in the text that can help solve each step.
3 - Under no circumstances invent a plan or content of a plan that does not come from the Source of Knowledge text.
4 - Do not think of questions that do not have plans that can come from the content of the Source of Knowledge text. In other words, do not think of questions whose plans cannot come from the content of the Source of Knowledge text.

Output format:
{
    "plans": [
        {
            "question": "What to do in case of... assuming that...", # this is an example of a question
            "plan": "First, do..., then do..., if X happens, do Y..., finally do..." # this is an example of a plan
        },
        {
            "question": "How to solve... and what are the options...", # this is another example of a question
            "plan": "Check if... if there is X, do Y... otherwise..." # this is another example of a plan
        }, ... # The questions and plans should be extracted from the Source of Knowledge text, not invented.
    ]
}
"""

PLAN_PROCESSING_PROMPT_STR_PT_BR = """
Observe o texto abaixo:
---------------- Fonte de conhecimento -----------------
{{text}}
--------------------------------------------------------

Agora, com base apenas no conteúdo do texto da Fonte de Conhecimento, você precisa seguir os seguintes passos:
1 - Observando o texto, pense uma situação que, caso ocorra, você precisaria de um plano para resolver e que os detalhes do plano poderiam ser extraídos do texto.
2 - Com base nessa situação, pense em uma pergunta que poderia ser feita para resolver essa situação (exemplo: "Supondo que... como...?").
3 - Agora, com base nessa pergunta, monte um passo-a-passo cujos detalhes venham do do texto da Fonte de Conhecimento.

Diretrizes importantes:
1 - Imagine situações variadas para diferenciar as perguntas e planos, maximizando a extração de conhecimento do texto da Fonte de Conhecimento.
2 - Não vago nas perguntas e planos. Busque ser específico e claro com o conteúdo do texto da Fonte de Conhecimento.
3 - Não faça referências à fonte de conhecimento no plano, como "utilize a fonte <nome da fonte de conhecimento> para", como se ela pudesse ser consultada depois. Pegue o conteúdo da fonte e o coloque no plano.

Formato de saída:
{
    "planos": [
        {
            "pergunta": "O que fazer em caso de... supondo que...", # isso é um exemplo de pergunta
            "plano": "Primeiro, faça..., depois faça..., se X acontecer, faça Y..., finalmente faça..." # isso é um exemplo de plano
        },
        {
            "pergunta": "Como resolver... e quais são as opções...", # isso é outro exemplo de pergunta
            "plano": "Verifique se... caso haja X, faça Y... do contrário... considere as seguintes opções..." # isso é outro exemplo de plano
        }, ... # As perguntas e planos devem ser extraídos do texto da Fonte de conhecimento, e não inventados.
    ]
}
"""

PLAN_CHECKING_PROMPT_STR_EN = """

Observe the following source of knowledge:
---------------- Original source of knowledge -----------------
{{text}}
-----------------------------------------------------------------

From this original source of knowledge, a candidate plan was extracted to integrate into a knowledge base:
---------------- Candidate plan -----------------
{{candidate_plan}}
-------------------------------------------------

Now we want to compare the question of this new candidate plan with other plans already extracted previously whose questions are possibly similar to the question of the candidate plan.
---------------- Some existing plans in the base -----------------
{{existing_plans}}
------------------------------------------------------------------

Your goal is to avoid duplication of questions and, if applicable, add something new to the existing plans base.

Important guidelines:
1 - Try to separate the plans well, avoiding that one plan answers more than one question.
2 - Not necessarily incorporate the knowledge of the candidate plan. Only do this if, observing the source of the original source of knowledge and the possibly similar questions, you realize that the candidate plan brings something new and relevant to the existing plans base.

Output format:
{
    "questions_to_remove": [
        "<question_1>",
        "<question_2>", ... these questions must be EXACTLY the same as the questions of the existing plans in the base that you want to remove. If there are no questions to be removed, leave this list empty.
    ],
    "plans_to_add": [
        {
            "question": "<a question that the plan answers>",
            "plan": "<The text of the plan itself>"
        }, ... this list should contain the plans you want to add to the knowledge base. If there are no plans to be added, leave this list empty.
    ]
}
"""

PLAN_CHECKING_PROMPT_STR_PT = """
Observe a seguinte fonte de conhecimento:
---------------- Fonte de conhecimento original -----------------
{{text}}
-----------------------------------------------------------------

Dessa fonte de conhecimento original foi extraído um plano candidato para integrar uma base de conhecimentos:
---------------- Plano candidato -----------------
{{candidate_plan}}
--------------------------------------------------

Agora queremos comparar a pergunta desse novo plano candidato com outros planos já extraídos anteriormente cujas perguntas são possivelmente semelhantes à pergunta do plano candidato.
---------------- Alguns planos já existente na base -----------------
{{existing_plans}}
---------------------------------------------------------------------

Seu objetivo é evitar a duplicação de perguntas e, se for o caso, adicionar algo novo à base de planos já existente.

Diretrizes importantes:
1 - Busque separar bem os planos, evitando que um plano responda a mais de uma pergunta.
2 - Não necessariamente incorpore o conhecimento do plano candidato. Só faça isso se, observando a fonte do conhecimento original e as perguntas possivelmente semelhantes, você perceber que o plano candidato traz algo novo e relevante para a base de planos já existente.

Formato da saída:
{
    "perguntas_a_remover": [
        "<pergunta_1>",
        "<pergunta_2>", ... essas perguntas devem ser EXATAMENTE iguais às perguntas dos planos já existentes na base que você quer remover. Se não houver perguntas a serem removidas, deixe essa lista vazia.
    ],
    "planos_a_adicionar": [
        {
            "pergunta": "<a pergunta que o plano responde>",
            "plano": "<O texto do plano em si>"
        }, ... essa lista deve conter os planos que você quer adicionar à base de conhecimento. Se não houver planos a serem adicionados, deixe essa lista vazia.
    ]
}
"""

# Prompt Templates
PLAN_PROCESSING_PROMPTS = {
    "en": PromptTemplate.from_template(PLAN_PROCESSING_PROMPT_STR_EN, template_format="jinja2"),
    "pt-br": PromptTemplate.from_template(PLAN_PROCESSING_PROMPT_STR_PT_BR, template_format="jinja2"),
}

PLAN_CHECKING_PROMPTS = {
    "en": PromptTemplate.from_template(PLAN_CHECKING_PROMPT_STR_EN, template_format="jinja2"),
    "pt-br": PromptTemplate.from_template(PLAN_CHECKING_PROMPT_STR_PT, template_format="jinja2")
}

def create_plan_processing_chain(
    prompt_language: str,
    llm: BaseLanguageModel,
    use_structured_output: bool = False,
) -> RunnableSequence:
    """
    Create a plan processing chain based on the provided configuration.

    Args:
        prompt_language (str): Language for the prompt (e.g., "en", "pt-br").
        model_name (str): Name of the LLM model to use.
        temperature (float): Sampling temperature for the model.
        max_tokens (int): Maximum number of tokens for the output.

    Returns:
        RunnableSequence: A chain that processes plans based on the provided configuration.
    """
    if prompt_language not in PLAN_PROCESSING_PROMPTS:
        raise ValueError(f"Unsupported prompt language: {prompt_language}")

    prompt = PLAN_PROCESSING_PROMPTS[prompt_language]
    output_parser = PlanProcessingOutputParser(
        source_lang=prompt_language,
        llm=llm,
        use_structured_output=use_structured_output
    )
    _parse = RunnableLambda(
        lambda x: output_parser.parse(x)
    )

    chain = (
        {"text": RunnablePassthrough()}
        | prompt
        | llm
        | _parse
    )

    return chain

def create_plan_checking_chain(
    prompt_language: str,
    llm: BaseLanguageModel,
    use_structured_output: bool = False,
) -> RunnableSequence:
    """
    Create a plan checking chain based on the provided configuration.

    Args:
        prompt_language (str): Language for the prompt (e.g., "en", "pt-br").
        model_name (str): Name of the LLM model to use.
        temperature (float): Sampling temperature for the model.
        max_tokens (int): Maximum number of tokens for the output.

    Returns:
        RunnableSequence: A chain that compares plans based on the provided configuration.
    """
    if prompt_language not in PLAN_CHECKING_PROMPTS:
        raise ValueError(f"Unsupported prompt language: {prompt_language}")

    prompt = PLAN_CHECKING_PROMPTS[prompt_language]
    output_parser = PlanCheckingOutputParser(
        source_lang=prompt_language,
        llm=llm,
        use_structured_output=use_structured_output
    )
    _parse = RunnableLambda(lambda x: output_parser.parse(x))

    chain = (
        {
            "text": itemgetter("text"),
            "candidate_plan": itemgetter("candidate_plan"),
            "existing_plans": itemgetter("existing_plans"),
        }
        | prompt
        | llm
        | _parse
    )

    return chain
