# ----------------------------------------------------------------------------------------------------
# IBM Confidential
# Licensed Materials - Property of IBM
# 5737-H76, 5900-A3Q
# © Copyright IBM Corp. 2025  All Rights Reserved.
# US Government Users Restricted Rights - Use, duplication or disclosure restricted by
# GSA ADPSchedule Contract with IBM Corp.
# ----------------------------------------------------------------------------------------------------


from typing import List, Optional, Type

import requests
from langchain.callbacks.manager import CallbackManagerForToolRun
from langchain.tools import BaseTool
from pydantic import BaseModel, PrivateAttr
from ibm_watsonx_gov.utils.python_utils import get
from ...schemas.search_tool_schema import GoogleSearchToolConfig, SearchToolInput


class GoogleSearchTool(BaseTool):
    """
    Tool to search and get results using google search engine

    Examples:
        Basic usage
            .. code-block:: python

                google_search_tool = GoogleSearchTool()
                google_search_tool.invoke({"query":"What is RAG?"})
    """
    name: str = "google_search_tool"
    description: str = (
        "Search Google using SerpAPI and return top-k results, "
        "Default top-k :3"
    )
    args_schema: Type[BaseModel] = SearchToolInput

    _top_k_results: any = PrivateAttr()

    _serpapi_key: str = PrivateAttr()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._headers = {"User-Agent": "Mozilla/5.0"}
        from ibm_watsonx_gov.tools.utils.package_utils import \
            install_and_import_packages

        install_and_import_packages(["bs4", "google-search-results"])

        # Load args into config
        config = GoogleSearchToolConfig(**kwargs)
        self._top_k_results = config.top_k_results
        self._serpapi_key = config.serpapi_key


    def _fetch_page_content(self, url: str, max_chars: int = 5000) -> str:
        try:
            from bs4 import BeautifulSoup
            response = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            soup = BeautifulSoup(response.text, "html.parser")

            # Remove JS scripts & css styles
            for script in soup(["script", "style"]):
                script.extract()

            # Join text with newlines between paragraphs
            paragraphs = [para.get_text(strip=True) for para in soup.find_all("p")]
            text = "".join(paragraphs)

            return text
        except Exception as e:
           print(f"Skipping {url}: {e}")
           return ""

    # Define Google Search Tool Without API Key
    def _run(self,
             query: str,
             top_k_results: int = None,
             run_manager: Optional[CallbackManagerForToolRun] = None,
             **kwargs) -> List[str]:
        """Performs a Google search and extracts content from the top results."""
        from bs4 import BeautifulSoup
        from serpapi import GoogleSearch

        if top_k_results is None:
            top_k_results = self._top_k_results

        search_results = GoogleSearch({
            "q": query,
            "api_key": self._serpapi_key
        })
        search_results = search_results.get_dict()

        organic_results = get(search_results, "organic_results", default=[])

        results = []
        for res in organic_results[:top_k_results]:
            link = res.get("link")
            if link:
                # Extract text from the webpage
                content = self._fetch_page_content(link)
                results.append(content)

        return results
