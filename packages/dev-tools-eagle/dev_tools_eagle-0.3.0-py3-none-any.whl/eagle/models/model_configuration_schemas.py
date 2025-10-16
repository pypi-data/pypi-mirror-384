from pydantic import BaseModel, Field

# Schemas
class LLMModelConfigSchema(BaseModel):
    """
    Schema for the LLM model configuration.
    """
    prompt_language: str = Field(default="pt-br", description="Language for the prompt")
    model_name: str = Field(..., description="Name of the LLM model")
    temperature: float = Field(default=0.0, description="Temperature for the LLM")
    max_tokens: int = Field(default=400, description="Maximum number of tokens")