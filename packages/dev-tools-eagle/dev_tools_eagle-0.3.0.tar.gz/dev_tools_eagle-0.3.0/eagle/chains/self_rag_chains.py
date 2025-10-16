from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.language_models.chat_models import BaseChatModel
from typing import Literal

# --- Pydantic Models for Structured Output ---

class GradeDocuments(BaseModel):
    """Binary score for relevance check on retrieved documents."""
    binary_score: str = Field(
        description="Documents are relevant to the question, 'yes' or 'no'"
    )

class GradeHallucinations(BaseModel):
    """Binary score for hallucination present in generation answer."""
    binary_score: str = Field(
        description="Answer is grounded in the facts, 'yes' or 'no'"
    )

class GradeAnswer(BaseModel):
    """Binary score to assess whether the answer addresses the question."""
    binary_score: str = Field(
        description="Answer addresses the question, 'yes' or 'no'"
    )

# --- Multilingual Prompts ---

PROMPTS = {
    "en": {
        "generator": """You are an assistant for question-answering tasks. 
                    Use the following pieces of retrieved context to answer the question. 
                    If you don't know the answer, just say that you don't know. 
                    Use three sentences maximum and keep the answer concise.
                    Question: {question} 
                    Context: {context} 
                    Answer:""",
        "retrieval_grader": {
            "system": """You are a grader assessing the relevance of a retrieved document to a user question.
                    It does not need to be a stringent test. The goal is to filter out erroneous retrievals.
                    If the document contains keyword(s) or semantic meaning related to the user question, grade it as relevant.
                    Give a binary score 'yes' or 'no' to indicate whether the document is relevant to the question.""",
            "human": "Retrieved document: \n\n {document} \n\n User question: {question}"
        },
        "question_rewriter": {
            "system": """You are a question re-writer that converts an input question to a better version that is optimized
                    for vectorstore retrieval. Look at the input and try to reason about the underlying semantic intent / meaning.""",
            "human": "Here is the initial question: \n\n {question} \n Formulate an improved question."
        },
        "hallucination_grader": {
            "system": """You are a grader assessing whether an LLM generation is grounded in / supported by a set of retrieved facts.
                    Give a binary score 'yes' or 'no'. 'Yes' means that the answer is grounded in / supported by the set of facts.""",
            "human": "Set of facts: \n\n {documents} \n\n LLM generation: {generation}"
        },
        "answer_grader": {
            "system": """You are a grader assessing whether an answer addresses / resolves a question.
                    Give a binary score 'yes' or 'no'. 'Yes' means that the answer resolves the question.""",
            "human": "User question: \n\n {question} \n\n LLM generation: {generation}"
        }
    },
    "pt": {
        "generator": """Você é um assistente para tarefas de perguntas e respostas.
                    Use os seguintes trechos de contexto recuperados para responder à pergunta.
                    Se você não sabe a resposta, apenas diga que não sabe.
                    Use no máximo três frases e mantenha a resposta concisa.
                    Pergunta: {question}
                    Contexto: {context}
                    Resposta:""",
        "retrieval_grader": {
            "system": """Você é um avaliador que verifica a relevância de um documento recuperado para uma pergunta de um usuário.
                    Não precisa ser um teste rigoroso. O objetivo é filtrar recuperações errôneas.
                    Se o documento contiver palavras-chave ou significado semântico relacionado à pergunta do usuário, classifique-o como relevante.
                    Dê uma pontuação binária 'sim' ou 'não' para indicar se o documento é relevante para a pergunta.""",
            "human": "Documento recuperado: \n\n {document} \n\n Pergunta do usuário: {question}"
        },
        "question_rewriter": {
            "system": """Você é um reescritor de perguntas que converte uma pergunta de entrada em uma versão melhor, otimizada
                    para recuperação em um vectorstore. Analise a entrada e tente raciocinar sobre a intenção/significado semântico subjacente.""",
            "human": "Aqui está a pergunta inicial: \n\n {question} \n Formule uma pergunta melhorada."
        },
        "hallucination_grader": {
            "system": """Você é um avaliador que verifica se uma geração de LLM é baseada em / suportada por um conjunto de fatos recuperados.
                    Dê uma pontuação binária 'sim' ou 'não'. 'Sim' significa que a resposta é baseada em / suportada pelo conjunto de fatos.""",
            "human": "Conjunto de fatos: \n\n {documents} \n\n Geração do LLM: {generation}"
        },
        "answer_grader": {
            "system": """Você é um avaliador que verifica se uma resposta aborda / resolve uma pergunta.
                Dê uma pontuação binária 'sim' ou 'não'. 'Sim' significa que a resposta resolve a pergunta.""",
            "human": "Pergunta do usuário: \n\n {question} \n\n Geração do LLM: {generation}"
        }
    }
}

# --- Chain Creation Functions ---

def get_rag_chain(generate_llm: BaseChatModel, language: Literal["en", "pt"] = "en"):
    """
    Creates the RAG chain for generating answers.

    Args:
        generate_llm (BaseChatModel): The language model for generation.
        language (str): The language for the prompt ('en' or 'pt').

    Returns:
        A runnable chain that generates an answer.
    """
    prompt = ChatPromptTemplate.from_messages([("system", PROMPTS[language]["generator"])])
    rag_chain = prompt | generate_llm | StrOutputParser()
    return rag_chain

def get_retrieval_grader_chain(grade_llm: BaseChatModel, language: Literal["en", "pt"] = "en"):
    """
    Creates the chain for grading the relevance of retrieved documents.

    Args:
        grade_llm (BaseChatModel): The language model for grading.
        language (str): The language for the prompt ('en' or 'pt').

    Returns:
        A runnable chain that outputs a GradeDocuments object.
    """
    prompts = PROMPTS[language]["retrieval_grader"]
    prompt = ChatPromptTemplate.from_messages([
        ("system", prompts["system"]),
        ("human", prompts["human"]),
    ])
    structured_grader_retrieval = grade_llm.with_structured_output(GradeDocuments)
    retrieval_grader_chain = prompt | structured_grader_retrieval
    return retrieval_grader_chain

def get_question_rewriter_chain(generate_llm: BaseChatModel, language: Literal["en", "pt"] = "en"):
    """
    Creates the chain for rewriting user questions to be more optimal for retrieval.

    Args:
        generate_llm (BaseChatModel): The language model for rewriting.
        language (str): The language for the prompt ('en' or 'pt').

    Returns:
        A runnable chain that outputs a rewritten question string.
    """
    prompts = PROMPTS[language]["question_rewriter"]
    prompt = ChatPromptTemplate.from_messages([
        ("system", prompts["system"]),
        ("human", prompts["human"]),
    ])
    question_rewriter_chain = prompt | generate_llm | StrOutputParser()
    return question_rewriter_chain

def get_hallucination_grader_chain(grade_llm: BaseChatModel, language: Literal["en", "pt"] = "en"):
    """
    Creates the chain for grading whether a generated answer is grounded in the documents.

    Args:
        grade_llm (BaseChatModel): The language model for grading.
        language (str): The language for the prompt ('en' or 'pt').

    Returns:
        A runnable chain that outputs a GradeHallucinations object.
    """
    prompts = PROMPTS[language]["hallucination_grader"]
    prompt = ChatPromptTemplate.from_messages([
        ("system", prompts["system"]),
        ("human", prompts["human"]),
    ])
    structured_grader_hallucination = grade_llm.with_structured_output(GradeHallucinations)
    hallucination_grader_chain = prompt | structured_grader_hallucination
    return hallucination_grader_chain

def get_answer_grader_chain(grade_llm: BaseChatModel, language: Literal["en", "pt"] = "en"):
    """
    Creates the chain for grading whether a generated answer addresses the question.

    Args:
        grade_llm (BaseChatModel): The language model for grading.
        language (str): The language for the prompt ('en' or 'pt').

    Returns:
        A runnable chain that outputs a GradeAnswer object.
    """
    prompts = PROMPTS[language]["answer_grader"]
    prompt = ChatPromptTemplate.from_messages([
        ("system", prompts["system"]),
        ("human", prompts["human"]),
    ])
    structured_grader_answer = grade_llm.with_structured_output(GradeAnswer)
    answer_grader_chain = prompt | structured_grader_answer
    return answer_grader_chain
