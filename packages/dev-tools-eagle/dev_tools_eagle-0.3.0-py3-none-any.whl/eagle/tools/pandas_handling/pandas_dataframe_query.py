from typing import Dict, Any
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from eagle.memory.shared.shared_objects_memory import SharedObjectsMemory
import pandas as pd

class PandasDataFrameQueryInput(BaseModel):
    df_id: str = Field(description="The ID of the DataFrame stored in SharedObjectsMemory.")
    query: str = Field(description="The pandas query string to filter the DataFrame.")

class PandasDataFrameQuery(BaseTool):
    name: str = "pandas_dataframe_query"
    description: str = (
        "A tool to query a pandas DataFrame stored in SharedObjectsMemory. "
        "It retrieves the DataFrame using its ID and applies a pandas query to it."
    )
    memory: SharedObjectsMemory
    chat_id: str  # Added chat_id parameter

    args_schema = PandasDataFrameQueryInput

    def _run(self, **_inputs: PandasDataFrameQueryInput) -> Dict[str, Any]:
        """
        Run the tool synchronously.

        Args:
            inputs (PandasDataFrameQueryInput): Input object containing df_id and query.

        Returns:
            Dict[str, Any]: The textual representation of the query result.
        """
        inputs = PandasDataFrameQueryInput(**_inputs)

        # Retrieve the DataFrame from SharedObjectsMemory
        shared_object = self.memory.get_memory(chat_id=self.chat_id, object_id=inputs.df_id)  # Use self.chat_id
        if not shared_object or not isinstance(shared_object.object, pd.DataFrame):
            raise ValueError(f"No DataFrame found with ID: {inputs.df_id}")

        df = shared_object.object

        # Apply the pandas query
        try:
            result_df = df.query(inputs.query)
        except Exception as e:
            raise ValueError(f"Error while applying query: {e}")

        # Convert the result to a textual representation
        result_text = result_df.to_string(index=False)

        return {"result": result_text}

    async def _arun(self, **_inputs: PandasDataFrameQueryInput) -> Dict[str, Any]:
        """
        Run the tool asynchronously.

        Args:
            inputs (PandasDataFrameQueryInput): Input object containing df_id and query.

        Returns:
            Dict[str, Any]: The textual representation of the query result.
        """
        inputs = PandasDataFrameQueryInput(**_inputs)

        # Retrieve the DataFrame from SharedObjectsMemory
        shared_object = await self.memory.aget_memory(chat_id=self.chat_id, object_id=inputs.df_id)  # Use self.chat_id
        if not shared_object or not isinstance(shared_object.object, pd.DataFrame):
            raise ValueError(f"No DataFrame found with ID: {inputs.df_id}")

        df = shared_object.object

        # Apply the pandas query
        try:
            result_df = df.query(inputs.query)
        except Exception as e:
            raise ValueError(f"Error while applying query: {e}")

        # Convert the result to a textual representation
        result_text = result_df.to_string(index=False)

        return {"result": result_text}
