from .output_enum import OutputEnum
from .icon_enum import IconEnum
from typing import Optional

class Params:
    class Location:
        def __init__(self, search_name: str = None, id: str = None):
            self._search_name = search_name
            self._id = id

        @property
        def search_name(self) -> str | None:
            return self._search_name
        
        @property
        def id(self) -> str | None:
            return self._id

        def __str__(self):
            return f"Location(search_name={self.search_name}, id={self.id})"
        
    def __init__(
            self,
            location: Optional["Params.Location"] = None,
            language: str = "en-US",
            output_format: OutputEnum = OutputEnum.CONSOLE,
            keep_open: bool = False,
            icons: IconEnum = IconEnum.EMOJI
        ):
        self._location = location
        self._language = language
        self._output_format = output_format
        self._keep_open = keep_open
        self._icons = icons

    @property
    def location(self) -> Optional["Params.Location"]:
        return self._location
    
    @property
    def language(self) -> str:
        return self._language
    
    @property
    def output_format(self) -> OutputEnum:
        return self._output_format
    
    @property
    def keep_open(self) -> bool:
        return self._keep_open
    
    @property
    def icons(self) -> IconEnum:
        return self._icons
    
    def __str__(self):
        return f"Params(location={self.location}, language={self.language}, output_format={self.output_format}, keep_open={self.keep_open}, icons={self.icons})"
    