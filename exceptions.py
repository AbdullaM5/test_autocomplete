class BaseServerException(Exception):
    def __init__(self, message):
        self.message: str = message


class CommandParseError(BaseServerException):
    pass


class SuggestionsNotFoundError(BaseServerException):
    pass
