from easyssl.common.utils.platform_utils import Filetype


class Material:
    file_type: Filetype
    parent_dir: str

    def __init__(self, file_type: Filetype, parent_dir: str):
        self.file_type = file_type
        self.parent_dir = parent_dir


class MaterialFactory(Material):

    @staticmethod
    def get_private_key_material():
        return Material(Filetype.P8, "private")

    @staticmethod
    def get_keystore_material():
        return Material(Filetype.JKS, "private")

    @staticmethod
    def get_certificate_material():
        return Material(Filetype.CRT, "certs")