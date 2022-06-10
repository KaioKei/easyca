from pathlib import Path


class CertificateException(Exception):
    pass


class PrivateKeyNotFound(CertificateException):
    def __init__(self, message: str = "Private key not found", *args):
        self.message = message
        super().__init__(self.message, args)


class CertificateNotFound(CertificateException):
    def __init__(self, message: str = "Certificate not found", *args):
        self.message = message
        super().__init__(self.message, args)
