from ....button.params import Params


class ItemButtonParams(Params):
    item_id: int

    def __init__(
        self,
        action: str,
        item_id: int,
    ):
        self.action = action
        self.item_id = item_id
