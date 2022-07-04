import logging
from typing import Dict

import typer

from easyca.logger import EasyCALogger
from easyca.services.ca_manager import CAManager

app = typer.Typer(help="List CAs and certificates")

logger: logging.Logger = logging.getLogger(EasyCALogger.name)


@app.command()
def ca():
    """
    List the CAs, the '*' refers to the current CA
    """
    ca_list = CAManager.list_cas()
    ca_current = CAManager.get_current()
    result = list(map(lambda x: str(x).replace(ca_current, f"* {ca_current}"), ca_list))
    logger.info("CA list:\n" + str.join("\n", result))


@app.command()
def certs(name: str = typer.Option(None, "--ca", help="Name of a CA to list its certificates")):
    """
    List the certificates of the current CA
    """
    ca_name = name if name else CAManager.get_current()
    logger.info(f"CA '{ca_name}' certs:")
    try:
        ca_certs: Dict = CAManager(ca_name).list_certs_names(exclude_ca=True)
        print(f"ca={ca_name}")
        for cn, certs_names in ca_certs.items():
            print(f"└── cn={cn}")
            for cert_name in certs_names:
                print(f"   ├──{cert_name}")
    except FileNotFoundError:
        pass
