from abc import ABC, abstractmethod
from typing import Any, List, Tuple, Union


class CoderInterface(ABC):
    """`CoderInterface` is interface for class, which serialize `Button`-`Params` values for storing them at `Button` and deserialize data from callback query to special `Button`-`Params` structure.

    In the box `Telegram-Bot-Discussion` contains two realizations of `CoderInterface`:

    - store callback query data within `Button` as callback action `Params` (with limited by native Telegram protocol data length <page> and variables types - int, string, because no need more for more tasks).

    - store unique identity of callback action `Params`, which are loaded when user click `Button` (no any limits of callback data length and variables types, but external storage must work independently).

    You can write self `Coder`-class based on `Pickle`, `ProtoBuf`, `FlatBuffers` and etc. I stopped on the byte-separated values format as more visual and clear.
    """

    _instance = None

    def check_signature(
        self,
        chat_id: int,
        signed_serialized_data: str,
        sender_id: Union[int, None] = None,
    ) -> bool:
        if sender_id is None:
            sender_id = chat_id
        signature, serialized_data = self.extract_signature_and_serialized_data(
            signed_serialized_data
        )
        if self.get_signature(chat_id, serialized_data, sender_id) == signature:
            return True
        return False

    @abstractmethod
    def deserialize(self, data: str) -> List[Any]: ...

    @abstractmethod
    def extract_signature_and_deserialized_data(
        self, signed_serialized_data: str
    ) -> Tuple[str, List[Any]]: ...

    @abstractmethod
    def extract_signature_and_serialized_data(
        self, signed_serialized_data: str
    ) -> Tuple[str, str]: ...

    @abstractmethod
    def get_signature(
        self, chat_id: int, serialized_data: str, sender_id: int
    ) -> str: ...

    @abstractmethod
    def serialize(self, *args: Any) -> str: ...

    @abstractmethod
    def sign(self, signature: str, serialized_data: str) -> str: ...

    def fetch_deserialized_data(self, signed_serialized_data: str) -> List[Any]:
        return self.extract_signature_and_deserialized_data(signed_serialized_data)[1]

    def fetch_serialized_data(self, signed_serialized_data: str) -> str:
        return self.extract_signature_and_serialized_data(signed_serialized_data)[1]

    def fetch_signature(self, signed_serialized_data: str) -> str:
        return self.extract_signature_and_deserialized_data(signed_serialized_data)[0]

    @classmethod
    def instance(cls, *args, **kwargs):
        if cls._instance == None:
            cls._instance = cls(*args, **kwargs)
        return cls._instance
