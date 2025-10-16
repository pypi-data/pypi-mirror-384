from typing import Annotated
from pydantic import BaseModel, Field

# Schemas
class ToolConfigSchema(BaseModel):
    """
    Schema for the LLM model configuration.
    """
    tool_name: str = Field(..., description="Name of the tool")
    init_kwargs: dict = Field(..., description="Initialization arguments for the tool")