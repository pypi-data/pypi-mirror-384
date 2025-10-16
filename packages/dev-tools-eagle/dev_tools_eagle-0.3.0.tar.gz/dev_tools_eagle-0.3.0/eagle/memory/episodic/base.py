from eagle.memory.base import StoredMemory
from langchain.chains.query_constructor.base import AttributeInfo

class EpisodicMemory(StoredMemory):
    """
    Base class for episodic memory, providing shared functionality for specific memory types.

    Args:
        store_class (type): The class of the store to use for persistence.
        embedding_model (Embeddings): The embedding model to use.
        embedding_dims (int): The dimensions of the embedding model.
    """

    MEMORY_NAME = "eagle-episodic-memory"

    EMBEDDED_FIELDS = ["description"]

    VALUE_EXAMPLE = {
        "description": "Example description",
        "type": "episodic_memory"
    }

    ATTRIBUTE_INFO=[
        AttributeInfo(name="value.description", type="string", description="Description of the memory"),
        AttributeInfo(name="value.type", type="string", description="Type of the memory"),
    ]
