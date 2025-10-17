# https://docs.searxng.org/dev/search_api.html


from pprint import pprint
import requests
from typing import Optional, List, Literal
from dotenv import load_dotenv
import os

class SearXNG:
    def __init__(self, base_url:str=""):
        load_dotenv(override=True)
        self.base_url = os.getenv("SEARXNG_BASE_URL")
        self.api_key = os.getenv("SEARXNG_API_KEY")

        if base_url:
            self.base_url = base_url
        
        self.base_url = self.base_url.rstrip("/") + "/search"

    def search(
        self,
        query: str,
        categories: Optional[
            List[
                Literal[
                    "general", "images", "news", "it", "science",
                    "videos", "music", "social media", "files", "map"
                ]
            ]
        ] = None,
        engines: Optional[List[str]] = None,
        language: Optional[str] = None,
        pageno: int = 1,
        time_range: Optional[Literal["day", "month", "year"]] = None,
        format: Optional[Literal["json", "csv", "rss"]] = "json",
        results_on_new_tab: int = 0,
        image_proxy: Optional[bool] = None,
        autocomplete: Optional[
            Literal[
                "google", "dbpedia", "duckduckgo", "mwmb1", "startpage",
                "wikipedia", "stract", "swisscows", "qwant"
            ]
        ] = None,
        safesearch: Optional[Literal[0, 1, 2]] = None,
        theme: Optional[str] = "simple",
        enabled_plugins: Optional[List[str]] = None,
        disabled_plugins: Optional[List[str]] = None,
        enabled_engines: Optional[List[str]] = None,
        disabled_engines: Optional[List[str]] = None,
        timeout: Optional[float] = 300,
    ) -> dict:
        params = {
            "q": query,
            "pageno": pageno,
            "format": format,
            "results_on_new_tab": results_on_new_tab,
            "theme": theme,
        }

        if categories:
            params["categories"] = ",".join(categories)
        if engines:
            params["engines"] = ",".join(engines)
        if language:
            params["language"] = language
        if time_range:
            params["time_range"] = time_range
        if image_proxy is not None:
            params["image_proxy"] = str(image_proxy).lower()
        if autocomplete:
            params["autocomplete"] = autocomplete
        if safesearch is not None:
            params["safesearch"] = safesearch
        if enabled_plugins:
            params["enabled_plugins"] = ",".join(enabled_plugins)
        if disabled_plugins:
            params["disabled_plugins"] = ",".join(disabled_plugins)
        if enabled_engines:
            params["enabled_engines"] = ",".join(enabled_engines)
        if disabled_engines:
            params["disabled_engines"] = ",".join(disabled_engines)
            
        params["key"] = self.api_key

        response = requests.get(self.base_url, params=params, timeout=timeout)
        response.raise_for_status()

        return response.json()


if __name__ == "__main__":
    searxng = SearXNG()
    results = searxng.search(query="google")
    pprint(results)