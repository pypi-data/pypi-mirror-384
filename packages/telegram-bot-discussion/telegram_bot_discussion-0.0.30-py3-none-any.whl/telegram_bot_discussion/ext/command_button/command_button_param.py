from ...button.params import Params


class CommandButtonParams(Params):
    command_name: str

    def __new__(cls, **kwargs):
        return super().__new__(cls, "command")

    def __init__(
        self,
        command_name: str,
        *args,
        **kwargs,
    ):
        self.command_name = command_name
