from engines4ai.searxng import SearXNG

from typing import List
from dataclasses import dataclass, field
import traceback
from pprint import pprint


@dataclass
class VideoData:
    author: str = ''
    category: str = ''
    content: str = ''
    engine: str = ''
    engines: List[str] = field(default_factory=list)
    iframe_src: str = ''
    img_src: str = ''
    length: str = ''
    parsed_url: List[str] = field(default_factory=list)
    positions: List[int] = field(default_factory=list)
    priority: str = ''
    score: float = 0.0
    template: str = ''
    thumbnail: str = ''
    title: str = ''
    url: str = ''


def video_engine(query: str, pageno: int = 1, engines: list[str]=[]) -> List[VideoData]:
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
            search_params["categories"] = ["videos"]
            
        results = engine.search(**search_params)['results']
        videos = []
        for result in results:
            data = VideoData(
                author=result.get("author", ""),
                category=result.get("category", ""),
                content=result.get("content", ""),
                engine=result.get("engine", ""),
                engines=result.get("engines", []),
                iframe_src=result.get("iframe_src", ""),
                img_src=result.get("img_src", ""),
                length=result.get("length", ""),
                parsed_url=result.get("parsed_url", []),
                positions=result.get("positions", []),
                priority=result.get("priority", ""),
                score=result.get("score", 0.0),
                template=result.get("template", ""),
                thumbnail=result.get("thumbnail", ""),
                title=result.get("title", ""),
                url=result.get("url", "")
            )
            videos.append(data)
        return videos

    except Exception as e:
        print(f"Error in video_engine: {type(e).__name__} - {str(e)}")
        traceback.print_exc()
        return []

if __name__ == "__main__":
    results = video_engine("ChatGPT")
    for video in results[:3]:
        pprint(video)
