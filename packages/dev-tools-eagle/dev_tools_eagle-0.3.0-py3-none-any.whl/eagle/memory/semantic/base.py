from eagle.memory.base import StoredMemory
from langchain.chains.query_constructor.base import AttributeInfo
from typing import Any, Optional, List, Dict
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
import hashlib

class SemanticMemory(StoredMemory):
    """
    Manages semantic memory, which stores facts, concepts, and general
    world knowledge in a queryable format.

    This class specializes in storing textual content and its associated metadata,
    enabling semantic searches based on the meaning of the text.

    Args:
        store_class (type): The class of the store to use for data persistence.
        embedding_model (Embeddings): The embedding model to use for vectorization.
        embedding_dims (int): The dimensions of the embedding model's vectors.
    """

    # A unique identifier for this type of memory in the database.
    MEMORY_NAME = "eagle-semantic-memory"

    # The 'page_content' field will be vectorized for semantic similarity searches.
    EMBEDDED_FIELDS = ["page_content"]

    # Example of the data structure for a memory entry.
    VALUE_EXAMPLE = {
        "page_content": "The capital of Peru is Lima.",
        "metadata": {"source": "https://example.com/peru_facts"}
    }

    # Metadata for LangChain's query constructor (Self-Querying Retriever).
    ATTRIBUTE_INFO = [
        AttributeInfo(
            name="value.page_content",
            type="string",
            description="A piece of factual information, a concept, or general knowledge."
        ),
        AttributeInfo(
            name="value.metadata",
            type="dict",
            description="Source information or other contextual data related to the text content."
        )
    ]

    def put_memory(
        self,
        set_id: str,
        memory_id: str,
        page_content: str,
        metadata: dict,
        ttl: Optional[float] = None,
    ) -> None:
        """
        Stores a piece of information (knowledge) in the memory.

        Args:
            set_id (str): Unique ID for a knowledge set, or 'global' for general knowledge.
            memory_id (str): Unique ID for this specific piece of information.
            page_content (str): The textual content of the information to store.
            metadata (dict): Metadata associated with the information (e.g., source, date).
            ttl (Optional[float]): Time-to-live for the memory in minutes.
        """
        namespace = (self.MEMORY_NAME, set_id)
        value = {"page_content": page_content, "metadata": metadata}
        super().put_memory(namespace=namespace, key=memory_id, value=value, ttl=ttl)

    async def aput_memory(
        self,
        set_id: str,
        memory_id: str,
        page_content: str,
        metadata: dict,
        ttl: Optional[float] = None,
    ) -> None:
        """
        Asynchronously stores a piece of information (knowledge) in the memory.

        Args:
            set_id (str): Unique ID for a knowledge set, or 'global' for general knowledge.
            memory_id (str): Unique ID for this specific piece of information.
            page_content (str): The textual content of the information to store.
            metadata (dict): Metadata associated with the information (e.g., source, date).
            ttl (Optional[float]): Time-to-live for the memory in minutes.
        """
        namespace = (self.MEMORY_NAME, set_id)
        value = {"page_content": page_content, "metadata": metadata}
        await super().aput_memory(namespace=namespace, key=memory_id, value=value, ttl=ttl)

    def search_memories(
        self,
        set_id: str,
        query: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Searches for information in the knowledge base.

        Args:
            set_id (str): The ID of the knowledge set or 'global' to search within.
            query (Optional[str]): Text for the semantic search.
            limit (int): Maximum number of results to return.
            offset (int): Number of results to skip.

        Returns:
            List[Dict[str, Any]]: A list of matching pieces of information.
        """
        namespace_prefix = (self.MEMORY_NAME, set_id)
        # The filter is removed as the namespace already scopes the search correctly.
        items = super().search_memories(
            namespace_prefix=namespace_prefix,
            query=query,
            limit=limit,
            offset=offset,
        )
        return [item.value for item in items]

    async def asearch_memories(
        self,
        set_id: str,
        query: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Asynchronously searches for information in the knowledge base.

        Args:
            set_id (str): The ID of the knowledge set or 'global' to search within.
            query (Optional[str]): Text for the semantic search.
            limit (int): Maximum number of results to return.
            offset (int): Number of results to skip.

        Returns:
            List[Dict[str, Any]]: A list of matching pieces of information.
        """
        namespace_prefix = (self.MEMORY_NAME, set_id)
        # The filter is removed as the namespace already scopes the search correctly.
        items = await super().asearch_memories(
            namespace_prefix=namespace_prefix,
            query=query,
            limit=limit,
            offset=offset,
        )
        return [item.value for item in items]

    # get_memory, aget_memory, delete_memory, adelete_memory, and 
    # delete_memories_by_namespace remain the same from the previous version.
    
    def get_memory(self, set_id: str, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a specific piece of information from memory by its ID.

        Args:
            set_id (str): The ID of the knowledge set or 'global'.
            memory_id (str): The ID of the information to retrieve.

        Returns:
            Optional[Dict[str, Any]]: The retrieved information or None if not found.
        """
        namespace = (self.MEMORY_NAME, set_id)
        item = super().get_memory(namespace=namespace, key=memory_id)
        return item.value if item else None

    async def aget_memory(self, set_id: str, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Asynchronously retrieves a specific piece of information from memory by its ID.

        Args:
            set_id (str): The ID of the knowledge set or 'global'.
            memory_id (str): The ID of the information to retrieve.

        Returns:
            Optional[Dict[str, Any]]: The retrieved information or None if not found.
        """
        namespace = (self.MEMORY_NAME, set_id)
        item = await super().aget_memory(namespace=namespace, key=memory_id)
        return item.value if item else None

    def delete_memory(self, set_id: str, memory_id: str) -> None:
        """
        Deletes a specific piece of information from memory.

        Args:
            set_id (str): The ID of the knowledge set or 'global'.
            memory_id (str): The ID of the information to delete.
        """
        namespace = (self.MEMORY_NAME, set_id)
        super().delete_memory(namespace=namespace, key=memory_id)

    async def adelete_memory(self, set_id: str, memory_id: str) -> None:
        """
        Asynchronously deletes a specific piece of information from memory.

        Args:
            set_id (str): The ID of the knowledge set or 'global'.
            memory_id (str): The ID of the information to delete.
        """
        namespace = (self.MEMORY_NAME, set_id)
        await super().adelete_memory(namespace=namespace, key=memory_id)

    def delete_memories_by_namespace(self, set_id: str) -> None:
        """
        Deletes the entire knowledge base for a specific 'set_id'.

        Args:
            set_id (str): The ID of the knowledge set (or 'global') to be deleted.
        """
        namespace = (self.MEMORY_NAME, set_id)
        super().delete_memories_by_namespace(namespace)

    def build(
        self,
        set_id: str,
        documents: List[Document],
        ttl: Optional[float] = None,
    ) -> None:
        """
        Builds the memory from a list of LangChain documents.

        Args:
            set_id (str): The ID of the knowledge set where the documents will be stored.
            documents (List[Document]): A list of Document objects to populate the memory with.
            ttl (Optional[float], optional): Time-to-live for the memories in minutes.
        """
        for doc in documents:
            # Generate a unique ID based on content to avoid duplicates.
            doc_id = hashlib.sha256(doc.page_content.encode("utf-8")).hexdigest()
            self.put_memory(
                set_id=set_id,
                memory_id=doc_id,
                page_content=doc.page_content,
                metadata=doc.metadata,
                ttl=ttl,
            )