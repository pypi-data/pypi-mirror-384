from engines4ai.searxng import SearXNG

from pprint import pprint
from dataclasses import dataclass, field
from typing import List, Optional, Literal


@dataclass
class GeneraleData:
    category: str = ''
    content: str = ''
    engine: str = ''
    engines: List[str] = field(default_factory=list)
    img_src: str = ''
    parsed_url: List[str] = field(default_factory=list)
    positions: List[int] = field(default_factory=list)
    priority: str = ''
    publishedDate: Optional[str] = None
    score: float = 0.0
    template: str = ''
    thumbnail: str = ''
    title: str = ''
    url: str = ''
    

def general_engine(query: str, pageno: int = 1, engines: list[str]=[], time_range: Literal["day", "month", "year"] = None) -> List[GeneraleData]:
    engine = SearXNG()

    try:
        results = engine.search(query=query, pageno=pageno, engines=engines, time_range=time_range)['results']
        general = []
        for result in results:
            data = GeneraleData(
                category=result.get("category", ""),
                content=result.get("content", ""),
                engine=result.get("engine", ""),
                engines=result.get("engines", []),
                img_src=result.get("img_src", ""),
                parsed_url=result.get("parsed_url", []),
                positions=result.get("positions", []),
                priority=result.get("priority", ""),
                publishedDate=result.get("publishedDate", None),
                score=result.get("score", 0.0),
                template=result.get("template", ""),
                thumbnail=result.get("thumbnail", ""),
                title=result.get("title", ""),
                url=result.get("url", "")
            )
            general.append(data)
        return general

    except Exception as e:
        print(f"Error in general_engine: {type(e).__name__} - {str(e)}")
        raise


if __name__ == "__main__":  
    results = general_engine("openai-python")
    pprint(results[:3])

