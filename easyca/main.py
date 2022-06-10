import logging

from easyca.cli.cli import cli
from easyca.environment import EnvironmentLoader
from easyca.logger import EasyCALogger
from easyca.workspace import WorkspaceLoader

logger: logging.Logger = logging.getLogger(EasyCALogger.name)


def main():
    # init
    EasyCALogger()
    EnvironmentLoader.init_environment()
    WorkspaceLoader.init_workspace()
    cli()


# debug
if __name__ == "__main__":
    main()
