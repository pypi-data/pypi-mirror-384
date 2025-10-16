from .base import GenericMemory
from typing import Any, Optional, Tuple, List, Dict
import asyncio

class HierarchicalMemory(GenericMemory):
    """
    Memory for storing and managing data in hierarchical namespaces.

    Namespaces are formed by joining self.MEMORY_NAME with a tuple of keys.
    """

    def put_memory(
        self,
        hierarchy: Tuple[Any, ...],
        key: str,
        value: Dict[str, Any],
        ttl: Optional[float] = None,
    ) -> None:
        """
        Store a value in a hierarchical namespace.

        Args:
            hierarchy (Tuple[Any, ...]): Tuple representing the hierarchy.
            key (str): Unique key for the value.
            value (Dict[str, Any]): Data to store.
            ttl (Optional[float]): Time-to-live in minutes.
        """
        namespace = (self.MEMORY_NAME,) + hierarchy
        super().put_memory(namespace=namespace, key=key, value=value, ttl=ttl)

    def get_memory(
        self,
        hierarchy: Tuple[Any, ...],
        key: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a value from a hierarchical namespace.

        Args:
            hierarchy (Tuple[Any, ...]): Tuple representing the hierarchy.
            key (str): Unique key for the value.

        Returns:
            Optional[Dict[str, Any]]: Retrieved value or None.
        """
        namespace = (self.MEMORY_NAME,) + hierarchy
        item = super().get_memory(namespace=namespace, key=key)
        return item.value if item else None

    def delete_memory(
        self,
        hierarchy: Tuple[Any, ...],
        key: str,
    ) -> None:
        """
        Delete a value from a hierarchical namespace.

        Args:
            hierarchy (Tuple[Any, ...]): Tuple representing the hierarchy.
            key (str): Unique key for the value.
        """
        namespace = (self.MEMORY_NAME,) + hierarchy
        super().delete_memory(namespace=namespace, key=key)

    def search_memories(
        self,
        hierarchy: Tuple[Any, ...],
        query: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
        filter_expr: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for values in a hierarchical namespace.

        Args:
            hierarchy (Tuple[Any, ...]): Tuple representing the hierarchy.
            query (Optional[str]): Query string for semantic search.
            limit (int): Max results.
            offset (int): Results to skip.
            filter_expr (Optional[str]): Additional filter expression.

        Returns:
            List[Dict[str, Any]]: List of matching values.
        """
        namespace_prefix = (self.MEMORY_NAME,) + hierarchy
        filter_list = ['eq("value.type", "generic_memory")']
        if filter_expr:
            filter_list.append(filter_expr)
        filter = 'and(' + ','.join(filter_list) + ')'
        items = super().search_memories(
            namespace_prefix=namespace_prefix,
            query=query,
            filter=filter,
            limit=limit,
            offset=offset,
        )
        return [item.value for item in items]

    def delete_memories_by_namespace(
        self,
        hierarchy: Tuple[Any, ...],
    ) -> None:
        """
        Delete all values in a hierarchical namespace.

        Args:
            hierarchy (Tuple[Any, ...]): Tuple representing the hierarchy.
        """
        namespace = (self.MEMORY_NAME,) + hierarchy
        super().delete_memories_by_namespace(namespace)

    async def aput_memory(
        self,
        hierarchy: Tuple[Any, ...],
        key: str,
        value: Dict[str, Any],
        ttl: Optional[float] = None,
    ) -> None:
        """
        Asynchronously store a value in a hierarchical namespace.
        """
        namespace = (self.MEMORY_NAME,) + hierarchy
        await super().aput_memory(namespace=namespace, key=key, value=value, ttl=ttl)

    async def aget_memory(
        self,
        hierarchy: Tuple[Any, ...],
        key: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Asynchronously retrieve a value from a hierarchical namespace.
        """
        namespace = (self.MEMORY_NAME,) + hierarchy
        item = await super().aget_memory(namespace=namespace, key=key)
        return item.value if item else None

    async def adelete_memory(
        self,
        hierarchy: Tuple[Any, ...],
        key: str,
    ) -> None:
        """
        Asynchronously delete a value from a hierarchical namespace.
        """
        namespace = (self.MEMORY_NAME,) + hierarchy
        await super().adelete_memory(namespace=namespace, key=key)

    async def asearch_memories(
        self,
        hierarchy: Tuple[Any, ...],
        query: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
        filter_expr: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Asynchronously search for values in a hierarchical namespace.
        """
        namespace_prefix = (self.MEMORY_NAME,) + hierarchy
        filter_list = ['eq("value.type", "generic_memory")']
        if filter_expr:
            filter_list.append(filter_expr)
        filter = 'and(' + ','.join(filter_list) + ')'
        items = await super().asearch_memories(
            namespace_prefix=namespace_prefix,
            query=query,
            filter=filter,
            limit=limit,
            offset=offset,
        )
        return [item.value for item in items]
