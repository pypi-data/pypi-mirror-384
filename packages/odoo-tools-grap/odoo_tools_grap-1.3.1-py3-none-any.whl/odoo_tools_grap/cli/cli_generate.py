import configparser
from pathlib import Path

import click
import yaml
from loguru import logger

from odoo_tools_grap.cli.click_options import option_repo_config_file


@click.command()
@click.option(
    "-i",
    "--input-files",
    multiple=True,
    type=click.Path(
        exists=True,
        dir_okay=False,
        resolve_path=True,
    ),
    help="Template odoo Config File(s)",
)
@click.option(
    "-o",
    "--output-file",
    type=click.Path(
        dir_okay=False,
        resolve_path=True,
    ),
    default="./odoo.cfg",
    help="Generated Odoo config file",
)
@option_repo_config_file
@click.pass_context
def generate(ctx, input_files, output_file, config_repo_file):
    """Generate a odoo.cfg file, based on:
    - one or more 'config.cfg ;
    - one repos.yml file, to generate addons_path.
    """
    input_files = [Path(x) for x in input_files]
    output_file = Path(output_file)
    config_repo_file = Path(config_repo_file)

    # Read Input Files
    parser = configparser.ConfigParser()
    parser.read(input_files)

    # Compute Addons path
    stream = open(config_repo_file, "r")
    data = yaml.safe_load(stream)

    addons_path = []
    for key in data.keys():
        path = config_repo_file.cwd() / key
        if path.name == "odoo":
            # Add two addons path
            addons_path.append(str(path / "addons"))
            addons_path.append(str(path / "odoo"))
        else:
            addons_path.append(str(path))

    parser.set("options", "addons_path", ",".join(addons_path))

    parser.write(open(output_file, "w"))
    logger.info("%s has been generated or updated." % (output_file))
