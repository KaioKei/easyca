from pathlib import Path


class CAException(Exception):
    pass


class CANotFound(CAException):
    def __init__(self, message: str = "CA does not exists", *args):
        self.message = message
        super().__init__(self.message, args)


class RootCANotFound(CAException):
    def __init__(self, message: str = "Root CA does not exists", *args):
        self.message = message
        super().__init__(self.message, args)


class SigningCANotFound(CAException):
    def __init__(self, message: str = "Signing CA does not exists", *args):
        self.message = message
        super().__init__(self.message, args)
