from engines4ai.searxng    import SearXNG
from engines4ai.general    import GeneraleData
from engines4ai.images     import ImageData
from engines4ai.videos     import VideoData
from engines4ai.news       import NewsData
from engines4ai.map        import MapData
from engines4ai.it         import ITData
from engines4ai.science    import ScienceData
from engines4ai.wikipedia  import _wikipedia_engine

from dataclasses import fields, dataclass
from pprint import pprint
import traceback
from typing import Union, List, Literal, Optional


# ------------------------------------------------------------------------------------------
# General engine result parser
# ------------------------------------------------------------------------------------------
def parse_result_to_dataclass(json_data: dict, dc: dataclass):
    field_names = {f.name for f in fields(dc)}
    filtered_data = {k: v for k, v in json_data.items() if k in field_names}
    return dc(**filtered_data)

def search_by(query: str, engines: Union[List[str], str], dc: dataclass, page: int = 1, time_range: Optional[Literal["day", "month", "year"]] = None) -> list:
    engine = SearXNG()
    return_data = []

    try:
        results = engine.search(query=query, engines=engines, pageno=page, time_range=time_range)['results']
        
        for json_data in results:
            parsed = parse_result_to_dataclass(json_data, dc)
            return_data.append(parsed)

    except Exception as e:
        print(f"Error in {engines}_engine: {type(e).__name__} - {str(e)}")
        traceback.print_exc()
        return []

    return return_data

# ------------------------------------------------------------------------------------------
# General
# ------------------------------------------------------------------------------------------
def google_engine(query:str, page:int=1, time_range:Optional[Literal["day", "month", "year"]] = None) -> list[GeneraleData]:
    return search_by(query=query, engines=["google"], dc=GeneraleData, page=page, time_range=time_range)

def bing_engine(query:str, page:int=1, time_range:Optional[Literal["day", "month", "year"]] = None) -> list[GeneraleData]:
    return search_by(query=query, engines=["bing"], dc=GeneraleData, page=page, time_range=time_range)

def wikipedia_engine(query:str, page:int=1) -> list[GeneraleData]:
    return _wikipedia_engine(query=query, page=page)


# ------------------------------------------------------------------------------------------
# Reverse image search
# ------------------------------------------------------------------------------------------
def tineye_engine(url:str) -> list[ImageData]:
    return search_by(query=url, engines=["tineye"], dc=ImageData)

# ------------------------------------------------------------------------------------------
# Images
# ------------------------------------------------------------------------------------------
def google_images_engine(query:str, page:int=1, time_range:Optional[Literal["day", "month", "year"]] = None) -> list[ImageData]:
    return search_by(query=query, engines=["google images"], dc=ImageData, page=page, time_range=time_range)

def adobe_stock_engine(query:str, page:int=1) -> list[ImageData]:
    return search_by(query=query, engines=["adobe stock"], dc=ImageData, page=page)

def unsplash_engine(query:str, page:int=1) -> list[ImageData]:
    return search_by(query=query, engines=["unsplash"], dc=ImageData, page=page)


# ------------------------------------------------------------------------------------------
# Videos
# ------------------------------------------------------------------------------------------
def youtube_engine(query:str, page:int=1, time_range:Optional[Literal["day", "month", "year"]] = None) -> list[VideoData]:
    return search_by(query=query, engines=["youtube"], dc=VideoData, page=page, time_range=time_range)


# ------------------------------------------------------------------------------------------
# News
# ------------------------------------------------------------------------------------------
def bing_news_engine(query:str, page:int=1, time_range:Optional[Literal["day", "month", "year"]] = None) -> list[NewsData]:
    return search_by(query=query, engines=["bing news"], dc=NewsData, page=page, time_range=time_range)

def yahoo_news_engine(query:str, page:int=1, time_range:Optional[Literal["day", "month", "year"]] = None) -> list[NewsData]:
    return search_by(query=query, engines=["yahoo news"], dc=NewsData, page=page, time_range=time_range)


# ------------------------------------------------------------------------------------------
# Maps
# ------------------------------------------------------------------------------------------
def apple_maps_engine(query:str, page:int=1) -> list[MapData]:
    return search_by(query=query, engines=["apple maps"], dc=MapData, page=page)


# ------------------------------------------------------------------------------------------
# IT
# ------------------------------------------------------------------------------------------
def stackoverflow_engine(query:str, page:int=1) -> list[ITData]:
    return search_by(query=query, engines=["stackoverflow"], dc=ITData, page=page)

def github_engine(query:str, page:int=1) -> list[ITData]:
    return search_by(query=query, engines=["github"], dc=ITData, page=page)

# ------------------------------------------------------------------------------------------
# Science
# ------------------------------------------------------------------------------------------
def arxiv_engine(query:str, page:int=1) -> list[ScienceData]:
    return search_by(query=query, engines=["arxiv"], dc=ScienceData, page=page)

def google_scholar_engine(query:str, page:int=1, time_range:Optional[Literal["day", "month", "year"]] = None) -> list[ScienceData]:
    return search_by(query=query, engines=["google scholar"], dc=ScienceData, page=page, time_range=time_range)

# Suspended: access denied
def semantic_scholar_engine(query:str, page:int=1) -> list[ScienceData]:
    return search_by(query=query, engines=["semantic scholar"], dc=ScienceData, page=page)


if __name__ == "__main__":
    results = yahoo_news_engine("deepseek")
    pprint(results[:3])