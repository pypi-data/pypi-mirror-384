from engines4ai.searxng import SearXNG

from dataclasses import dataclass, field
from typing import List, Optional
from pprint import pprint
from typing import List
import traceback


@dataclass
class ITData:
    category: str = ''
    content: str = ''
    engine: str = ''
    engines: List[str] = field(default_factory=list)
    homepage: Optional[str] = None
    img_src: str = ''
    license_name: Optional[str] = None
    license_url: Optional[str] = None
    maintainer: str = ''
    package_name: str = ''
    parsed_url: List[str] = field(default_factory=list)
    popularity: int = 0
    positions: List[int] = field(default_factory=list)
    priority: str = ''
    publishedDate: Optional[str] = None
    score: float = 0.0
    source_code_url: str = ''
    tags: List[str] = field(default_factory=list)
    template: str = ''
    thumbnail: str = ''
    title: str = ''
    url: str = ''
    

def it_engine(query: str, pageno: int = 1, engines: list[str]=[]) -> List[ITData]:
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
            search_params["categories"] = ["it"]
            
        results = engine.search(**search_params)['results']
        it_list = []
        for result in results:
            it = ITData(
                category=result.get("category", ""),
                content=result.get("content", ""),
                engine=result.get("engine", ""),
                engines=result.get("engines", []),
                homepage=result.get("homepage", None),
                img_src=result.get("img_src", ""),
                license_name=result.get("license_name", None),
                license_url=result.get("license_url", None),
                maintainer=result.get("maintainer", ""),
                package_name=result.get("package_name", ""),
                parsed_url=result.get("parsed_url", []),
                popularity=result.get("popularity", 0),
                positions=result.get("positions", []),
                priority=result.get("priority", ""),
                publishedDate=result.get("publishedDate", None),
                score=result.get("score", 0.0),
                source_code_url=result.get("source_code_url", ""),
                tags=result.get("tags", []),
                template=result.get("template", ""),
                thumbnail=result.get("thumbnail", ""),
                title=result.get("title", ""),
                url=result.get("url", "")
            )
            it_list.append(it)
        return it_list

    except Exception as e:
        print(f"Error in it_engine: {type(e).__name__} - {str(e)}")
        traceback.print_exc()
        return []


if __name__ == "__main__":
    it_results = it_engine("openai python sdk")
    for item in it_results[:3]:
        pprint(item)
