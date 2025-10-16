from typing import Any, Optional, List, Dict
from eagle.memory.planning.base import PlanningMemory

class PossiblePlansAndToolsMemory(PlanningMemory):
    """
    Memory class for managing possible plans and tools.

    This class extends PlanningMemory to provide specific functionality
    for handling possible plans and tools.
    """
    
    MEMORY_NAME = "eagle-possible-plans-and-tools-memory"

    EMBEDDED_FIELDS = ["description", "plan"]

    VALUE_EXAMPLE = {
        "description": "Example description",
        "plan": "Example plan",
        "type": "possible_plans_and_tools_memory",
        "tools": {
        }
    }

    def put_memory(
        self,
        agent_id: str,
        plan_id: str,
        description: str,
        plan: str,
        tools: Dict[str, Dict[str, str]],
        ttl: Optional[float] = None,
    ) -> None:
        """
        Add a memory for a possible plan and its tools.

        Args:
            agent_id (str): The unique identifier for the agent.
            plan_id (str): The unique identifier for the plan.
            description (str): A description of the plan.
            plan (str): The plan details.
            tools (Dict[str, Dict[str, str]]): A dictionary of tools with their descriptions.
            ttl (Optional[float]): Time-to-live for the memory in minutes.
        """
        namespace = (self.MEMORY_NAME, agent_id)
        value = {
            "description": description,
            "plan": plan,
            "type": "possible_plans_and_tools_memory",
            "tools": tools,
        }
        super().put_memory(namespace=namespace, key=plan_id, value=value, ttl=ttl)

    async def aput_memory(
        self,
        agent_id: str,
        plan_id: str,
        description: str,
        plan: str,
        tools: Dict[str, Dict[str, str]],
        ttl: Optional[float] = None,
    ) -> None:
        """
        Asynchronously add a memory for a possible plan and its tools.

        Args:
            agent_id (str): The unique identifier for the agent.
            plan_id (str): The unique identifier for the plan.
            description (str): A description of the plan.
            plan (str): The plan details.
            tools (Dict[str, Dict[str, str]]): A dictionary of tools with their descriptions.
            ttl (Optional[float]): Time-to-live for the memory in minutes.
        """
        namespace = (self.MEMORY_NAME, agent_id)
        value = {
            "description": description,
            "plan": plan,
            "type": "possible_plans_and_tools_memory",
            "tools": tools,
        }
        await super().aput_memory(namespace=namespace, key=plan_id, value=value, ttl=ttl)

    def get_memory(self, agent_id: str, plan_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a memory for a possible plan and its tools.

        Args:
            agent_id (str): The unique identifier for the agent.
            plan_id (str): The unique identifier for the plan.

        Returns:
            Optional[Dict[str, Any]]: The retrieved memory or None if not found.
        """
        namespace = (self.MEMORY_NAME, agent_id)
        item = super().get_memory(namespace=namespace, key=plan_id)
        return item.value if item else None

    async def aget_memory(self, agent_id: str, plan_id: str) -> Optional[Dict[str, Any]]:
        """
        Asynchronously retrieve a memory for a possible plan and its tools.

        Args:
            agent_id (str): The unique identifier for the agent.
            plan_id (str): The unique identifier for the plan.

        Returns:
            Optional[Dict[str, Any]]: The retrieved memory or None if not found.
        """
        namespace = (self.MEMORY_NAME, agent_id)
        item = await super().aget_memory(namespace=namespace, key=plan_id)
        return item.value if item else None

    def delete_memory(self, agent_id: str, plan_id: str) -> None:
        """
        Delete a memory for a possible plan and its tools.

        Args:
            agent_id (str): The unique identifier for the agent.
            plan_id (str): The unique identifier for the plan.
        """
        namespace = (self.MEMORY_NAME, agent_id)
        super().delete_memory(namespace=namespace, key=plan_id)

    async def adelete_memory(self, agent_id: str, plan_id: str) -> None:
        """
        Asynchronously delete a memory for a possible plan and its tools.

        Args:
            agent_id (str): The unique identifier for the agent.
            plan_id (str): The unique identifier for the plan.
        """
        namespace = (self.MEMORY_NAME, agent_id)
        await super().adelete_memory(namespace=namespace, key=plan_id)

    def delete_memories_by_namespace(self, agent_id: str) -> None:
        """
        Delete all possible plans and tools memories in the given namespace.

        Args:
            agent_id (str): The unique identifier for the agent.
        """
        namespace = (self.MEMORY_NAME, agent_id)
        super().delete_memories_by_namespace(namespace)

    def search_memories(
        self,
        agent_id: str,
        query: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Search for memories of possible plans and tools.

        Args:
            agent_id (str): The unique identifier for the agent.
            query (Optional[str]): A query string for semantic search.
            limit (int): Maximum number of results to return.
            offset (int): Number of results to skip.

        Returns:
            List[Dict[str, Any]]: A list of matching memories.
        """
        namespace_prefix = (self.MEMORY_NAME, agent_id)
        filter = 'eq("value.type", "possible_plans_and_tools_memory")'
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
        agent_id: str,
        query: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Asynchronously search for memories of possible plans and tools.

        Args:
            agent_id (str): The unique identifier for the agent.
            query (Optional[str]): A query string for semantic search.
            limit (int): Maximum number of results to return.
            offset (int): Number of results to skip.

        Returns:
            List[Dict[str, Any]]: A list of matching memories.
        """
        namespace_prefix = (self.MEMORY_NAME, agent_id)
        filter = 'eq("value.type", "possible_plans_and_tools_memory")'
        items = await super().asearch_memories(
            namespace_prefix=namespace_prefix,
            query=query,
            filter=filter,
            limit=limit,
            offset=offset,
        )
        return [item.value for item in items]


