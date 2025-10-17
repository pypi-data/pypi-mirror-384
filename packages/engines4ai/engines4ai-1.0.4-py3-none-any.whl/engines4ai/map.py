from engines4ai.searxng import SearXNG

from dataclasses import dataclass, field
from typing import List, Optional
from pprint import pprint


@dataclass
class MapData:
    title: str = ''
    latitude: float = 0.0
    longitude: float = 0.0
    url: str = ''
    engine: str = ''
    engines: List[str] = field(default_factory=list)
    score: float = 0.0
    geojson: dict = field(default_factory=dict)
    boundingbox: List[float] = field(default_factory=list)
    osm_id: Optional[int] = None
    osm_type: Optional[str] = None
    parsed_url: List[str] = field(default_factory=list)
    positions: List[int] = field(default_factory=list)
    category: str = ''
    template: str = ''
    

def map_engine(query: str, pageno: int = 1, engines: list[str]=[]) -> List[MapData]:
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
            search_params["categories"] = ["map"]
            
        results = engine.search(**search_params)["results"]
        maps = []

        for result in results:
            data = MapData(
                title=result.get("title", ""),
                latitude=result.get("latitude", 0.0),
                longitude=result.get("longitude", 0.0),
                url=result.get("url", ""),
                engine=result.get("engine", ""),
                engines=result.get("engines", []),
                score=result.get("score", 0.0),
                geojson=result.get("geojson", {}),
                boundingbox=result.get("boundingbox", []),
                osm_id=result.get("osm", {}).get("id"),
                osm_type=result.get("osm", {}).get("type"),
                parsed_url=result.get("parsed_url", []),
                positions=result.get("positions", []),
                category=result.get("category", ""),
                template=result.get("template", "")
            )
            maps.append(data)

        return maps

    except Exception as e:
        print(f"Error in map_engine: {type(e).__name__} - {str(e)}")
        raise


if __name__ == "__main__":
    results = map_engine("Restaurant in tokyo")
    pprint(results)

