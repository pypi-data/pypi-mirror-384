from engines4ai.searxng import SearXNG

from dataclasses import dataclass
from typing import List
from pprint import pprint
import traceback

@dataclass
class NewsData:
    category: str
    content: str
    engine: str
    engines: List[str]
    img_src: str
    parsed_url: List[str]
    positions: List[int]
    priority: str
    score: float
    template: str
    thumbnail: str
    title: str
    url: str
    

def news_engine(query: str, pageno: int = 1, engines: list[str]=[]) -> List[NewsData]:
    engine = SearXNG()
    
    try:
        # Only set categories if no specific engines are requested
        search_params = {
            "query": query,
            "pageno": pageno
        }
        
        if engines:
            search_params["engines"] = engines
        else:
            search_params["categories"] = ["news"]
            
        results = engine.search(**search_params)['results']
        news_list = []
        for result in results:
            news = NewsData(
                category=result.get("category", ""),
                content=result.get("content", ""),
                engine=result.get("engine", ""),
                engines=result.get("engines", []),
                img_src=result.get("img_src", ""),
                parsed_url=result.get("parsed_url", []),
                positions=result.get("positions", []),
                priority=result.get("priority", ""),
                score=result.get("score", 0.0),
                template=result.get("template", ""),
                thumbnail=result.get("thumbnail", ""),
                title=result.get("title", ""),
                url=result.get("url", "")
            )
            news_list.append(news)
        return news_list

    except Exception as e:
        print(f"Error in news_engine: {type(e).__name__} - {str(e)}")
        traceback.print_exc()
        return []


if __name__ == "__main__":
    news_results = news_engine("DeepSeek AI China")
    for news in news_results[:3]:
        pprint(news)
