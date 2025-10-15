from typing import Type


from ....button import ButtonMeta
from ..replicas.page import PageReplica


class PageButtonMeta(ButtonMeta):
    action: str = "page"
    page_replica: Type[PageReplica] = PageReplica
