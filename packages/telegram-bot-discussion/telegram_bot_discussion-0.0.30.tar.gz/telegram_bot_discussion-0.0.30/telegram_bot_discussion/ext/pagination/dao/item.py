from abc import ABC, abstractmethod
from typing import Any, List


class Item(ABC):

    @abstractmethod
    def get_id(self, *args, **kwargs):
        raise Exception("Must realize `get_id()`")

    @abstractmethod
    def item(self, *args, **kwargs) -> str:
        raise Exception("Must realize `item()`")

    @classmethod
    @abstractmethod
    def page(cls, query: Any, page: int, *args, **kwargs) -> List["Item"]:
        raise Exception("Must realize `page()`")

    @classmethod
    @abstractmethod
    def is_page_exist(cls, query: Any, page: int, *args, **kwargs) -> bool:
        raise Exception("Must realize `is_page_exist()`")
