import logging
from pathlib import Path
from typing import List

import typer

from easyca.cli.commands import delete_cmd, export_cmd, list_cmd, create_cmd, set_cmd
from easyca.environment import EnvironmentLoader
from easyca.logger import EasyCALogger
from easyca.services.ca_manager import CAManager

app = typer.Typer(help=f"Manage CA and certificates",
                  no_args_is_help=True)
app.add_typer(create_cmd.app, name="create")
app.add_typer(list_cmd.app, name="list")
app.add_typer(delete_cmd.app, name="delete")
app.add_typer(set_cmd.app, name="set")
app.add_typer(export_cmd.app, name="export")

logger: logging.Logger = logging.getLogger(EasyCALogger.name)


def log_debug(verbose: bool):
    """
    Logger callback for more verbosity
    """
    if verbose:
        logger.setLevel(logging.DEBUG)


@app.callback(invoke_without_command=True)
def main_callback(
        version: bool = typer.Option(False, "--version",
                                     help="Print version",
                                     is_eager=True)):
    env = EnvironmentLoader.get_environment()
    if version:
        typer.echo(f"{env.get_application_name()} v{env.get_version()}")
        # raise exit to avoid further mandatory options
        raise typer.Exit()


@app.command()
def export(ca: str = typer.Option(None, "--ca", help="Name of a CA to export its "
                                                     "certificates"),
           output: Path = typer.Option(..., "-o", "--output", resolve_path=True,
                                       help="Output directory"),
           names: List[str] = typer.Option(None, "-n", "--names", help="Certificates names to "
                                                                       "export. If not provided, "
                                                                       "export all.")):
    """
    Export certificates to an output location
    """
    ca_name = ca if ca else CAManager.get_current()
    logger.info(f"Export '{ca_name}' certificates in {output}")
    CAManager(ca_name).export_certs(output)
    logger.info("OK")


# @app.command()
# def check(ca: str = typer.Option(None, "--ca", help="Name of a CA to export its "
#                                                      "certificates")):
#     """
#     Export certificates to an output location
#     """
#     ca_name = ca if ca else CAManager.get_current()
#     CAManager(ca_name).check_ca()


def cli():
    app()
