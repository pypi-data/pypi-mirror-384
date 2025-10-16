from eagle.chains.translation import create_translation_chain
from eagle.memory.planning.base import PlanningMemory
from langchain_core.language_models.chat_models  import BaseChatModel
from typing import List, Dict, Optional, Any
from langchain.chains.query_constructor.base import AttributeInfo
from pydantic import BaseModel, Field, field_validator
import asyncio

# Build config schema
class PossibleToolsMemoryConfigSchema(BaseModel):
    chain_llm: Optional[BaseChatModel] = Field(default=None, description="Language model for translation")
    chain_llm_prompt_language: str = Field(default="pt-br", description="Language for the translation prompt")

    @field_validator('chain_llm', mode='before')
    def validate_llm_objects(cls, v):
        if v is None or issubclass(type(v), BaseChatModel):
            return v
        raise TypeError("LLM must be an instance of BaseChatModel or its subclasses.")

    def model_dump(self, *args, **kwargs):
        data = super().model_dump(*args, **kwargs)
        # Serialize LLM objects to dictionaries
        for field_name in ['chain_llm']:
            data[field_name] = getattr(self, field_name)
        return data
    
    class Config:
        arbitrary_types_allowed = True

class ToolsDescriptorSchema(BaseModel):
    name: str = Field(..., description="Name of the tool")
    description: str = Field(..., description="Description of the tool")

# Memory class
class PossibleToolsMemory(PlanningMemory):
    """
    Memory class for managing possible tools.

    This class extends PlanningMemory to handle tools and their descriptions.
    """

    MEMORY_NAME = "eagle-possible-tools-memory"

    EMBEDDED_FIELDS = ["description"]

    VALUE_EXAMPLE = {
        "name": "Example tool",
        "description": "Example description",
        "type": "possible_tools_memory",
    }

    ATTRIBUTE_INFO = PlanningMemory.ATTRIBUTE_INFO + [
        AttributeInfo(name="value.name", type="string", description="Name of the tool"),
    ]

    def put_memory(
        self,
        tools_set_id: str,
        tool_name: str,
        description: str,
        ttl: Optional[float] = None,
    ) -> None:
        namespace = (self.MEMORY_NAME, tools_set_id)
        value = {
            "name": tool_name,
            "description": description,
            "type": "possible_tools_memory",
        }
        super().put_memory(namespace=namespace, key=tool_name, value=value, ttl=ttl)

    async def aput_memory(
        self,
        tools_set_id: str,
        tool_name: str,
        description: str,
        ttl: Optional[float] = None,
    ) -> None:
        namespace = (self.MEMORY_NAME, tools_set_id)
        value = {
            "name": tool_name,
            "description": description,
            "type": "possible_tools_memory",
        }
        await super().aput_memory(namespace=namespace, key=tool_name, value=value, ttl=ttl)

    def get_memory(self, tools_set_id: str, tool_name: str) -> Optional[Dict[str, Any]]:
        namespace = (self.MEMORY_NAME, tools_set_id)
        item = super().get_memory(namespace=namespace, key=tool_name)
        return item.value if item else None

    async def aget_memory(self, tools_set_id: str, tool_name: str) -> Optional[Dict[str, Any]]:
        namespace = (self.MEMORY_NAME, tools_set_id)
        item = await super().aget_memory(namespace=namespace, key=tool_name)
        return item.value if item else None

    def delete_memory(self, tools_set_id: str, tool_name: str) -> None:
        namespace = (self.MEMORY_NAME, tools_set_id)
        super().delete_memory(namespace=namespace, key=tool_name)

    async def adelete_memory(self, tools_set_id: str, tool_name: str) -> None:
        namespace = (self.MEMORY_NAME, tools_set_id)
        await super().adelete_memory(namespace=namespace, key=tool_name)

    def delete_memories_by_namespace(self, tools_set_id: str) -> None:
        """
        Delete all possible tools memories in the given namespace.

        Args:
            tools_set_id (str): The unique identifier for the tools set.
        """
        namespace = (self.MEMORY_NAME, tools_set_id)
        super().delete_memories_by_namespace(namespace)

    def search_memories(
        self,
        tools_set_id: str,
        query: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        namespace_prefix = (self.MEMORY_NAME, tools_set_id)
        filter = 'eq("value.type","possible_tools_memory")'
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
        tools_set_id: str,
        query: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        namespace_prefix = (self.MEMORY_NAME, tools_set_id)
        filter = 'eq("value.type","possible_tools_memory")'
        items = await super().asearch_memories(
            namespace_prefix=namespace_prefix,
            query=query,
            filter=filter,
            limit=limit,
            offset=offset,
        )
        return [item.value for item in items]

    async def abuild(
        self,
        tools_set_id: str,
        tools_descriptors: List[ToolsDescriptorSchema],
        config: PossibleToolsMemoryConfigSchema = {"chain_llm": None},
        ttl: Optional[float] = None,
    ) -> None:
        """
        Build and persist tools with translated (or not translated) descriptions.

        Args:
            tools_set_id (str): The unique identifier for this set of tools.
            tools (List[Dict[str, str]]): A list of dictionaries with 'name' and 'description'.
            config (PossibleToolsMemoryConfigSchema): Configuration for the translation process.
            ttl (Optional[float]): Time-to-live for the memory in minutes.
        """
        # Create a translation chain using the provided config
        if config.get("chain_llm") is not None:
            config = PossibleToolsMemoryConfigSchema(**config).model_dump()
            translation_chain = create_translation_chain(
                prompt_language=config["chain_llm_prompt_language"],
                llm=config["chain_llm"],
            )
        else:
            translation_chain = None

        async def process_tool(tool: ToolsDescriptorSchema) -> None:
            name = tool["name"]
            description = tool["description"]
            final_description = await translation_chain.ainvoke(description) if translation_chain else description
            await self.aput_memory(tools_set_id=tools_set_id, tool_name=name, description=final_description, ttl=ttl)

        await asyncio.gather(*(process_tool(tool) for tool in tools_descriptors))

    def build(self, tools_set_id: str,
        tools_descriptors: List[ToolsDescriptorSchema],
        config: PossibleToolsMemoryConfigSchema = {"chain_llm": None},
        ttl: Optional[float] = None,
    ) -> None:
        """
        Synchronous build method for possible tools memory.

        Args:
            tools_set_id (str): The unique identifier for this set of tools.
            tools_descriptors (List[ToolsDescriptorSchema]): A list of dictionaries with 'name' and 'description'.
            config (PossibleToolsMemoryConfigSchema): Configuration for the translation process.
            ttl (Optional[float]): Time-to-live for the memory in minutes.
        """
        # Create a translation chain using the provided config
        if config.get("chain_llm") is not None:
            config = PossibleToolsMemoryConfigSchema(**config).model_dump()
            translation_chain = create_translation_chain(
                prompt_language=config["chain_llm_prompt_language"],
                llm=config["chain_llm"],
            )
        else:
            translation_chain = None

        def process_tool(tool: ToolsDescriptorSchema) -> None:
            name = tool["name"]
            description = tool["description"]
            if translation_chain:
                final_description = translation_chain.invoke(description)
            else:
                final_description = description
            self.put_memory(tools_set_id=tools_set_id, tool_name=name, description=final_description, ttl=ttl)

        for tool in tools_descriptors:
            process_tool(tool)
