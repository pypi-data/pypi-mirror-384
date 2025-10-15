
class NeedRetryException(Exception):
    def __init__(self, *args: object, message, timeout) -> None:
        super().__init__(*args)
        self.timeout = timeout
        self.message = message
