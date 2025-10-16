"""Tool for interacting with Yahoo Finance using yfinance."""
import warnings
from typing import Any, Dict, Optional, Type, Union
import yfinance as yf
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
import pandas as pd

class YFinanceAPIWrapper(BaseModel):
    """Wrapper for Yahoo Finance API using yfinance."""

    session: Optional[Any] = None

    def load_custom_session(self, session: Any) -> None:
        """Load a custom requests.Session for the API wrapper."""
        self.session = session

    def get_stock_info(self, ticker: str) -> Dict[str, Any]:
        """Fetch stock information for a given ticker."""
        stock = yf.Ticker(ticker, session=self.session)
        info = stock.info
        if not info:
            return {"error": f"No data found for ticker: {ticker}"}
        return info

    def get_stock_history(
        self, ticker: str, period: str = "1mo", interval: str = "1d"
    ) -> pd.DataFrame:
        """Fetch historical data for a given ticker."""
        stock = yf.Ticker(ticker, session=self.session)
        history = stock.history(period=period, interval=interval)
        return history

class YFinanceInput(BaseModel):
    """Input for the Yahoo Finance tool."""

    ticker: str = Field(description="Stock ticker symbol to look up")
    # action: str = Field(
    #     description="Action to perform: 'info' for stock info, 'history' for historical data"
    # )
    period: Optional[str] = Field(
        default="1mo", description="Period for historical data (e.g., '1mo', '1y')"
    )
    interval: Optional[str] = Field(
        default="1d", description="Interval for historical data (e.g., '1d', '1wk')"
    )


class YFinanceTool(BaseTool):
    """Tool for interacting with Yahoo Finance."""

    name: str = "yahoo_finance"
    description: str = (
        "A tool for fetching stock information and historical data from Yahoo Finance. "
        "Input should include a stock ticker and the desired action ('info' or 'history')."
    )
    api_wrapper: YFinanceAPIWrapper = Field(default_factory=YFinanceAPIWrapper)
    args_schema: Type[BaseModel] = YFinanceInput
    output_evaluation_callable: Optional[callable] = None

    def _run(self, **_inputs: YFinanceInput) -> Union[Dict[str, Any], pd.DataFrame]:
        """Run the tool."""

        inputs = YFinanceInput(**_inputs)
        ticker = inputs.ticker
        action = "history"  # Default action
        period = inputs.period
        interval = inputs.interval

        if action == "info":
            return self.api_wrapper.get_stock_info(ticker)
        elif action == "history":
            try:
                output = self.api_wrapper.get_stock_history(ticker, period, interval)
            except Exception as e:
                output = e
            if self.output_evaluation_callable:
                output = self.output_evaluation_callable(output, inputs.model_dump())
            return output
        else:
            raise ValueError(f"Invalid action: {action}. Use 'info' or 'history'.")

    def _arun(self, *args: Any, **kwargs: Any) -> Any:
        """Async run not implemented."""
        raise NotImplementedError("YFinanceTool does not support async operations.")


def YahooFinanceTool(*args: Any, **kwargs: Any) -> YFinanceTool:
    """
    Deprecated. Use YFinanceTool instead.

    Args:
        *args:
        **kwargs:

    Returns:
        YFinanceTool
    """
    warnings.warn(
        "YahooFinanceTool will be deprecated in the future. "
        "Please use YFinanceTool instead.",
        DeprecationWarning,
    )
    return YFinanceTool(*args, **kwargs)
