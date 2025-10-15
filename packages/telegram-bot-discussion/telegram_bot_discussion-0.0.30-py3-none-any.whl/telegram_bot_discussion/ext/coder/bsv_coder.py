from hashlib import md5
from typing import Any, List, Tuple, Union


from ...button.coder_interface import CoderInterface


ThisTypesOnly = Union[int, str, None]


class InvalidType(Exception):
    var: Any

    def __init__(self, var: Any) -> None:
        self.var = var

    def __str__(self) -> str:
        return f"Invalid type of variable {self.var}"


class NoneIsNotNone(Exception):
    data: Any

    def __init__(self, data: Any) -> None:
        self.data = data

    def __str__(self) -> str:
        return f"None value has some data {self.data} (len: {len(self.data)})"


class IntIsNone(Exception):

    def __init__(self) -> None: ...

    def __str__(self) -> str:
        return f"Int is None"


class InvalidTypePrefix(Exception):
    prefix: Any

    def __init__(self, prefix: Any) -> None:
        self.prefix = prefix

    def __str__(self) -> str:
        return f"Invalid type prefix {self.prefix}"


class BSV_Coder(CoderInterface):
    """`Bytes Separated Values Coder` serialize data with type-special byte-delimiter:

    - \\x00 - `None` prefix;
    - \\x01 - `int` prefix;
    - \\x02 - `str` prefix.

    Remember about native Telegram callback query data length limit.

    Data deserialization relies on the preceding type-special byte-delimiter.
    """

    secret: str
    """ str: Secret string is used for make digital signature of data."""

    _SIGNATURE_SUFFIX = "\x13"

    _NUL_PREFIX = "\x00"
    _INT_PREFIX = "\x01"
    _STR_PREFIX = "\x02"

    def __init__(self, secret: str):
        self.secret = secret

    def serialize(self, *args: ThisTypesOnly) -> str:
        result: str = ""
        for arg in args:
            if arg is None:
                result += self.__class__._NUL_PREFIX
            elif isinstance(arg, int):
                result += self.__class__._INT_PREFIX + str(arg)
            elif isinstance(arg, str):
                result += self.__class__._STR_PREFIX + arg
            else:
                raise InvalidType(arg)
        return result

    def deserialize(self, data: str) -> List[ThisTypesOnly]:
        if data[0] not in (
            self.__class__._INT_PREFIX,
            self.__class__._STR_PREFIX,
            self.__class__._NUL_PREFIX,
        ):
            raise InvalidTypePrefix(data[0])

        result: List[ThisTypesOnly] = []
        part = data
        while True:
            data_marker = part[0]

            body_before_next_int_candidate = part[1:].split(
                self.__class__._INT_PREFIX, 1
            )[0]
            body_before_next_int_candidate_len = len(body_before_next_int_candidate)

            body_before_next_str_candidate = part[1:].split(
                self.__class__._STR_PREFIX, 1
            )[0]
            body_before_next_str_candidate_len = len(body_before_next_str_candidate)

            body_before_next_nul_candidate = part[1:].split(
                self.__class__._NUL_PREFIX, 1
            )[0]
            body_before_next_nul_candidate_len = len(body_before_next_nul_candidate)

            body_before_next_len = min(
                body_before_next_int_candidate_len,
                body_before_next_str_candidate_len,
                body_before_next_nul_candidate_len,
            )
            data_body = part[1 : 1 + body_before_next_len]
            if data_marker == self.__class__._INT_PREFIX:
                if body_before_next_len == 0:
                    raise IntIsNone()
                else:
                    result.append(int(data_body))
            elif data_marker == self.__class__._STR_PREFIX:
                result.append(data_body)
            elif data_marker == self.__class__._NUL_PREFIX:
                if body_before_next_len > 0:
                    raise NoneIsNotNone(data_body)
                else:
                    result.append(None)
            else:
                raise InvalidTypePrefix(data_marker.encode())
            part = part[1 + body_before_next_len :]
            if len(part) == 0:
                break

        return result

    def get_signature(self, chat_id: int, serialized_data: str, sender_id: int) -> str:
        return md5(
            f"{serialized_data}{self.secret}{chat_id}{sender_id}".encode()
        ).hexdigest()[:10]

    def sign(self, signature: str, serialized_data: str) -> str:
        return self.__class__._SIGNATURE_SUFFIX.join([signature, serialized_data])

    def extract_signature_and_serialized_data(
        self, signed_serialized_data: str
    ) -> Tuple[str, str]:
        sign, serialized_data = signed_serialized_data.split(
            self.__class__._SIGNATURE_SUFFIX, 1
        )
        return sign, serialized_data

    def extract_signature_and_deserialized_data(
        self, signed_serialized_data: str
    ) -> Tuple[str, List[ThisTypesOnly]]:
        sign, serialized_data = self.extract_signature_and_serialized_data(
            signed_serialized_data
        )
        deserialized_data = self.deserialize(serialized_data)
        return sign, deserialized_data
