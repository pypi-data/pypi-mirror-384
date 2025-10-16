from weathergrabber.domain.search import Search

def search_to_dict(search: Search) -> dict:
    return {
        "id": search.id,
        "search_name": search.search_name,
    }
