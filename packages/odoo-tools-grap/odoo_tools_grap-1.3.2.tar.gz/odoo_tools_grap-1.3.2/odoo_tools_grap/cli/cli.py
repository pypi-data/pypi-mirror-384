import logging
import sys

import click
from click_loglevel import LogLevel
from loguru import logger

import odoo_tools_grap
from odoo_tools_grap.cli.cli_create_branch import create_branch
from odoo_tools_grap.cli.cli_diff import diff
from odoo_tools_grap.cli.cli_generate import generate
from odoo_tools_grap.cli.cli_migrate import migrate


@click.group()
@click.version_option(odoo_tools_grap.__version__, "-v", "--version")
@click.option("-l", "--log-level", type=LogLevel(), default=logging.INFO)
@click.pass_context
def main(ctx, log_level):
    """
    Provides a command set to perform odoo environment manipulations.
    """
    logger.remove()
    logger.add(sys.stderr, level=log_level)


main.add_command(create_branch)
main.add_command(diff)
main.add_command(generate)
main.add_command(migrate)
