from engines4ai.searxng import SearXNG
from engines4ai.general import GeneraleData

from typing import List


def _wikipedia_engine(query: str, page: int = 1) -> List[GeneraleData]:
    engine = SearXNG()

    try:
        results = engine.search(query=query, engines=["wikipedia"], pageno=page)['infoboxes']
        wikipedia_results = []
        for result in results:
            data = GeneraleData(
                category=result.get("category", ""),
                content=result.get("content", ""),
                engine=result.get("engine", ""),
                engines=result.get("engines", []),
                img_src=result.get("img_src", ""),
                parsed_url=result.get("parsed_url", []),
                positions=result.get("positions", ""),
                priority=result.get("priority", ""),
                score=result.get("score", 0.0),
                template=result.get("template", ""),
                thumbnail=result.get("thumbnail", ""),
                title=result.get("title", ""),
                url=result.get("urls", "")[0].get("url", ""),
            )
            
            wikipedia_results.append(data)
        return wikipedia_results

    except Exception as e:
        print(f"Error in wikipedia_engine: {type(e).__name__} - {str(e)}")
        raise
