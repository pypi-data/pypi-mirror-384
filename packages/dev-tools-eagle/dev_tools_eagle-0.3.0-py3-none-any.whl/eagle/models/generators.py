from langchain_openai import AzureChatOpenAI
from langchain_openai.embeddings import AzureOpenAIEmbeddings
from eagle.models.config import Config

# Static data
LLMS_NO_VISION = [
    "claude-instant-v1",
    "claude-v2",
    "claude-v2.1",
    "command-light-v14",
    "command-r",
    "command-r-plus",
    "command-v14",
    "gpt-35-turbo-16k",
    "llama3-70b-instruct",
    "llama3-8b-instruct",
    "mistral-7b-instruct",
    "mistral-large",
    "mistral-small",
    "mixtral-8x7b-instruct",
    "gpt-4o",
    "claude-v35-sonnet",
    "claude-v3-haiku",
    "claude-v3-sonnet",
    "gpt-4o-petrobras"
]

LLMS_VISION = [
    "gpt-4o",
    "claude-v35-sonnet",
    "claude-v3-haiku",
    "claude-v3-sonnet"
]

EMBEDDING_MODELS = { # TODO: rever todas as dimns e confirmar os valores.
    "embedding-cohere-english-v3": {
        "dims": 1024,
    },
    "embedding-openai-ada-002": {
        "dims": 1536,
    },
    "text-embedding-3-large": {
        "dims": 2048,
    },
    "text-embedding-3-small": {
        "dims": 1536,
    }
}


# Carregar as configurações
config = Config()

# Função para obter um modelo LLM sem suporte a 'vision'
def get_llm_model(model_name, temperature=0, max_response_tokens=400):
    if model_name not in LLMS_NO_VISION:
        raise ValueError(f"Model name must be one of {LLMS_NO_VISION}")

    return AzureChatOpenAI(
        azure_deployment=model_name,
        model=model_name,
        temperature=temperature,
        max_tokens=max_response_tokens
    )

# Função para obter um modelo LLM com suporte a 'vision'
def get_vision_model(model_name, temperature=0, max_response_tokens=400):
    if model_name not in LLMS_VISION:
        raise ValueError(f"Model name must be one of {LLMS_VISION}")

    return AzureChatOpenAI(
        azure_deployment=model_name,
        model=model_name,
        temperature=temperature,
        max_tokens=max_response_tokens
    )

# Função para obter um modelo de embeddings
def get_embedding_model(model_name):
    if model_name not in EMBEDDING_MODELS:
        raise ValueError(f"Model name must be one of {EMBEDDING_MODELS}")

    return AzureOpenAIEmbeddings(
        azure_deployment=model_name,
        model=model_name
    )

def get_embedding_model_dims(model_name):
    if model_name not in EMBEDDING_MODELS:
        raise ValueError(f"Model name must be one of {EMBEDDING_MODELS}")

    return EMBEDDING_MODELS[model_name]["dims"]

def embed_texts_generator(model_name):
    def embed_texts(texts: list[str]) -> list[list[float]]:
        embedding_model = get_embedding_model(model_name)
        response = embedding_model.embed_documents(texts)
        return response
    return embed_texts