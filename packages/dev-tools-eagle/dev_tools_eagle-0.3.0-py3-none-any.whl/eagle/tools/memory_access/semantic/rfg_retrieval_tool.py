# rfg_retrieval_tool.py

from typing import Any, Iterator, Dict, Literal
from pydantic import Field, PrivateAttr
from langchain_core.tools import BaseTool
from langchain_core.language_models.chat_models import BaseChatModel
import logging
from eagle.tools.memory_access.semantic.rfg_retrieval_graph import RFGRetrievalGraph, RFGGraphState

# --- Basic Logging Configuration ---
# Sets up logging to display informational messages, which is useful for tracking the tool's execution.
logging.basicConfig(level=logging.INFO)

class RFGRetrievalTool(BaseTool):
    """
    A tool that uses a Retrieval-Feedback Generation (RFG) graph to find relevant documents.
    This process enhances retrieval by first generating a hypothetical document based on an initial
    set of retrieved results, and then using this richer, hypothetical document to perform a
    more accurate final search.
    """
    name: str = "rfg_document_retriever"
    description: str = (
        "Useful for finding and retrieving relevant documents from a knowledge base. "
        "It works by first generating a hypothetical document based on the context of 'n' initially retrieved documents, "
        "and then uses that hypothetical document for a more refined search. Returns the final, relevant documents found."
    )

    # --- Configuration Attributes ---
    # These fields are configured when the tool is instantiated.
    memory: Any = Field(description="The retriever instance for searching the knowledge base.")
    prompt_language: Literal["en", "pt", "es"] = Field(default="es", description="The language for the prompts.")
    generator_llm: BaseChatModel = Field(description="The language model used to generate the hypothetical document.")
    set_id: str = Field(description="The identifier for the semantic memory set to search within.")
    top_k_rfg: int = Field(description="The number of documents to retrieve in the initial step for context.")
    top_k: int = Field(description="The final number of documents to retrieve after using the hypothetical document.")

    # --- Internal State ---
    # A private attribute to hold the compiled and ready-to-use graph.
    _app: Any = PrivateAttr()

    def model_post_init(self, __context: Any) -> None:
        """
        Initializes and compiles the internal RFGRetrievalGraph after the model is created.

        This method is automatically called by Pydantic after the tool's fields are initialized.
        It sets up the underlying LangGraph application that powers the tool's logic.

        Args:
            __context (Any): The Pydantic model validation context (not used directly).
        """
        super().model_post_init(__context)
        logging.info("--- Initializing and compiling RFGRetrievalGraph for the Tool ---")
        
        graph_builder = RFGRetrievalGraph(
            semantic_memory=self.memory,
            generator_llm=self.generator_llm,
            prompt_language=self.prompt_language,
            set_id=self.set_id,
            top_k_rfg=self.top_k_rfg,
            top_k=self.top_k
        )
        
        self._app = graph_builder.get_compiled_graph()
        logging.info("--- RFG Graph compiled and ready to use. ---")

    def _run(self, question: str, **kwargs: Any) -> RFGGraphState:
        """
        Runs the tool synchronously to find and retrieve documents.

        This is the primary synchronous execution method called by a LangChain agent.

        Args:
            question (str): The user's question to search for.
            **kwargs (Any): Additional arguments (not used here but required by the BaseTool interface).

        Returns:
            RFGGraphState: The final state of the graph, containing the retrieved documents
                           and other intermediate values.
        """
        logging.info(f"\n--- Running RFGRetrievalTool with question: '{question}' ---")
        
        initial_state = {"question": question}
        
        final_state = self._app.invoke(initial_state, {"recursion_limit": 5})
              
        logging.info(f"--- Final documents retrieved by the RFG graph ---")
        
        return final_state
        
    async def _arun(self, question: str, **kwargs: Any) -> RFGGraphState:
        """
        Runs the tool asynchronously to find and retrieve documents.

        This is the asynchronous version of _run, for use in async environments.

        Args:
            question (str): The user's question to search for.
            **kwargs (Any): Additional arguments (not used here but required by the BaseTool interface).

        Returns:
            RFGGraphState: The final state of the graph, containing the retrieved documents
                           and other intermediate values.
        """
        logging.info(f"\n--- Running RFGRetrievalTool (async) with question: '{question}' ---")
        
        initial_state = {"question": question}

        final_state = await self._app.ainvoke(initial_state, {"recursion_limit": 5})
              
        logging.info(f"--- Final documents retrieved by the RFG graph (async) ---")

        return final_state
    
    def stream_graph(self, question: str) -> Iterator[Dict[str, Any]]:
        """
        Runs the underlying graph in streaming mode to observe each step of the execution.

        This method is useful for debugging and understanding the flow of the process,
        as it yields the state of the graph after each node completes.

        Args:
            question (str): The user's question.

        Yields:
            Iterator[Dict[str, Any]]: An iterator of state dictionaries from each step
                                      of the graph's execution.
        """
        initial_state = {"question": question}
        yield from self._app.stream(initial_state, {"recursion_limit": 5})