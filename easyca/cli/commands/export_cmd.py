import logging
import os
import shutil
from pathlib import Path
from typing import List

import typer

from easyca.logger import EasyCALogger
from easyca.services.ca_manager import CAManager
from easyca.utils.file_utils import list_dirs
from easyca.workspace import WorkspaceLoader

app = typer.Typer(help="Export certificates")

logger: logging.Logger = logging.getLogger(EasyCALogger.name)


@app.command()
def certs(output: Path = typer.Option(..., "-o", "--output", resolve_path=True,
                                                             help="Output directory"),
          ca_name: str = typer.Option(None, "--ca", help="The CA name of the certificates to "
                                                         "export"),
          names: List[str] = typer.Option(None, "-n", "--names", help="Certificates names to "
                                                                      "export. If not provided, "
                                                                      "export all.")):
    """
    Destroy one or more CAs based on names, or all
    """
    current_ca_name = ca_name if ca_name else CAManager.get_current()
    logger.info(f"Export '{current_ca_name}' certificates in {output}")
    CAManager(current_ca_name).export_certs(output)
    logger.info("OK")
