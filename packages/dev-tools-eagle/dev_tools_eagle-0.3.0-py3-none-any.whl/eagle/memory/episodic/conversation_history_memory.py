from eagle.memory.episodic.base import EpisodicMemory
from typing import Any, Optional, List, Dict

class ConversationHistoryMemory(EpisodicMemory):
    """
    Memory for storing and managing chat conversations.

    Args:
        store_class (type): The class of the store to use for persistence.
        embedding_model (Embeddings): The embedding model to use.
        embedding_dims (int): The dimensions of the embedding model.
    """

    MEMORY_NAME = "eagle-conversation-history"

    EMBEDDED_FIELDS = ["description"]
    
    VALUE_EXAMPLE = {
        "messages": [
            {
                "role": "user",
                "content": "Hello, how are you?",
            },
            {
                "role": "assistant",
                "content": "I'm fine, thank you!",
            },
        ],
        "description": "Example conversation",
        "type": "conversation_history",
    }
        
    def put_memory(
        self,
        chat_id: str,
        memory_id: str,
        messages: List[Dict[str, Any]],
        description: str,
        ttl: Optional[float] = None,
    ) -> None:
        """
        Add a memory to the conversation history.

        Args:
            chat_id (str): The unique identifier for the chat.
            memory_id (str): The unique identifier for the memory.
            messages (List[Dict[str, Any]]): A list of messages in the memory.
            description (str): A description characterizing the memory.
            ttl (Optional[float]): Time-to-live for the memory in minutes.
        """
        namespace = (self.MEMORY_NAME, chat_id)
        value = {"messages": messages, "description": description, "type": "conversation_history"}
        super().put_memory(namespace=namespace, key=memory_id, value=value, ttl=ttl)

    async def aput_memory(
        self,
        chat_id: str,
        memory_id: str,
        messages: List[Dict[str, Any]],
        description: str,
        ttl: Optional[float] = None,
    ) -> None:
        """
        Asynchronously add a memory to the conversation history.

        Args:
            chat_id (str): The unique identifier for the chat.
            memory_id (str): The unique identifier for the memory.
            messages (List[Dict[str, Any]]): A list of messages in the memory.
            description (str): A description characterizing the memory.
            ttl (Optional[float]): Time-to-live for the memory in minutes.
        """
        namespace = (self.MEMORY_NAME, chat_id)
        value = {"messages": messages, "description": description, "type": "conversation_history"}
        await super().aput_memory(namespace=namespace, key=memory_id, value=value, ttl=ttl)

    def get_memory(self, chat_id: str, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a memory from the conversation history.

        Args:
            chat_id (str): The unique identifier for the chat.
            memory_id (str): The unique identifier for the memory.

        Returns:
            Optional[Dict[str, Any]]: The retrieved memory or None if not found.
        """
        namespace = (self.MEMORY_NAME, chat_id)
        item = super().get_memory(namespace=namespace, key=memory_id)
        return item.value if item else None

    async def aget_memory(self, chat_id: str, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Asynchronously retrieve a memory from the conversation history.

        Args:
            chat_id (str): The unique identifier for the chat.
            memory_id (str): The unique identifier for the memory.

        Returns:
            Optional[Dict[str, Any]]: The retrieved memory or None if not found.
        """
        namespace = (self.MEMORY_NAME, chat_id)
        item = await super().aget_memory(namespace=namespace, key=memory_id)
        return item.value if item else None

    def delete_memory(self, chat_id: str, memory_id: str) -> None:
        """
        Delete a memory from the conversation history.

        Args:
            chat_id (str): The unique identifier for the chat.
            memory_id (str): The unique identifier for the memory.
        """
        namespace = (self.MEMORY_NAME, chat_id)
        super().delete_memory(namespace=namespace, key=memory_id)

    async def adelete_memory(self, chat_id: str, memory_id: str) -> None:
        """
        Asynchronously delete a memory from the conversation history.

        Args:
            chat_id (str): The unique identifier for the chat.
            memory_id (str): The unique identifier for the memory.
        """
        namespace = (self.MEMORY_NAME, chat_id)
        await super().adelete_memory(namespace=namespace, key=memory_id)

    def delete_memories_by_namespace(self, chat_id: str) -> None:
        """
        Delete all conversation history memories in the given namespace.

        Args:
            chat_id (str): The unique identifier for the chat.
        """
        namespace = (self.MEMORY_NAME, chat_id)
        super().delete_memories_by_namespace(namespace)

    def search_memories(
        self,
        chat_id: str,
        query: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Search for memories in the conversation history.

        Args:
            chat_id (str): The unique identifier for the chat.
            query (Optional[str]): A query string for semantic search.
            limit (int): Maximum number of results to return.
            offset (int): Number of results to skip.

        Returns:
            List[Dict[str, Any]]: A list of matching memories.
        """
        namespace_prefix = (self.MEMORY_NAME, chat_id)
        filter = 'eq("value.type","conversation_history")'
        items = super().search_memories(
            namespace_prefix=namespace_prefix,
            query=query,
            filter=filter,
            limit=limit,
            offset=offset,
        )
        return [item.value for item in items]

    async def asearch_memories(
        self,
        chat_id: str,
        query: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Asynchronously search for memories in the conversation history.

        Args:
            chat_id (str): The unique identifier for the chat.
            query (Optional[str]): A query string for semantic search.
            limit (int): Maximum number of results to return.
            offset (int): Number of results to skip.

        Returns:
            List[Dict[str, Any]]: A list of matching memories.
        """
        namespace_prefix = (self.MEMORY_NAME, chat_id)
        filter = 'eq("value.type","conversation_history")'
        items = await super().asearch_memories(
            namespace_prefix=namespace_prefix,
            query=query,
            filter=filter,
            limit=limit,
            offset=offset,
        )
        return [item.value for item in items]