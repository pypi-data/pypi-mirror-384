
from eagle.memory.planning.base import PlanningMemory
from eagle.chains.plan_processing import create_plan_processing_chain, create_plan_checking_chain
from langchain_core.language_models.chat_models  import BaseChatModel
from typing import Any, Optional, List, Dict
from pydantic import BaseModel, Field, field_validator
from langchain.chains.query_constructor.base import AttributeInfo
import asyncio
import hashlib
import os
import yaml

# Schemas
class PlanDescriptorSchema(BaseModel):
    plan: str = Field(..., description="Details of the plan")
    question: str = Field(..., description="Question derived from the plan")
    source: Optional[str] = Field(None, description="Source of the plan")

class PossiblePlansMemoryConfigSchema(BaseModel):
    chain_llm: Optional[BaseChatModel] = Field(default=None, description="Language model for processing and checking")
    chain_llm_prompt_language: str = Field(default="pt-br", description="Language for the translation prompt")
    k_review_candidates: Optional[int] = Field(
        default=None, description="Number of review candidates for plan checking"
    )
    rounds: Optional[int] = Field(default=None, description="Number of processing rounds")

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

# Memory class
class PossiblePlansMemory(PlanningMemory):
    """
    Memory class for managing possible plans.

    This class extends PlanningMemory to provide specific functionality
    for handling possible plans.
    """
    
    MEMORY_NAME = "eagle-possible-plans-memory"

    EMBEDDED_FIELDS = ["question", "plan", "source"]

    VALUE_EXAMPLE = {
        "question": "Example question",
        "plan": "Example plan",
        "source": "Example source",
        "type": "possible_plans"
    }

    ATTRIBUTE_INFO = [
        AttributeInfo(name="value.question", type="string", description="Question derived from the memory"),
        AttributeInfo(name="value.plan", type="string", description="Plan details"),
        AttributeInfo(name="value.source", type="string", description="Source of the plan"),
        AttributeInfo(name="value.type", type="string", description="Type of the memory"),
    ]

    def put_memory(
        self,
        plans_set_id: str,
        plan_id: str,
        question: str,
        plan: str,
        source: str,
        ttl: Optional[float] = None,
    ) -> None:
        """
        Add a memory for a possible plan.

        Args:
            plans_set_id (str): The unique identifier for the set of plans.
            plan_id (str): The unique identifier for the plan.
            question (str): A question derived from the plan.
            plan (str): The plan details.
            source (str): The source of the plan.
            ttl (Optional[float]): Time-to-live for the memory in minutes.
        """
        namespace = (self.MEMORY_NAME, plans_set_id)
        value = {
            "question": question,
            "plan": plan,
            "source": source,
            "type": "possible_plans_memory",
        }
        super().put_memory(namespace=namespace, key=plan_id, value=value, ttl=ttl)

    async def aput_memory(
        self,
        plans_set_id: str,
        plan_id: str,
        question: str,
        plan: str,
        source: str,
        ttl: Optional[float] = None,
    ) -> None:
        """
        Asynchronously add a memory for a possible plan.

        Args:
            plans_set_id (str): The unique identifier for the set of plans.
            plan_id (str): The unique identifier for the plan.
            question (str): A question derived from the plan.
            plan (str): The plan details.
            source (str): The source of the plan.
            ttl (Optional[float]): Time-to-live for the memory in minutes.
        """
        namespace = (self.MEMORY_NAME, plans_set_id)
        value = {
            "question": question,
            "plan": plan,
            "source": source,
            "type": "possible_plans_memory",
        }
        await super().aput_memory(namespace=namespace, key=plan_id, value=value, ttl=ttl)

    def get_memory(self, plans_set_id: str, plan_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a memory for a possible plan.

        Args:
            plans_set_id (str): The unique identifier for the set of plans.
            plan_id (str): The unique identifier for the plan.

        Returns:
            Optional[Dict[str, Any]]: The retrieved memory or None if not found.
        """
        namespace = (self.MEMORY_NAME, plans_set_id)
        item = super().get_memory(namespace=namespace, key=plan_id)
        return item.value if item else None

    async def aget_memory(self, plans_set_id: str, plan_id: str) -> Optional[Dict[str, Any]]:
        """
        Asynchronously retrieve a memory for a possible plan.

        Args:
            plans_set_id (str): The unique identifier for the set of plans.
            plan_id (str): The unique identifier for the plan.

        Returns:
            Optional[Dict[str, Any]]: The retrieved memory or None if not found.
        """
        namespace = (self.MEMORY_NAME, plans_set_id)
        item = await super().aget_memory(namespace=namespace, key=plan_id)
        return item.value if item else None

    def delete_memory(self, plans_set_id: str, plan_id: str) -> None:
        """
        Delete a memory for a possible plan.

        Args:
            plans_set_id (str): The unique identifier for the set of plans.
            plan_id (str): The unique identifier for the plan.
        """
        namespace = (self.MEMORY_NAME, plans_set_id)
        super().delete_memory(namespace=namespace, key=plan_id)

    async def adelete_memory(self, plans_set_id: str, plan_id: str) -> None:
        """
        Asynchronously delete a memory for a possible plan.

        Args:
            plans_set_id (str): The unique identifier for the set of plans.
            plan_id (str): The unique identifier for the plan.
        """
        namespace = (self.MEMORY_NAME, plans_set_id)
        await super().adelete_memory(namespace=namespace, key=plan_id)

    def delete_memories_by_namespace(self, plans_set_id: str) -> None:
        """
        Delete all possible plans memories in the given namespace.

        Args:
            plans_set_id (str): The unique identifier for the plans set.
        """
        namespace = (self.MEMORY_NAME, plans_set_id)
        super().delete_memories_by_namespace(namespace)

    def search_memories(
        self,
        plans_set_id: str,
        query: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
        filter_sources: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for memories of possible plans.

        Args:
            plans_set_id (str): The unique identifier for the set of plans.
            query (Optional[str]): A query string for semantic search.
            limit (int): Maximum number of results to return.
            offset (int): Number of results to skip.

        Returns:
            List[Dict[str, Any]]: A list of matching memories.
        """
        namespace_prefix = (self.MEMORY_NAME, plans_set_id)
        base_filter = 'eq("value.type", "possible_plans_memory")'
        filter_list = [base_filter]
        if filter_sources:
            filter_sources = 'or(' + ','.join([f'eq("value.source", "{source}")' for source in filter_sources]) + ')'
            filter_list.append(filter_sources)
        filter = 'and(' + ','.join(filter_list) + ')'
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
        plans_set_id: str,
        query: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
        filter_sources: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Asynchronously search for memories of possible plans.

        Args:
            plans_set_id (str): The unique identifier for the set of plans.
            query (Optional[str]): A query string for semantic search.
            limit (int): Maximum number of results to return.
            offset (int): Number of results to skip.

        Returns:
            List[Dict[str, Any]]: A list of matching memories.
        """
        namespace_prefix = (self.MEMORY_NAME, plans_set_id)
        base_filter = 'eq("value.type", "possible_plans_memory")'
        filter_list = [base_filter]
        if filter_sources:
            filter_sources = 'or(' + ','.join([f'eq("value.source", "{source}")' for source in filter_sources]) + ')'
            filter_list.append(filter_sources)
        filter = 'and(' + ','.join(filter_list) + ')'
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
        plans_set_id: str,
        plans_descriptors: List[PlanDescriptorSchema],
        config: PossiblePlansMemoryConfigSchema = {"chain_llm": None, "k_review_candidates": 5, "rounds": 1},
        ttl: Optional[float] = None,
    ) -> None:
        """
        Build and persist plans with processed questions, including plan checking.

        Args:
            plans_set_id (str): The unique identifier for the set of plans.
            plans_descriptors (List[PlanDescriptorSchema]): A list of dictionaries with 'plan', 'question', and optional 'source'.
            config (PossiblePlansMemoryConfigSchema): Configuration for the processing and checking chains.
            ttl (Optional[float]): Time-to-live for the memory in minutes.
        """
        # Initialize configuration
        config = PossiblePlansMemoryConfigSchema(**config).model_dump()
        k_review_candidates = config.get("k_review_candidates", 5)
        rounds = config.get("rounds", 1)

        if config['chain_llm'] is None:
            processing_chain, checking_chain = None, None
        else:
            # Create chains
            processing_chain = create_plan_processing_chain(
                prompt_language=config["chain_llm_prompt_language"],
                llm=config["chain_llm"]
            )
            checking_chain = create_plan_checking_chain(
                prompt_language=config["chain_llm_prompt_language"],
                llm=config["chain_llm"]
            )

        async def process_plan_descriptor(plan_descriptor: PlanDescriptorSchema) -> None:

            if processing_chain is None or checking_chain is None:
                plan_id = hashlib.sha256(plan_descriptor['question'].encode("utf-8")).hexdigest()
                await self.aput_memory(
                    plans_set_id=plans_set_id,
                    plan_id=plan_id,
                    question=plan_descriptor['question'],
                    plan=plan_descriptor['plan'],
                    source=plan_descriptor['source'],
                    ttl=ttl,
                )
                # wait for the index to be updated
                await asyncio.sleep(1)
                
            else:
                for _ in range(rounds):
                    source = plan_descriptor.get("source", "unknown")
                    processed_output = await processing_chain.ainvoke({"text": plan_descriptor["plan"]})
                    candidate_plans = processed_output.plans

                    
                    for candidate_plan in candidate_plans:
                        candidate_question = candidate_plan["question"] if isinstance(candidate_plan, dict) else candidate_plan.question
                        candidate_plan_text = candidate_plan["plan"] if isinstance(candidate_plan, dict) else candidate_plan.plan

                        # Search for existing plans
                        existing_plans = self.search_memories(
                            plans_set_id=plans_set_id,
                            query=candidate_question,
                            limit=k_review_candidates,
                            filter_sources=[source]
                        )

                        # If no existing plans, directly insert the plan
                        if len(existing_plans) < k_review_candidates:
                            plan_id = hashlib.sha256(candidate_question.encode("utf-8")).hexdigest()
                            await self.aput_memory(
                                plans_set_id=plans_set_id,
                                plan_id=plan_id,
                                question=candidate_question,
                                plan=candidate_plan_text,
                                source=source,
                                ttl=ttl
                            )
                            # wait for the index to be updated
                            await asyncio.sleep(1)
                            continue
                        
                        if candidate_question in set(plan["question"] for plan in existing_plans) and candidate_plan_text in set(plan["plan"] for plan in existing_plans):
                            continue

                        # Run the checking chain
                        checking_result = await checking_chain.ainvoke(
                            {
                                "text": plan_descriptor["plan"],
                                "candidate_plan": {"question": candidate_question, "plan": candidate_plan_text},
                                "existing_plans": existing_plans,  # Pass the entire list of existing plans
                            }
                        )

                        # Handle the result
                        for question_to_remove in checking_result.questions_to_remove:
                            existing_plan_id = hashlib.sha256(question_to_remove.encode("utf-8")).hexdigest()
                            await self.adelete_memory(plans_set_id=plans_set_id, plan_id=existing_plan_id)

                        for plan_to_add in checking_result.plans_to_add:
                            plan_id = hashlib.sha256(plan_to_add.question.encode("utf-8")).hexdigest()
                            await self.aput_memory(
                                plans_set_id=plans_set_id,
                                plan_id=plan_id,
                                question=plan_to_add.question,
                                plan=plan_to_add.plan,
                                source=source,
                                ttl=ttl,
                            )
                        # wait for the index to be updated
                        await asyncio.sleep(1)

        # Process all plan descriptors asynchronously
        await asyncio.gather(*(process_plan_descriptor(plan) for plan in plans_descriptors))

    def build(
        self,
        plans_set_id: str,
        plans_descriptors: List[PlanDescriptorSchema],
        config: PossiblePlansMemoryConfigSchema = {"chain_llm": None},
        ttl: Optional[float] = None,
    ) -> None:
        """
        Synchronous build method for possible plans memory.

        Args:
            plans_set_id (str): The unique identifier for the set of plans.
            plans_descriptors (List[PlanDescriptorSchema]): A list of dictionaries with 'plan', 'question', and optional 'source'.
            config (PossiblePlansMemoryConfigSchema): Configuration for the processing chain.
            ttl (Optional[float]): Time-to-live for the memory in minutes.
        """
        # Initialize configuration
        config = PossiblePlansMemoryConfigSchema(**config).model_dump()
        k_review_candidates = config.get("k_review_candidates", 5)
        rounds = config.get("rounds", 1)

        if config['chain_llm'] is None:
            processing_chain, checking_chain = None, None
        else:
            processing_chain = create_plan_processing_chain(
                prompt_language=config["chain_llm_prompt_language"],
                llm=config["chain_llm"]
            )
            checking_chain = create_plan_checking_chain(
                prompt_language=config["chain_llm_prompt_language"],
                llm=config["chain_llm"]
            )

        def process_plan_descriptor(plan_descriptor: PlanDescriptorSchema) -> None:
            if processing_chain is None or checking_chain is None:
                plan_id = hashlib.sha256(plan_descriptor['question'].encode("utf-8")).hexdigest()
                self.put_memory(
                    plans_set_id=plans_set_id,
                    plan_id=plan_id,
                    question=plan_descriptor['question'],
                    plan=plan_descriptor['plan'],
                    source=plan_descriptor['source'],
                    ttl=ttl,
                )
            else:
                for _ in range(rounds):
                    source = plan_descriptor.get("source", "unknown")
                    processed_output = processing_chain.invoke({"text": plan_descriptor["plan"]})
                    candidate_plans = processed_output.plans

                    for candidate_plan in candidate_plans:
                        candidate_question = candidate_plan["question"] if isinstance(candidate_plan, dict) else candidate_plan.question
                        candidate_plan_text = candidate_plan["plan"] if isinstance(candidate_plan, dict) else candidate_plan.plan

                        # Search for existing plans
                        existing_plans = self.search_memories(
                            plans_set_id=plans_set_id,
                            query=candidate_question,
                            limit=k_review_candidates,
                            filter_sources=[source]
                        )

                        # If no existing plans, directly insert the plan
                        if len(existing_plans) < k_review_candidates:
                            plan_id = hashlib.sha256(candidate_question.encode("utf-8")).hexdigest()
                            self.put_memory(
                                plans_set_id=plans_set_id,
                                plan_id=plan_id,
                                question=candidate_question,
                                plan=candidate_plan_text,
                                source=source,
                                ttl=ttl
                            )
                            continue

                        if candidate_question in set(plan["question"] for plan in existing_plans) and candidate_plan_text in set(plan["plan"] for plan in existing_plans):
                            continue

                        # Run the checking chain
                        checking_result = checking_chain.invoke(
                            {
                                "text": plan_descriptor["plan"],
                                "candidate_plan": {"question": candidate_question, "plan": candidate_plan_text},
                                "existing_plans": existing_plans,  # Pass the entire list of existing plans
                            }
                        )

                        # Handle the result
                        for question_to_remove in checking_result.questions_to_remove:
                            existing_plan_id = hashlib.sha256(question_to_remove.encode("utf-8")).hexdigest()
                            self.delete_memory(plans_set_id=plans_set_id, plan_id=existing_plan_id)

                        for plan_to_add in checking_result.plans_to_add:
                            plan_id = hashlib.sha256(plan_to_add.question.encode("utf-8")).hexdigest()
                            self.put_memory(
                                plans_set_id=plans_set_id,
                                plan_id=plan_id,
                                question=plan_to_add.question,
                                plan=plan_to_add.plan,
                                source=source,
                                ttl=ttl,
                            )

        # Process all plan descriptors synchronously
        for plan in plans_descriptors:
            process_plan_descriptor(plan)

    def study(
        self,
        plans_set_id: str,
        directories: List[str],
        config: PossiblePlansMemoryConfigSchema = {"chain_llm": None},
    ) -> None:
        """
        Create a set of plans by processing YAML files in the given directories.

        Args:
            plans_set_id (str): The unique identifier for this set of plans.
            directories (List[str]): A list of directory paths to search for YAML files.
            config (PossiblePlansMemoryConfigSchema): Configuration for the processing chain.
        """
        plans_descriptors = []

        for directory in directories:
            for filename in os.listdir(directory):
                if filename.endswith(".yaml") or filename.endswith(".yml"):
                    file_path = os.path.join(directory, filename)
                    with open(file_path, "r", encoding="utf-8") as file:
                        try:
                            data = yaml.safe_load(file)
                            source = data.get("source", "unknown").strip()
                            text = data.get("text", "").strip()
                            title = data.get("title", "").strip()
                            if text:
                                plans_descriptors.append({"plan": text, "question": title, "source": source})
                        except yaml.YAMLError:
                            raise ValueError(f"Invalid YAML format in file: {file_path}")

        # Call the build method with the extracted descriptors and config
        self.build(plans_set_id=plans_set_id, plans_descriptors=plans_descriptors, config=config)
