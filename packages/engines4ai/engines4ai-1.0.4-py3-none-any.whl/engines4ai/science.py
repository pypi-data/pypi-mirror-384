from engines4ai.searxng import SearXNG

from dataclasses import dataclass, field
from typing import List, Optional
import traceback
from pprint import pprint


@dataclass
class ScienceData:
    authors: List[str] = field(default_factory=list)
    category: str = ""
    comments: Optional[str] = None
    content: str = ""
    doi: Optional[str] = None
    engine: str = ""
    engines: List[str] = field(default_factory=list)
    img_src: str = ""
    journal: Optional[str] = None
    parsed_url: List[str] = field(default_factory=list)
    pdf_url: Optional[str] = None
    positions: List[int] = field(default_factory=list)
    priority: str = ""
    publishedDate: Optional[str] = None
    score: float = 0.0
    tags: List[str] = field(default_factory=list)
    template: str = ""
    thumbnail: str = ""
    title: str = ""
    url: str = ""


def science_engine(query: str, pageno: int = 1, engines: list[str]=[]) -> List[ScienceData]:
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
            search_params["categories"] = ["science"]
            
        results = engine.search(**search_params)['results']
        science_list = []
        for result in results:
            science = ScienceData(
                authors=result.get("authors", []),
                category=result.get("category", ""),
                comments=result.get("comments", None),
                content=result.get("content", ""),
                doi=result.get("doi", None),
                engine=result.get("engine", ""),
                engines=result.get("engines", []),
                img_src=result.get("img_src", ""),
                journal=result.get("journal", None),
                parsed_url=result.get("parsed_url", []),
                pdf_url=result.get("pdf_url", None),
                positions=result.get("positions", []),
                priority=result.get("priority", ""),
                publishedDate=result.get("publishedDate", None),
                score=result.get("score", 0.0),
                tags=result.get("tags", []),
                template=result.get("template", ""),
                thumbnail=result.get("thumbnail", ""),
                title=result.get("title", ""),
                url=result.get("url", "")
            )
            science_list.append(science)
        return science_list

    except Exception as e:
        print(f"Error in science_engine: {type(e).__name__} - {str(e)}")
        traceback.print_exc()
        return []


if __name__ == "__main__":
    results = science_engine("DeepSeek")
    for paper in results[:3]:
        pprint(paper)
