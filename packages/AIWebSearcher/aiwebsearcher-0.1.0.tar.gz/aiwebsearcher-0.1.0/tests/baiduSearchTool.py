import json
from typing import Any, Dict, List, Optional
from bs4 import BeautifulSoup
import trafilatura

from agno.tools import Toolkit
from agno.utils.log import log_debug

try:
    from baidusearch.baidusearch import search  # type: ignore
except ImportError:
    raise ImportError("`baidusearch` not installed. Please install using `pip install baidusearch`")

try:
    from pycountry import pycountry
except ImportError:
    raise ImportError("`pycountry` not installed. Please install using `pip install pycountry`")


class BaiduSearchTools(Toolkit):
    """
    BaiduSearch is a toolkit for searching Baidu easily.

    Args:
        fixed_max_results (Optional[int]): A fixed number of maximum results.
        fixed_language (Optional[str]): A fixed language for the search results.
        headers (Optional[Any]): Headers to be used in the search request.
        proxy (Optional[str]): Proxy to be used in the search request.
        debug (Optional[bool]): Enable debug output.
    """

    def __init__(
        self,
        fixed_max_results: Optional[int] = None,
        fixed_language: Optional[str] = None,
        headers: Optional[Any] = None,
        proxy: Optional[str] = None,
        timeout: Optional[int] = 10,
        debug: Optional[bool] = False,
        enable_baidu_search: bool = True,
        all: bool = False,
        **kwargs,
    ):
        self.fixed_max_results = fixed_max_results
        self.fixed_language = fixed_language
        self.headers = headers
        self.proxy = proxy
        self.timeout = timeout
        self.debug = debug

        tools = []
        if all or enable_baidu_search:
            tools.append(self.baidu_search)

        super().__init__(name="baidusearch", tools=tools, **kwargs)

    def baidu_search(self, query: str, max_results: int = 12, language: str = "zh") -> str:
        """Execute Baidu search and return results

        Args:
            query (str): Search keyword
            max_results (int, optional): Maximum number of results to return, default 12
            language (str, optional): Search language, default Chinese

        Returns:
            str: A JSON formatted string containing the search results.
        """
        max_results = self.fixed_max_results or max_results
        language = self.fixed_language or language

        if len(language) != 2:
            try:
                language = pycountry.languages.lookup(language).alpha_2
            except LookupError:
                language = "zh"

        log_debug(f"Searching Baidu [{language}] for: {query}")

        results = search(keyword=query, num_results=max_results)

        res: List[Dict[str, str]] = []
        for idx, item in enumerate(results, 1):
            res.append(
                {
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "abstract": item.get("abstract", ""),
                    "rank": str(idx),
                }
            )
        return json.dumps(res, indent=2, ensure_ascii=False)

    def fetch_page(self, url: str, timeout_s: int | None = 10) -> str:
        """Fetch a single web page and return main text content.

        Uses trafilatura for better content extraction, falls back to BeautifulSoup.
        """
        try:
            import requests
            
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                )
            }
            resp = requests.get(url, headers=headers, timeout=timeout_s)
            resp.raise_for_status()

            text = trafilatura.extract(resp.content, include_comments=False, include_tables=False)
            if text and len(text.strip()) > 100:  # Only return if we got substantial content
                return text.strip()

            raw_text = resp.text.strip()
            return raw_text[:5000] if len(raw_text) > 5000 else raw_text

            soup = BeautifulSoup(resp.content, "html.parser")
            
            # Remove script, style, and other non-content tags
            for element in soup(["script", "style", "nav", "header", "footer", "aside", "iframe", "noscript"]):
                element.decompose()
            
            # Try to find main content area
            main_content = soup.find("main") or soup.find("article") or soup.find("div", class_=["content", "main", "article"])
            if main_content:
                text = main_content.get_text(" ", strip=True)
            else:
                text = soup.get_text(" ", strip=True)
            
            # Clean up excessive whitespace
            import re
            text = re.sub(r'\s+', ' ', text)
            
            # Limit to reasonable length (first 5000 chars)
            return text[:5000] if len(text) > 5000 else text
            
        except Exception as e:
            log_debug(f"Error fetching page {url}: {e}")
            return ""


if __name__ == "__main__":
    tool = BaiduSearchTools(debug=True)
    jsonOutput = tool.baidu_search("人工智能", language="zh")
    jsonData = json.loads(jsonOutput)
    for item in jsonData:
        print("--------------------------------")
        print(item)
    # print(tool.fetch_page("https://www.sohu.com"))
