import os
from typing import Any, Literal, TypedDict

import httpx
from dotenv import load_dotenv
from markitdown import MarkItDown
from universal_mcp.applications.application import BaseApplication

load_dotenv()


class SeriesItem(TypedDict):
    seriesName: str
    value: float


class ChartDataItem(TypedDict):
    xAxisLabel: str
    series: list[SeriesItem]


class PieChartDataItem(TypedDict):
    label: str
    value: float


class ColumnDefinition(TypedDict):
    key: str
    label: str
    type: Literal["string", "number", "date", "boolean"] | None


class UiApp(BaseApplication):
    """An application for creating UI tools"""

    def __init__(self, **kwargs):
        """Initialize the DefaultToolsApp"""
        super().__init__(name="ui")
        self.markitdown = MarkItDown(enable_plugins=True)
        self.exa_base_url = "https://api.exa.ai"
        self.exa_api_key = os.getenv("EXA_API_KEY")

    def create_bar_chart(
        self,
        title: str,
        data: list[ChartDataItem],
        description: str | None = None,
        y_axis_label: str | None = None,
    ):
        """Create a bar chart with multiple data series.

        Args:
            title (str): The title of the chart.
            data (List[ChartDataItem]): Chart data with x-axis labels and series values.
            description (Optional[str]): Optional description for the chart.
            y_axis_label (Optional[str]): Optional label for the Y-axis.

        Tags:
            important
        """
        return "Success"

    def create_line_chart(
        self,
        title: str,
        data: list[ChartDataItem],
        description: str | None = None,
        y_axis_label: str | None = None,
    ):
        """Create a line chart with multiple data series.

        Args:
            title (str): The title of the chart.
            data (List[ChartDataItem]): Chart data with x-axis labels and series values.
            description (Optional[str]): Optional description for the chart.
            y_axis_label (Optional[str]): Optional label for the Y-axis.

        Tags:
            important
        """
        return "Success"

    def create_pie_chart(
        self,
        title: str,
        data: list[PieChartDataItem],
        description: str | None = None,
        unit: str | None = None,
    ):
        """Create a pie chart.

        Args:
            title (str): The title of the chart.
            data (List[PieChartDataItem]): Data for the pie chart with labels and values.
            description (Optional[str]): Optional description for the chart.
            unit (Optional[str]): Optional unit for the values.

        Tags:
            important
        """
        return "Success"

    def create_table(
        self,
        title: str,
        columns: list[ColumnDefinition],
        data: list[dict],
        description: str | None = None,
    ):
        """Create an interactive table with data.

        The table will automatically have sorting, filtering, and search functionality. Note that this only creates a table on the frontend. Do not mix this up with tables from applications like google_sheet, airtable.

        Args:
            title (str): The title of the table.
            columns (List[ColumnDefinition]): Column configuration array.
            data (List[dict]): Array of row objects. Each object should have keys matching the column keys.
            description (Optional[str]): Optional description for the table.

        Tags:
            important
        """
        return "Success"

    def _fetch_exa(self, endpoint: str, body: dict, error_solution: str) -> dict[str, Any]:
        if not self.exa_api_key:
            return {
                "isError": True,
                "error": "EXA_API_KEY is not configured",
                "solution": error_solution,
            }

        url = f"{self.exa_base_url}{endpoint}"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.exa_api_key,
        }
        try:
            response = httpx.post(url, json=body, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {
                "isError": True,
                "error": str(e),
                "solution": error_solution,
            }

    def web_search(
        self,
        query: str,
        numResults: int | None = None,
        type: Literal["auto", "keyword", "neural"] | None = None,
        category: str | None = None,
        includeDomains: list[str] | None = None,
        excludeDomains: list[str] | None = None,
        startPublishedDate: str | None = None,
        endPublishedDate: str | None = None,
        maxCharacters: int | None = None,
    ) -> dict[str, Any]:
        """
        Search the web using Exa AI - performs real-time web searches with semantic and neural search capabilities. Returns high-quality, relevant results with full content extraction.

        Args:
            query (str): Search query.
            numResults (Optional[int]): Number of search results to return.
            type (Optional[str]): Search type - auto lets Exa decide, keyword for exact matches, neural for semantic search.
            category (Optional[str]): Category to focus the search on.
            includeDomains (Optional[List[str]]): List of domains to specifically include in search results.
            excludeDomains (Optional[List[str]]): List of domains to specifically exclude from search results.
            startPublishedDate (Optional[str]): Start date for published content (YYYY-MM-DD format).
            endPublishedDate (Optional[str]): End date for published content (YYYY-MM-DD format).
            maxCharacters (Optional[int]): Maximum characters to extract from each result.

        Returns:
            dict[str, Any]: Exa search response. On error, returns { isError, error, solution }.

        Tags:
            important
        """
        # Build request body
        request_body: dict[str, Any] = {
            "query": query,
            "type": type or "auto",
            "numResults": numResults or 5,
            "contents": {
                "text": {"maxCharacters": maxCharacters or 3000},
                "livecrawl": "preferred",
            },
        }

        # Optional fields (only include if provided)
        if category is not None:
            request_body["category"] = category
        if includeDomains:
            request_body["includeDomains"] = includeDomains
        if excludeDomains:
            request_body["excludeDomains"] = excludeDomains
        if startPublishedDate is not None:
            request_body["startPublishedDate"] = startPublishedDate
        if endPublishedDate is not None:
            request_body["endPublishedDate"] = endPublishedDate

        error_solution = (
            "A web search error occurred. First, explain to the user what caused this specific "
            "error and how they can resolve it. Then provide helpful information based on your "
            "existing knowledge to answer their question."
        )

        result = self._fetch_exa("/search", request_body, error_solution)

        # Add guide if not an error
        if not result.get("isError"):
            result["guide"] = (
                "Use the search results to answer the user's question. Summarize the content and ask if "
                "they have any additional questions about the topic."
            )
        return result

    def web_content(
        self,
        urls: list[str],
        maxCharacters: int | None = None,
        livecrawl: Literal["always", "fallback", "preferred"] | None = None,
    ) -> dict[str, Any]:
        """
        Extract detailed content from specific URLs using Exa AI - retrieves full text content, metadata, and structured information from web pages with live crawling capabilities.

        Args:
            urls (List[str]): List of URLs to extract content from.
            maxCharacters (Optional[int]): Maximum characters to extract from each URL.
            livecrawl (Optional[str]): Live crawling preference - always forces live crawl, fallback uses cache first, preferred tries live first.

        Returns:
            dict[str, Any]: Exa contents response. On error, returns { isError, error, solution }.

        Tags:
            important
        """
        request_body: dict[str, Any] = {
            "ids": urls,
            "contents": {
                "text": {"maxCharacters": maxCharacters or 3000},
                "livecrawl": livecrawl or "preferred",
            },
        }

        error_solution = (
            "A web content extraction error occurred. First, explain to the user what caused this "
            "specific error and how they can resolve it. Then provide helpful information based on "
            "your existing knowledge to answer their question."
        )

        return self._fetch_exa("/contents", request_body, error_solution)

    def list_tools(self):
        """List all available tool methods in this application.

        Returns:
            list: A list of callable tool methods.
        """
        return [
            self.create_bar_chart,
            self.create_line_chart,
            self.create_pie_chart,
            self.create_table,
            self.web_search,
            self.web_content,
        ]
