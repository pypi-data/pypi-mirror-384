from eagle.stores.base import EagleBaseStore
from eagle.stores.opensearch import OpenSearchIndexConfig, OpenSearchStore
from typing import Any, Optional
from langgraph.store.base import Item
from langchain_core.embeddings import Embeddings
from langchain.chains.query_constructor.base import AttributeInfo

class StoredMemory:
    """
    Base class for stored memory, using a persistent store for data storage.

    Args:
        store (EagleBaseStore): An instance of a subclass of EagleBaseStore for persistence.
    """

    BUILD_CONFIG_SCHEMA = None
    MEMORY_NAME = "eagle-stored-memory"
    VALUE_EXAMPLE = {
        "key": "Example value."
    }
    ATTRIBUTE_INFO = [
        AttributeInfo(name="value.key", type="string", description="Example key"),
    ]
    EMBEDDED_FIELDS = ["key"]

    def __init__(self, store: EagleBaseStore) -> None:
        self.store = store

    def __init__(self, store_class, embedding_model: Embeddings, embedding_dims: int):
        """
        Initialize EagleBaseStore.

        Args:
            store_class (type): The class of the store to use for persistence.
            embedding_model (Embeddings): The embedding model to use.
            embedding_dims (int): The dimensions of the embedding model.
        """
        self.store = self._create_store(store_class, embedding_model, embedding_dims)

    def _create_store(self, store_class: type, embedding_model: Embeddings, embedding_dims: int) -> EagleBaseStore:
        """
        Create and configure the store for episodic memory.

        Args:
            store_class (type): The class of the store to use for persistence.
            embedding_model (Embeddings): The embedding model to use.
            embedding_dims (int): The dimensions of the embedding model.

        Returns:
            BaseStore: An instance of the configured store.
        """
        if issubclass(store_class, OpenSearchStore):
            index = OpenSearchIndexConfig(
                index_name=self.MEMORY_NAME.lower(),
                dims=embedding_dims,
                embed=embedding_model,
                fields=self.EMBEDDED_FIELDS,
                value_example=self.VALUE_EXAMPLE,
                attribute_info=self.ATTRIBUTE_INFO
            )
            store = store_class(index=index)
            def _wrap(store_client):
                if not store_client.indices.exists(index=index['index_name']):
                    store.create_index()
            store.with_client(_wrap)
            return store
        else:
            raise ValueError(
                f"Unsupported store class: {store_class}. For now, only OpenSearchStore is supported."
            )

    def build(self, *args: Any, **kwargs: Any) -> None:
        """
        Build the memory instance. This method must be overridden by subclasses.
        """
        raise NotImplementedError("Subclasses must implement the build method.")
    
    async def abuild(self, *args: Any, **kwargs: Any) -> None:
        """
        Build the memory instance. This method must be overridden by subclasses.
        """
        raise NotImplementedError("Subclasses must implement the build method.")

    def put_memory(
        self,
        namespace: tuple[str, ...],
        key: str,
        value: dict[str, Any],
        ttl: Optional[float] = None,
    ) -> None:
        """
        Store an stored memory.

        Args:
            namespace (tuple[str, ...]): The namespace for the memory.
            key (str): The unique key for the memory.
            value (dict[str, Any]): The memory data to store.
            ttl (Optional[float]): Time-to-live for the memory in minutes.
        """
        self.store.put(namespace=namespace, key=key, value=value, ttl=ttl)

    def get_memory(self, namespace: tuple[str, ...], key: str) -> Optional[Item]:
        """
        Retrieve an stored memory.

        Args:
            namespace (tuple[str, ...]): The namespace for the memory.
            key (str): The unique key for the memory.

        Returns:
            Optional[Item]: The retrieved memory or None if not found.
        """
        return self.store.get(namespace=namespace, key=key)

    def search_memories(
        self,
        namespace_prefix: tuple[str, ...],
        query: Optional[str] = None,
        filter: Optional[str] = "NO_FILTER",
        limit: int = 10,
        offset: int = 0,
        sort: Optional[dict[str, str]] = None,
    ) -> list[Item]:
        """
        Search stored memories.

        Args:
            namespace_prefix (tuple[str, ...]): The namespace prefix to search within.
            query (Optional[str]): A query string for semantic search.
            filter (Optional[str]): String-based filter for the search.
            limit (int): Maximum number of results to return.
            offset (int): Number of results to skip.

        Returns:
            list[Item]: A list of matching memories.
        """
        return self.store.search(
            namespace_prefix,
            query=query,
            filter=filter,
            limit=limit,
            offset=offset,
            sort=sort

        )

    def delete_memory(self, namespace: tuple[str, ...], key: str) -> None:
        """
        Delete an stored memory.

        Args:
            namespace (tuple[str, ...]): The namespace for the memory.
            key (str): The unique key for the memory.
        """
        self.store.delete(namespace=namespace, key=key)

    def delete_memories_by_namespace(self, namespace: tuple[str, ...]) -> None:
        """
        Delete all stored memories in the given namespace.

        Args:
            namespace (tuple[str, ...]): The namespace to delete memories from.
        """
        self.store.delete_by_namespace(namespace)

    async def aput_memory(
        self,
        namespace: tuple[str, ...],
        key: str,
        value: dict[str, Any],
        ttl: Optional[float] = None,
    ) -> None:
        """
        Asynchronously store a memory.

        Args:
            namespace (tuple[str, ...]): The namespace for the memory.
            key (str): The unique key for the memory.
            value (dict[str, Any]): The memory data to store.
            ttl (Optional[float]): Time-to-live for the memory in minutes.
        """
        await self.store.aput(namespace=namespace, key=key, value=value, ttl=ttl)

    async def aget_memory(self, namespace: tuple[str, ...], key: str) -> Optional[Item]:
        """
        Asynchronously retrieve a memory.

        Args:
            namespace (tuple[str, ...]): The namespace for the memory.
            key (str): The unique key for the memory.

        Returns:
            Optional[Item]: The retrieved memory or None if not found.
        """
        return await self.store.aget(namespace=namespace, key=key)

    async def asearch_memories(
        self,
        namespace_prefix: tuple[str, ...],
        query: Optional[str] = None,
        filter: Optional[str] = "NO_FILTER",
        limit: int = 10,
        offset: int = 0,
        sort: Optional[dict[str, str]] = None,
    ) -> list[Item]:
        """
        Asynchronously search stored memories.

        Args:
            namespace_prefix (tuple[str, ...]): The namespace prefix to search within.
            query (Optional[str]): A query string for semantic search.
            filter (Optional[str]): String-based filter for the search.
            limit (int): Maximum number of results to return.
            offset (int): Number of results to skip.

        Returns:
            list[Item]: A list of matching memories.
        """
        return await self.store.asearch(
            namespace_prefix,
            query=query,
            filter=filter,
            limit=limit,
            offset=offset,
            sort=sort,
        )

    async def adelete_memory(self, namespace: tuple[str, ...], key: str) -> None:
        """
        Asynchronously delete a memory.

        Args:
            namespace (tuple[str, ...]): The namespace for the memory.
            key (str): The unique key for the memory.
        """
        await self.store.adelete(namespace=namespace, key=key)
