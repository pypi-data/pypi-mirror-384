class Config:
    """`Config` is base class of Telegram-bot configuration."""

    token: str
    """str: It seems that Telegram-bot token field is absolutely needed for any config."""

    def __init__(
        self,
        token: str,
    ):
        self.token = token
