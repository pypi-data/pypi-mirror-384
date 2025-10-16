class Search:
    def __init__(self, id: str, search_name: str | None = None):
        self._id = id
        self._search_name = search_name

    @property
    def id(self) -> str:
        return self._id

    @property
    def search_name(self) -> str:
        return self._search_name

    def __repr__(self):
        return f"Search(id={self.id!r}, search_name={self.search_name!r})"
