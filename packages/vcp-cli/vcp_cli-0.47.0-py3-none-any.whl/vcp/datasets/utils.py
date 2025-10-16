from typing import List

from vcp.datasets.api import Location, SearchResponse


# extract locations from the API search result
def extract_locations(sr: SearchResponse) -> List[Location]:
    result: List[Location] = []
    for ds in sr.data:
        result.extend(ds.locations)
    return result
