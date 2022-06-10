import logging

import typer

from easyca.logger import EasyCALogger
from easyca.workspace import WorkspaceLoader

app = typer.Typer(help="Create CAs and certificates")

logger: logging.Logger = logging.getLogger(EasyCALogger.name)


@app.command()
def ca(name: str = typer.Option(..., "-n", "--name", help="Set the CA to use for certificate "
                                                          "creation.")):
    """
    Set the CA to use to create certificates
    """
    logger.info(f"Set CA to '{name}'")
    workspace = WorkspaceLoader.get_workspace()
    workspace.set_metadata({"current": name})
