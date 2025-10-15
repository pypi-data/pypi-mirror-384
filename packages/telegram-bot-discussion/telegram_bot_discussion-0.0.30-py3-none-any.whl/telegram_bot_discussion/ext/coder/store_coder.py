from abc import ABC, abstractmethod
from hashlib import md5
from typing import Any, List, Tuple


from ...button.coder_interface import CoderInterface


class KeyValueStorageInterface(ABC):
    """KeyValueStorageInterface is interface for external storage where custom values of `Params` are stored."""

    @staticmethod
    @abstractmethod
    def autogenerate_primary_key(): ...

    @abstractmethod
    def get(self, key: str) -> Any: ...

    @abstractmethod
    def add(self, value: Any) -> str: ...


class StoreCoder(CoderInterface):
    """`StoreCoder` serialize data and save its value in external storage with unique primary key.
    Primary key store at `Button`. For deserialize data was get from external storage by primary key.

    So there are no any limits for callback query data (long strings, complex multi params, redundant big json and etc.).
    """

    db: KeyValueStorageInterface
    """ KeyValueStorageInterface: external storage where custom values of `Params` are stored."""
    secret: str
    """ str: Secret string is used for make digital signature of data."""

    def __init__(self, secret: str, db: KeyValueStorageInterface):
        self.secret = secret
        self.db = db

    def serialize(self, *args: Any) -> str:
        return self.db.add(args)

    def deserialize(self, data: str) -> List[Any]:
        return self.db.get(data)

    def get_signature(self, chat_id: int, serialized_data: str, sender_id: int) -> str:
        return md5(
            f"{serialized_data}{self.secret}{chat_id}{sender_id}".encode()
        ).hexdigest()

    def sign(self, signature: str, serialized_data: str) -> str:
        return f"{signature}{serialized_data}"

    def extract_signature_and_serialized_data(
        self, signed_serialized_data: str
    ) -> Tuple[str, str]:
        signature = signed_serialized_data[:32]
        serialized_data = signed_serialized_data[32:]
        return signature, serialized_data

    def extract_signature_and_deserialized_data(
        self, signed_serialized_data: str
    ) -> Tuple[str, List[Any]]:
        signature, serialized_data = self.extract_signature_and_serialized_data(
            signed_serialized_data
        )
        deserialized_data = self.deserialize(serialized_data)
        return signature, deserialized_data
