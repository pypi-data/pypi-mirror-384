from langchain_community.tools.google_scholar.tool import GoogleScholarQueryRun as _GoogleScholarQueryRun
from langchain_community.utilities.google_scholar import GoogleScholarAPIWrapper
from pydantic import Field

class GoogleScholarQueryRun(_GoogleScholarQueryRun):
    name: str = "google_scholar_modified"
    api_wrapper: GoogleScholarAPIWrapper = Field(default_factory=GoogleScholarAPIWrapper)
