from langchain_community.tools.arxiv.tool import ArxivQueryRun, ArxivInput
from pydantic import Field, BaseModel
from typing import Type

class ArvixModifiedInput(ArxivInput):
    """Modified ArxivInput class to include other parameters"""
    top_k_results: int = Field(description="Number of top results to return", default=5)

class ArxivModifiedQueryRun(ArxivQueryRun):

    name: str = "arxiv_modified"
    args_schema: Type[BaseModel] = ArvixModifiedInput

    """Modified ArxivQueryRun class to include other parameters"""
    def _run(self, **inputs: ArvixModifiedInput) -> str:
        """Run the query and return the results."""
        _inputs = ArvixModifiedInput(**inputs)
        self.api_wrapper.top_k_results = _inputs.top_k_results
        return self.api_wrapper.run(_inputs.query)
    