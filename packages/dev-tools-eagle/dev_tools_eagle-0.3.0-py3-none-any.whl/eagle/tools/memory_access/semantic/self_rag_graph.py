# self_rag_graph.py

from langgraph.graph import END, StateGraph, START
from typing import List, TypedDict, Any, Dict, Literal
from langchain_core.language_models.chat_models import BaseChatModel
from eagle.chains.self_rag_chains import (
    get_hallucination_grader_chain, 
    get_answer_grader_chain, 
    get_question_rewriter_chain, 
    get_retrieval_grader_chain, 
    get_rag_chain
)
from eagle.memory.semantic.base import SemanticMemory
import logging
logging.basicConfig(level=logging.INFO)

# --- State and Data Model Definitions ---

class SelfRagGraphState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        question (str): The user's question.
        generation (str): The LLM's generated answer.
        documents (List[str]): A list of retrieved documents.
    """
    question: str
    better_question: str
    generation: str
    documents: List[Dict[str, Any]]
    relevant_documents : List[Dict[str, Any]]

def format_docs(docs: List[Dict[str, Any]]) -> str:
    """Utility function to format a list of documents into a single string."""
    return "\n\n".join(doc['page_content'] for doc in docs)


binary_score = {
    "en":{
        "positive":"yes",
        "negative":"no" 
    },
    "pt":{
        "positive":"sim",
        "negative":"não" 
    }
}

# --- Main Graph Class ---

class SelfRagGraph:
    """
    Encapsulates the logic for a self-correcting RAG (Retrieval-Augmented Generation) graph.
    
    This class is initialized with the necessary components (LLMs, memory) and
    builds a compiled, ready-to-use LangGraph application.
    """

    def __init__(self, prompt_language:Literal["en", "pt"] ,generate_llm: BaseChatModel, grader_llm: BaseChatModel, semantic_memory: SemanticMemory, set_id: str, top_k:int=10):
        """
        Initializes the RAG graph instance.

        Args:
            prompt_language (Literal["en", "pt"]): The language for the prompts.
            generate_llm (BaseChatModel): The language model for generation and question rewriting.
            grader_llm (BaseChatModel): The language model for grading tasks (relevance, hallucinations).
            semantic_memory (SemanticMemory): An instance of the semantic memory for document retrieval.
            set_id (str): The identifier for the memory set to use.
        """
        self.prompt_language = prompt_language
        self.generate_llm = generate_llm
        self.grader_llm = grader_llm
        self.semantic_memory = semantic_memory
        self.set_id = set_id
        self.top_k = top_k
        
        # Initialize all necessary components (chains, graders)
        self._initialize_components()

        # Build and compile the graph, making it ready at the 'app' attribute
        self.app = self._build_and_compile_graph()

    def _initialize_components(self):
        """Creates all the necessary chains and graders for the graph."""
        self.retrieval_grader = get_retrieval_grader_chain(self.grader_llm, self.prompt_language)
        self.rag_chain = get_rag_chain(self.generate_llm, self.prompt_language)
        self.question_rewriter = get_question_rewriter_chain(self.generate_llm, self.prompt_language)
        self.hallucination_grader = get_hallucination_grader_chain(self.grader_llm, self.prompt_language)
        self.answer_grader = get_answer_grader_chain(self.grader_llm, self.prompt_language)

    # --- Graph Nodes (as class methods) ---

    def retrieve(self, state: SelfRagGraphState) -> dict:
        """
        Retrieves documents from the semantic memory based on the current question.

        Args:
            state (SelfRagGraphState): The current state of the graph.

        Returns:
            dict: An updated state dictionary with the retrieved documents.
        """
        logging.info("---NODE: RETRIEVE---")
        question_to_search = state.get("better_question") or state["question"]
        logging.info(f"--- Question to Search: '{question_to_search}' ---")
        question = state["question"]
        documents = self.semantic_memory.search_memories(self.set_id, question_to_search, self.top_k)
        return {"documents": documents, "question": question, "better_question": question_to_search}

    def generate(self, state: SelfRagGraphState) -> dict:
        """
        Generates an answer using the RAG chain based on the retrieved documents.

        Args:
            state (SelfRagGraphState): The current state of the graph.

        Returns:
            dict: An updated state dictionary with the generated answer.
        """
        logging.info("---NODE: GENERATE---")
        question = state["question"]
        documents = state["documents"]
        generation = self.rag_chain.invoke({"context": format_docs(documents), "question": question})
        return {"documents": documents, "question": question, "generation": generation}

    def grade_documents(self, state: SelfRagGraphState) -> dict:
        """
        Filters documents by grading their relevance to the question.

        Args:
            state (SelfRagGraphState): The current state of the graph.

        Returns:
            dict: An updated state dictionary with only the relevant documents.
        """
        logging.info("---NODE: GRADE DOCUMENTS---")
        question = state["question"]
        documents = state["documents"]
        filtered_docs = []
        for d in documents:
            score = self.retrieval_grader.invoke({"question": question, "document": d})
            if score.binary_score == binary_score[self.prompt_language]["positive"]:
                logging.info("---GRADE: RELEVANT DOCUMENT---")
                filtered_docs.append(d)
            else:
                logging.info("---GRADE: NOT RELEVANT DOCUMENT---")
        return {"documents": documents, "relevant_documents": filtered_docs, "question": question}

    def transform_query(self, state: SelfRagGraphState) -> dict:
        """
        Rewrites the question to improve the quality of document retrieval.

        Args:
            state (SelfRagGraphState): The current state of the graph.

        Returns:
            dict: An updated state dictionary with the new, rewritten question.
        """
        logging.info("---NODE: TRANSFORM QUERY---")
        question = state["question"]
        documents = state["documents"] 
        better_question = self.question_rewriter.invoke({"question": question})
        logging.info(f"--- Original Question: '{question}' ---")
        logging.info(f"--- Rewritten Question: '{better_question}' ---")
        return {"documents": documents, "question": question, "better_question":better_question}
    
    # --- Conditional Logic (Edges, as class methods) ---

    def decide_to_generate(self, state: SelfRagGraphState) -> str:
        """
        Determines the next step after grading documents. If relevant documents are found,
        it proceeds to generation. Otherwise, it transforms the query.

        Args:
            state (SelfRagGraphState): The current state of the graph.

        Returns:
            str: The name of the next node to execute ("transform_query" or "generate").
        """
        logging.info("---EDGE: DECIDE TO GENERATE---")
        if not state["relevant_documents"]:
            logging.info("---DECISION: No relevant documents found. Transforming query.---")
            return "transform_query"
        else:
            logging.info("---DECISION: Relevant documents found. Generating answer.---")
            return "generate"

    def grade_generation_v_documents_and_question(self, state: SelfRagGraphState) -> str:
        """
        Grades the generated answer for hallucinations and relevance to the question.

        This function performs two checks:
        1. Hallucination Check: Is the answer grounded in the provided documents?
        2. Answer Check: Does the answer actually address the user's question?

        Args:
            state (SelfRagGraphState): The current state of the graph.

        Returns:
            str: The name of the next branch to take ("useful", "not supported", or "not useful").
        """
        logging.info("---EDGE: GRADE GENERATION---")
        question = state["question"]
        documents = state["documents"]
        generation = state["generation"]

        # 1. Check for hallucinations
        logging.info("---Checking for hallucinations---")
        score_hallucination = self.hallucination_grader.invoke(
            {"documents": format_docs(documents), "generation": generation}
        )
        if score_hallucination.binary_score == binary_score[self.prompt_language]["negative"]:
            logging.info("---DECISION: Generation is NOT grounded in documents. Retrying.---")
            return "not supported"
        
        logging.info("---DECISION: Generation is grounded in documents.---")
        
        # 2. Check if the answer addresses the question
        logging.info("---Checking for answer usefulness---")
        score_answer = self.answer_grader.invoke({"question": question, "generation": generation})
        if score_answer.binary_score == binary_score[self.prompt_language]["positive"]:
            logging.info("---DECISION: Generation addresses the question. Finishing.---")
            return "useful"
        else:
            logging.info("---DECISION: Generation does NOT address the question. Transforming query.---")
            return "not useful"

    def _build_and_compile_graph(self) -> Any:
        """
        Builds the StateGraph, adds all nodes and edges, and compiles it into a runnable application.

        Returns:
            Any: The compiled LangGraph application.
        """
        workflow = StateGraph(SelfRagGraphState)

        # Add nodes (referencing the class methods)
        workflow.add_node("retrieve", self.retrieve)
        workflow.add_node("grade_documents", self.grade_documents)
        workflow.add_node("generate", self.generate)
        workflow.add_node("transform_query", self.transform_query)

        # Define the graph structure (edges)
        workflow.add_edge(START, "retrieve")
        workflow.add_edge("retrieve", "grade_documents")
        
        workflow.add_conditional_edges(
            "grade_documents",
            self.decide_to_generate,
            {
                "transform_query": "transform_query",
                "generate": "generate",
            },
        )
        
        workflow.add_edge("transform_query", "retrieve")
        
        workflow.add_conditional_edges(
            "generate",
            self.grade_generation_v_documents_and_question,
            {
                "not supported": "generate",        # Retry generation
                "useful": END,                      # Finish successfully
                "not useful": "transform_query",    # The answer was not helpful, improve the question
            },
        )
        
        logging.info("Graph built. Compiling...")
        return workflow.compile()
        
    def get_compiled_graph(self) -> Any:
        """
        Returns the compiled graph application.

        Returns:
            Any: The compiled and runnable LangGraph application.
        """
        return self.app
