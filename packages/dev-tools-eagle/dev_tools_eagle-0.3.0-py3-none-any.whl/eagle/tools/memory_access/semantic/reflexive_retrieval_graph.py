# reflexive_retrieval_graph.py

import logging
from typing import List, TypedDict, Any, Literal, Dict

from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.graph import END, StateGraph, START
from eagle.memory.semantic.base import SemanticMemory

from eagle.chains.self_rag_chains import (
    get_retrieval_grader_chain, 
    get_question_rewriter_chain
)


# --- Logging Setup ---
# Configures basic logging to display timestamps, log levels, and messages.
# This helps in tracing the execution flow of the graph.
logging.basicConfig(level=logging.INFO)

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

# --- Data Models and State ---

class ReflexiveRetrievalState(TypedDict):
    """
    Represents the state of our reflexive retrieval graph.

    This dictionary-like object is passed between the nodes of the graph. Each node
    can read from and write to this state, allowing information to flow through the graph.

    Attributes:
        question (str): The user's initial question, kept for reference.
        better_question (str): A rewritten question to improve retrieval.
        documents (List[Dict[str, Any]]): The list of documents retrieved in the current cycle.
        relevant_documents (List[Dict[str, Any]]): The grader's decision on document relevance ('Yes' or 'No').
    """
    question: str
    better_question: str
    documents: List[Dict[str, Any]]
    relevant_documents: List[Dict[str, Any]]

# --- Main Graph Class ---

class ReflexiveRetrievalGraph:
    """
    Encapsulates the logic for a Reflexive Retrieval graph.

    This graph attempts to retrieve relevant documents. If it finds none,
    it rewrites the question and tries again, creating a loop. The process
    stops once relevant documents are found.
    """

    def __init__(self, set_id: str, semantic_memory: SemanticMemory, grader_llm: BaseChatModel,
                 rewriter_llm: BaseChatModel, prompt_language: Literal["en", "pt"] = "en", top_k:int=10):
        """
        Initializes the Reflexive Retrieval Graph instance.

        Args:
            set_id (str): Identifier for the semantic memory set.
            semantic_memory (SemanticMemory): The retriever for document search.
            grader_llm (BaseChatModel): The language model for grading document relevance.
            rewriter_llm (BaseChatModel): The language model for rewriting questions.
            prompt_language (Literal["en", "pt"]): The language for the prompts.
            top_k (int): The number of documents to retrieve in each cycle.
        """
        self.prompt_language = prompt_language
        self.grader_llm = grader_llm
        self.rewriter_llm = rewriter_llm
        self.semantic_memory = semantic_memory
        self.set_id = set_id
        self.top_k = top_k

        # Initialize the necessary components (chains) for the graph.
        self._initialize_components()
        # Build and compile the graph structure into a runnable application.
        self.app = self._build_and_compile_graph()

    def _initialize_components(self):
        """Creates all the necessary LangChain components (chains) for the graph."""
        self.retrieval_grader = get_retrieval_grader_chain(self.grader_llm, self.prompt_language)
        self.question_rewriter = get_question_rewriter_chain(self.rewriter_llm, self.prompt_language)

    # --- Graph Nodes ---

    def retrieve(self, state: ReflexiveRetrievalState) -> dict:
        """
        Retrieves documents based on the original or a rewritten question.
        """
        logging.info("---NODE: RETRIEVE---")
        # Use the better question if it exists, otherwise use the original.
        question_to_search = state.get("better_question") or state["question"]
        logging.info(f"--- Searching with question: '{question_to_search}' ---")
        
        documents = self.semantic_memory.search_memories(self.set_id, question_to_search, self.top_k)
        
        return {"documents": documents}

    def grade_documents(self, state: ReflexiveRetrievalState) -> dict:
        """
        Filters documents by grading their relevance against the original question.
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
                
        return {"relevant_documents": filtered_docs}

    def transform_query(self, state: ReflexiveRetrievalState) -> dict:
        """
        Rewrites the question to improve the quality of document retrieval.
        This node is executed when no relevant documents are found.
        """
        logging.info("---NODE: TRANSFORM QUERY---")
        question = state["question"]
        
        better_question = self.question_rewriter.invoke({"question": question})
        
        logging.info(f"--- Original Question: '{question}' ---")
        logging.info(f"--- Rewritten Question: '{better_question}' ---")
        
        return {"better_question": better_question}

    # --- Conditional Edge ---

    def decide_to_finish(self, state: ReflexiveRetrievalState) -> str:
        """
        Determines the next step after grading documents.

        If relevant documents are found, the process ends.
        Otherwise, it triggers the query transformation step.
        """
        logging.info("---EDGE: DECIDE TO FINISH---")
        if state["relevant_documents"]:
            logging.info("---DECISION: Relevant documents found. Finishing.---")
            return "end"
        else:
            logging.info("---DECISION: No relevant documents found. Transforming query.---")
            return "transform_query"

    def _build_and_compile_graph(self) -> Any:
        """
        Builds the StateGraph, adds all nodes and edges, and compiles it.
        """
        workflow = StateGraph(ReflexiveRetrievalState)

        # Add nodes to the graph
        workflow.add_node("retrieve", self.retrieve)
        workflow.add_node("grade_documents", self.grade_documents)
        workflow.add_node("transform_query", self.transform_query)

        # Define the graph structure
        workflow.set_entry_point("retrieve")
        workflow.add_edge("retrieve", "grade_documents")

        # Add the conditional logic after grading
        workflow.add_conditional_edges(
            "grade_documents",
            self.decide_to_finish,
            {
                "transform_query": "transform_query",
                "end": END,
            },
        )
        
        # Add the loop back to retry retrieval after transforming the question
        workflow.add_edge("transform_query", "retrieve")

        logging.info("Reflexive Retrieval Graph built. Compiling...")
        return workflow.compile()

    def get_compiled_graph(self) -> Any:
        """
        Returns the compiled and runnable graph application.
        """
        return self.app