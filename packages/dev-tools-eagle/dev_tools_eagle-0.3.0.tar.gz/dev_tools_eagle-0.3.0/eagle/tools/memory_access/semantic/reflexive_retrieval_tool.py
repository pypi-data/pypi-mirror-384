# reflexive_retrieval_tool.py

from typing import Any, Iterator, Dict, Literal
from pydantic import Field, PrivateAttr
from langchain_core.tools import BaseTool
from langchain_core.language_models.chat_models import BaseChatModel
import logging

# Make sure the new graph is accessible for import
from eagle.tools.memory_access.semantic.reflexive_retrieval_graph import ReflexiveRetrievalGraph, ReflexiveRetrievalState

# --- Basic Logging Configuration ---
# Sets up logging to display informational messages, which is useful for tracking the tool's execution.
logging.basicConfig(level=logging.INFO)

class ReflexiveRetrievalTool(BaseTool):
    """
    A tool that uses a Reflexive Retrieval graph to find relevant documents..
    """
    # --- Tool Identification ---
    name: str = "reflexive_retrieval_tool"
    description: str = (
        "Useful for finding and retrieving relevant documents from a knowledge base. "
    )

    # --- Configuration Attributes ---
    # These fields are configured when the tool is instantiated.
    memory: Any = Field(description="Retriever for the initial search in the knowledge base.")
    prompt_language: Literal["en", "pt"] = Field(default="en", description="Language of the prompts ('en' or 'pt').")
    grader_llm: BaseChatModel = Field(description="Language model used to grade the relevance of retrieved documents.")
    rewriter_llm : BaseChatModel = Field(description="Language model used to rewrite the question.")
    set_id: str
    top_k:int

    # --- Internal State ---
    # A private attribute to hold the compiled and ready-to-use graph.
    # The leading underscore indicates it's intended for internal use within the class.
    _app: Any = PrivateAttr()

    def model_post_init(self, __context: Any) -> None:
        """
        Initializes and compiles the internal Reflexive Retrieval graph after the model is created.
        
        This method is automatically called by Pydantic after the tool's fields are initialized.
        It sets up the underlying LangGraph application that powers the tool's logic.
        """
        super().model_post_init(__context)
        logging.info("--- Initializing and compiling ReflexiveRetrievalGraph for the Tool ---")
        
        # 1. Create an instance of the graph builder with the tool's configuration.
        graph_builder = ReflexiveRetrievalGraph(
            semantic_memory=self.memory,
            grader_llm=self.grader_llm,
            rewriter_llm = self.rewriter_llm,
            prompt_language=self.prompt_language,
            set_id=self.set_id,
            top_k=self.top_k
        )
        
        # 2. Compile the graph to create a runnable application.
        # This compiled graph is stored in the private '_app' attribute.
        self._app = graph_builder.get_compiled_graph()
        logging.info("--- Graph compiled and ready to use. ---")


    def _run(self, question: str, **kwargs: Any) -> ReflexiveRetrievalState:
        """
        Runs the tool synchronously to find and retrieve documents.

        This is the primary synchronous execution method called by the LangChain agent.

        Args:
            question (str): The user's question to search for.
            **kwargs: Additional arguments (not used here but required by the BaseTool interface).

        Returns:
            str: A formatted string containing the relevant documents found, or a
                 message indicating that no results were found.
        """
        logging.info(f"\n--- Running ReflexiveRetrievalTool with question: '{question}' ---")
        
        # Define the initial state for the graph execution.
        # It includes the original question, the current question (which may be rewritten), and a retry counter.
        initial_state = {"question": question}
        
        # Invoke the compiled graph with the initial state and a recursion limit to prevent infinite loops.
        final_state = self._app.invoke(initial_state, {"recursion_limit": 10})
        
        # Extract the final list of documents from the graph's final state.
        final_documents = final_state.get("documents", [])
        
        # Format the documents for a clean output.
        logging.info(f"--- Final documents retrieved by the graph: ---\n{len(final_documents)}")
        
        return final_state
        
    async def _arun(self, question: str, **kwargs: Any) -> ReflexiveRetrievalState:
        """
        Runs the tool asynchronously to find and retrieve documents.

        This is the asynchronous version of _run, for use in async environments.

        Args:
            question (str): The user's question to search for.
            **kwargs: Additional arguments.

        Returns:
            str: A formatted string of the relevant documents or a no-results message.
        """
        logging.info(f"\n--- Running ReflexiveRetrievalTool (async) with question: '{question}' ---")
        
        # Define the initial state for the asynchronous graph execution.
        initial_state = {"question": question}

        # Asynchronously invoke the graph.
        final_state = await self._app.ainvoke(initial_state, {"recursion_limit": 10})
        
        # Extract and format the results.
        final_documents = final_state.get("documents", [])
        logging.info(f"--- Final documents retrieved by the graph (async): ---\n{len(final_documents)}")

        return final_state
    
    def stream_graph(self, question: str) -> Iterator[Dict[str, Any]]:
        """
        Runs the underlying graph in streaming mode to observe each step of the execution.

        This method is useful for debugging and understanding the flow of the reflexive process,
        as it yields the state of the graph after each node completes.

        Args:
            question (str): The user's question.

        Yields:
            Iterator[Dict[str, Any]]: An iterator of state dictionaries from each step of the graph execution.
        """
        # Define the initial state for the stream.
        initial_state = {"question": question}

        # The 'yield from' statement passes through each event from the graph's stream method.
        yield from self._app.stream(initial_state, {"recursion_limit": 10})