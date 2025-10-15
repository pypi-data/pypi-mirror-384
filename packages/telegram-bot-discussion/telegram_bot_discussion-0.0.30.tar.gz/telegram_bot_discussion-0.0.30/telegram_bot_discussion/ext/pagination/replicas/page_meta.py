from typing import Type


from ....dialogue.replicas import ReplicaMeta
from ..buttons.item_button import ItemButton
from ..dao import Item


class PageReplicaMeta(ReplicaMeta):
    item_class: Type[Item] = Item
    item_button_class: Type[ItemButton] = ItemButton
