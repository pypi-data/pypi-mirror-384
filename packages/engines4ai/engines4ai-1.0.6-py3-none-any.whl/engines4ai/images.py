from engines4ai.searxng import SearXNG

from dataclasses import dataclass, field
from typing import List


@dataclass
class ImageData:
    category: str = ''
    content: str = ''
    engine: str = ''
    engines: List[str] = field(default_factory=list)
    img_src: str = ''
    parsed_url: List[str] = field(default_factory=list)
    positions: List[int] = field(default_factory=list)
    priority: str = ''
    resolution: str = ''
    score: float = 0.0
    source: str = ''
    template: str = ''
    thumbnail: str = ''
    thumbnail_src: str = ''
    title: str = ''
    url: str = ''


def image_engine(query: str, 
                 pageno: int = 1,
                 engines: list[str]=[]) -> List[ImageData]:
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
            search_params["categories"] = ["images"]
            
        results = engine.search(**search_params)['results']
        images = []
        
        for result in results:
            data = ImageData(
                category=result.get("category", ""),
                content=result.get("content", ""),
                engine=result.get("engine", ""),
                engines=result.get("engines", []),
                img_src=result.get("img_src", ""),
                parsed_url=result.get("parsed_url", []),
                positions=result.get("positions", []),
                priority=result.get("priority", ""),
                resolution=result.get("resolution", ""),
                score=result.get("score", 0.0),
                source=result.get("source", ""),
                template=result.get("template", ""),
                thumbnail=result.get("thumbnail", ""),
                thumbnail_src=result.get("thumbnail_src", ""),
                title=result.get("title", ""),
                url=result.get("url", "")
            )
            images.append(data)

        return images

    except Exception as e:
        print(f"Error in image_engine: {type(e).__name__} - {str(e)}")
        raise


if __name__ == "__main__":
    from pprint import pprint
    results = image_engine("banff national park")
    pprint(results[:2])
