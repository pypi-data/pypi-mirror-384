from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableSequence, RunnableLambda
from langchain_core.language_models.base import BaseLanguageModel
from pydantic import BaseModel, Field
from typing import ClassVar, List
from operator import itemgetter
from eagle.utils.prompt_utils import EagleJsonOutputParser

# Schemas for QA output
class QAOutputSchemaEN(BaseModel):
    response: str = Field(description="The response with the most suitable plan for the given question or situation.")
    sources: List[str] = Field(description="A list of sources consulted to construct the response.")

class QAOutputSchemaPT_BR(BaseModel):
    resposta: str = Field(description="A resposta com o plano mais adequado para a pergunta feita ou situação passada.")
    fontes: List[str] = Field(description="Uma lista com as fontes consultadas para montar a resposta.")

# Output Parser
class QAOutputParser(EagleJsonOutputParser):
    """Custom output parser for the QA chain."""

    CONVERTION_SCHEMA: ClassVar[dict] = {
        "pt-br": {
            "class_for_parsing": QAOutputSchemaPT_BR,
            "convertion_schema": {
                "resposta": {
                    "target_key": "response",
                    "value_mapping": {}
                },
                "fontes": {
                    "target_key": "sources",
                    "value_mapping": {}
                }
            }
        },
        "en": {
            "class_for_parsing": QAOutputSchemaEN,
            "convertion_schema": {
                "response": {
                    "target_key": "response",
                    "value_mapping": {}
                },
                "sources": {
                    "target_key": "sources",
                    "value_mapping": {}
                }
            }
        },
    }

    TARGET_SCHEMA: BaseModel = QAOutputSchemaEN

# Prompts
QA_PROMPT_STR_EN = """
You are tasked with answering the following question based on the provided plans:
---------------- Question -----------------
{{question}}
------------------------------------------

Below are the plans that may serve as a basis for answering the question:
---------------- Plans -----------------
{{plans}}
----------------------------------------

Your task:
1 - Analyze the question and identify the most suitable plan(s) to answer it.
2 - Construct a response to the question using as many details from the relevant plan(s) as possible.
3 - List the sources (plans) you used to construct the response.

You MUST follow the output format below, even if you are not able to find a plan that fits the question:
{
    "response": "<a response with the most suitable plan for the given question or situation, or something to say if you couldn't find a plan that fits>",
    "sources": ["<source_1>", "<source_2>", ...] # List of sources exactly as they appear in the references. Leave it empty if you are not able to find a plan that fits the question.
}
"""

QA_PROMPT_STR_PT_BR = """
Você deve responder à seguinte pergunta com base nos planos fornecidos:
---------------- Pergunta -----------------
{{question}}
------------------------------------------

Abaixo estão os planos que podem servir de base para responder à pergunta:
---------------- Planos -----------------
{{plans}}
----------------------------------------

Sua tarefa:
1 - Analise a pergunta e identifique o(s) plano(s) mais adequado(s) para respondê-la.
2 - Construa uma resposta para a pergunta utilizando ao máximo possível TODOS os detalhes do(s) plano(s) que sejam pertinentes(s).
3 - Liste as fontes (planos) que você utilizou para construir a resposta.

Você DEVE seguir o formato de saída abaixo, mesmo que não consiga encontrar um plano que se encaixe na pergunta:
{
    "resposta": "<a resposta com o plano mais adequado para a pergunta feita ou situação passada, ou alguma coisa a dizer em caso não tenha encontrado um plano que se encaixe>",
    "fontes": ["<fonte_1>", "<fonte_2>", ...] # Lista de fontes exatamente como aparecem nas referências. Deixe vazio se não conseguir encontrar um plano que se encaixe na pergunta.
}
"""

# Prompt Templates
QA_PROMPTS = {
    "en": PromptTemplate.from_template(QA_PROMPT_STR_EN, template_format="jinja2"),
    "pt-br": PromptTemplate.from_template(QA_PROMPT_STR_PT_BR, template_format="jinja2"),
}

def create_qa_chain(
    prompt_language: str,
    llm: BaseLanguageModel,
    use_structured_output: bool = False
) -> RunnableSequence:
    """
    Create a QA chain based on the provided configuration.

    Args:
        prompt_language (str): Language for the prompt (e.g., "en", "pt-br").
        model_name (str): Name of the LLM model to use.
        temperature (float): Sampling temperature for the model.
        max_tokens (int): Maximum number of tokens for the output.

    Returns:
        RunnableSequence: A chain that answers questions based on the provided plans.
    """
    if prompt_language not in QA_PROMPTS:
        raise ValueError(f"Unsupported prompt language: {prompt_language}")

    prompt = QA_PROMPTS[prompt_language]
    output_parser = QAOutputParser(
        source_lang=prompt_language,
        llm=llm,
        use_structured_output=use_structured_output
    )
    _parse = RunnableLambda(lambda x: output_parser.parse(x))

    chain = (
        {
            "question": itemgetter("question"),
            "plans": itemgetter("plans"),
        }
        | prompt
        | llm
        | _parse
    )

    return chain
