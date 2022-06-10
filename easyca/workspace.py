import os
from pathlib import Path
from typing import Dict, Optional

from easyca.environment import EasyCAEnvironment
from easyca.utils.file_utils import read_json, write_json


class EasyCAWorkspace:

    @staticmethod
    def get_path() -> "Path":
        return Path(EasyCAEnvironment.get_workspace())

    @staticmethod
    def get_metadata_path() -> "Path":
        return EasyCAWorkspace.get_path() / ".metadata"

    @staticmethod
    def get_metadata() -> "Dict":
        return read_json(EasyCAWorkspace.get_metadata_path())

    @staticmethod
    def set_metadata(content: Dict):
        write_json(EasyCAWorkspace.get_metadata_path(), content)


class WorkspaceLoader:
    """
    Use this class to init/load current environment
    """
    __WORKSPACE_INSTANCE: Optional[EasyCAWorkspace] = None

    @staticmethod
    def init_workspace():
        WorkspaceLoader.__WORKSPACE_INSTANCE = EasyCAWorkspace()
        if not WorkspaceLoader.__WORKSPACE_INSTANCE.get_path().exists():
            os.makedirs(WorkspaceLoader.__WORKSPACE_INSTANCE.get_path())
        if not WorkspaceLoader.__WORKSPACE_INSTANCE.get_metadata_path().exists():
            write_json(WorkspaceLoader.__WORKSPACE_INSTANCE.get_metadata_path(), {})

    @staticmethod
    def get_workspace() -> "EasyCAWorkspace":
        """
        Use this method to get the initiated environment from any module in this code application
        """
        return WorkspaceLoader.__WORKSPACE_INSTANCE
