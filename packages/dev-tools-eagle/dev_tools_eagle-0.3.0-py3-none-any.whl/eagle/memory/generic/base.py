from eagle.memory.base import StoredMemory
from langchain.chains.query_constructor.base import AttributeInfo

class GenericMemory(StoredMemory):
    """
    Memory for storing and managing generic data.

    Args:
        store_class (type): The class of the store to use for persistence.
        embedding_model (Embeddings): The embedding model to use.
        embedding_dims (int): The dimensions of the embedding model.
    """

    MEMORY_NAME = "eagle-generic-memory"

    EMBEDDED_FIELDS = ["description"]

    VALUE_EXAMPLE = {
        "description": "Example generic data",
        "type": "generic_memory",
    }

    ATTRIBUTE_INFO = [
        AttributeInfo(name="value.description", type="string", description="Description of the memory"),
        AttributeInfo(name="value.type", type="string", description="Type of the memory"),
    ]

