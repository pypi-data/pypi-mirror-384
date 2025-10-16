from eagle.memory.base import StoredMemory
from eagle.stores.base import SearchItem
from typing import Optional, List, Dict, Any, Callable
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from langchain_core.runnables import RunnableSequence
from langchain_core.output_parsers.transform import BaseCumulativeTransformOutputParser

class GenericMemoryToolInput(BaseModel):
    query: str = Field(description="The query to search in the memory.")
    namespace_prefix: List[str] = Field(description="The namespace prefix to search within.")
    limit: int = Field(default=10, description="Maximum number of results to return.")
    offset: int = Field(default=0, description="Number of results to skip.")
    filter: Optional[str] = Field(default=None, description="Optional filter for the search.")

class GenericMemoryTool(BaseTool):
    name: str = "generic_memory_tool"
    description: str = (
        "A tool to perform simple retrieval-augmented generation (RAG) using a generic StoredMemory instance."
    )
    memory: StoredMemory
    chain: RunnableSequence  # RunnableSequence to process the inputs
    input_transformer: Callable[[BaseModel], GenericMemoryToolInput]  # Callable to transform inputs to GenericMemoryToolInput
    chain_input_preparer: Callable[[GenericMemoryToolInput], List[GenericMemoryToolInput]]  # Prepares input for the chain
    output_parser: BaseCumulativeTransformOutputParser # Pydantic schema to parse the chain result
    args_schema: type = BaseModel  # Adaptable schema for the raw input

    def _run(self, **_inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the tool synchronously.

        Args:
            _inputs (Dict[str, Any]): Input object containing the query and search parameters.

        Returns:
            Dict[str, Any]: The parsed output of the tool.
        """
        # Transform inputs using the provided transformer
        raw_inputs = self.args_schema(**_inputs)
        transformed_inputs = self.input_transformer(raw_inputs)

        # Search for relevant items in memory
        items = self.memory.search_memories(
            namespace_prefix=tuple(transformed_inputs.namespace_prefix),
            query=transformed_inputs.query,
            filter=transformed_inputs.filter,
            limit=transformed_inputs.limit,
            offset=transformed_inputs.offset,
        )

        # Prepare input for the chain
        chain_input = self.chain_input_preparer(transformed_inputs, items)

        # Run the chain
        chain_result = self.chain.invoke(chain_input)

        # Parse the output using the output schema
        return self.output_parser.parse(chain_result)

    async def _arun(self, **_inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the tool asynchronously.

        Args:
            _inputs (Dict[str, Any]): Input object containing the query and search parameters.

        Returns:
            Dict[str, Any]: The parsed output of the tool.
        """
        # Transform inputs using the provided transformer
        raw_inputs = self.args_schema(**_inputs)
        transformed_inputs = self.input_transformer(raw_inputs)

        # Search for relevant items in memory
        items = await self.memory.asearch_memories(
            namespace_prefix=tuple(transformed_inputs.namespace_prefix),
            query=transformed_inputs.query,
            filter=transformed_inputs.filter,
            limit=transformed_inputs.limit,
            offset=transformed_inputs.offset,
        )

        # Prepare input for the chain
        chain_input = self.chain_input_preparer(transformed_inputs, items)

        # Run the chain
        chain_result = await self.chain.ainvoke(chain_input)
        
        # Parse the output using the output schema
        return self.output_parser.parse(chain_result)
