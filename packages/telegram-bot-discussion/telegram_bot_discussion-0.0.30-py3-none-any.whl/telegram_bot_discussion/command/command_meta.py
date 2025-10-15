ACTION: str = "action"
TITLE: str = "title"


class CommandMeta:
    """`CommandMeta` is special meta class for autogenerate  properties values for object of `Command` class."""

    action: str
    """ str: Unique action name for handling its reaction route in CommandHandler."""
    title: str
    """ str: Text can be used in button as title. In more tasks it is no needed."""
