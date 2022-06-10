import os
from typing import Optional

from dotenv import load_dotenv


class EasyCAEnvironment:
    """
    Use this class to :
      - initialize environment in main
      - call this environment to get environment values
    """
    MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
    load_dotenv()

    @staticmethod
    def get_application_name() -> "str":
        return os.getenv("APPLICATION")

    @staticmethod
    def get_version() -> "str":
        return os.getenv("VERSION")

    @staticmethod
    def get_workspace() -> "str":
        return os.getenv("WORKSPACE")

    @classmethod
    def get_resources_dir(cls) -> "str":
        return cls.MODULE_DIR + "/resources"

    @classmethod
    def get_scripts_dir(cls) -> "str":
        return cls.MODULE_DIR + "/scripts"


class EnvironmentLoader:
    """
    Use this class to init/load current environment
    """
    __ENVIRONMENT_INSTANCE: Optional[EasyCAEnvironment] = None

    @staticmethod
    def init_environment():
        EnvironmentLoader.__ENVIRONMENT_INSTANCE = EasyCAEnvironment()

    @staticmethod
    def get_environment() -> "EasyCAEnvironment":
        """
        Use this method to get the initiated environment from any module in this code application
        """
        return EnvironmentLoader.__ENVIRONMENT_INSTANCE
