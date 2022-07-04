import logging
from pathlib import Path

import typer

from easyca.exceptions.ca_exceptions import CANotFound
from easyca.exceptions.certificate_exception import CertificateExists
from easyca.logger import EasyCALogger
from easyca.services.ca_manager import CAManager

app = typer.Typer(help="Create CAs and certificates")

logger: logging.Logger = logging.getLogger(EasyCALogger.name)


def log_debug(verbose: bool):
    """
    Logger callback for more verbosity
    """
    if verbose:
        logger.setLevel(logging.DEBUG)


@app.command()
def ca(name: str = typer.Option(None, "-n", "--name", help="Name of the CA to create"),
       verbose: bool = typer.Option(False, "-v", help="More verbosity for debug",
                                    callback=log_debug)):
    """
    Create a new root CA and a signing CA to generate certificates
    """
    ca_name = name if name else CAManager.get_current()
    manager = CAManager(ca_name)
    manager.generate_root_ca()
    manager.generate_intermediate_ca()
    manager.set_current(ca_name)
    logger.info("OK")


@app.command()
def certs(configuration: Path = typer.Option(None, "-c", "--config",
                                             exists=True,
                                             file_okay=True,
                                             readable=True,
                                             resolve_path=True,
                                             help="Configuration file path"),
          verbose: bool = typer.Option(False, "-v", help="More verbosity for debug",
                                       callback=log_debug)):
    """
    Create certificates\n
    Use the current CA and create certificates according to the provided configuration file.\n
    Provide no configuration for default certificates.
    """
    current_ca = CAManager.get_current()
    manager = CAManager(current_ca)
    # create CA if not exist
    try:
        manager.check_ca()
    except CANotFound:
        logger.info(f"Create CA {current_ca}")
        ca(current_ca)
    # create certs
    logger.info(f"Create certificates")
    manager.generate_certificates(configuration, debug=verbose)
    logger.info("OK")
