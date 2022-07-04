import logging
import sys
from typing import Dict, List

import typer

from easyca.logger import EasyCALogger
from easyca.services.ca_manager import CAManager
from easyca.utils.subprocess_utils import yes_no_question

app = typer.Typer(help="Delete CAs and certificates")

logger: logging.Logger = logging.getLogger(EasyCALogger.name)


@app.command()
def ca(names: List[str] = typer.Option(None, "-n", "--names", help="CA names to delete"),
       del_all: bool = typer.Option(False, "-a", "--all", help="Delete all CAs")):
    """
    Destroy CAs and all certificates attached to it
    """
    if del_all:
        names = [str(path) for path in CAManager.list_cas()]
    logger.warning(f"The following CA will be removed: {names}")
    if yes_no_question("Are you sure ? (Y/n)[default: n]", False):
        CAManager.delete_cas(names)
        logger.info("OK")
    else:
        logger.info("Aborted")


@app.command()
def certs(ca_: str = typer.Option(None, "--ca", help="The CA name of the certificates to delete"),
          names: List[str] = typer.Option(None, "-n", "--names", help="Certificates names to delete"),
          del_all: bool = typer.Option(False, "-a", "--all", help="Delete all CAs")):
    """
    Destroy certificates
    """
    ca_name = ca_ if ca_ else CAManager.get_current()
    if del_all:
        names: List[str] = [str(path) for path in CAManager(ca_name).list_certs().keys()]
    elif not names:
        logger.error("You must provide '--names' or '--all'")
        raise typer.Exit()

    logger.warning(f"The following certs will be removed: {names}")
    if yes_no_question("Are you sure ? (Y/n)[default: n]", False):
        CAManager.delete_certs(ca_name, names)
        logger.info("OK")
    else:
        logger.info("Aborted")
