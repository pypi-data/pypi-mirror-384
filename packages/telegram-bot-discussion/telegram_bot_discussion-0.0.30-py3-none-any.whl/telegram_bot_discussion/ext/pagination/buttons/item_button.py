from telegram import Update
from telegram.ext import CallbackContext


from ....button import Button
from ..dao import Item
from .item_button_meta import ItemButtonMeta
from .item_button_params import ItemButtonParams


class ItemButton(Button):

    class Meta(ItemButtonMeta): ...

    item: Item
    params: ItemButtonParams

    def __init__(
        self,
        chat_id: int,
        item: Item,
    ):
        self.item = item
        self.params = ItemButtonParams(
            action=self.action(),
            item_id=self.item.get_id(),
        )
        super().__init__(chat_id)

    @classmethod
    async def on_click(
        cls,
        _: Update,
        __: CallbackContext,
    ): ...
