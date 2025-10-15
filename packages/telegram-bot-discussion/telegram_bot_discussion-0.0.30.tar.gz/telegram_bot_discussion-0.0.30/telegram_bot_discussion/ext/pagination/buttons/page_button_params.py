from typing import Any


from ....button.params import Params


class PageButtonParams(Params):
    query: Any
    page: int

    def __init__(
        self,
        action: str,
        query: Any,
        page: int,
    ):
        self.action = action
        self.query = query
        self.page = page
