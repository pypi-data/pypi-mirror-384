import subprocess
from pathlib import Path

import click
from loguru import logger

from .tools import (
    ensure_line,
    git_checkout,
    git_commit_all,
    git_push,
    replace_expression,
)


@click.command()
@click.option(
    "-i",
    "--initial-version",
    type=str,
    required=True,
    help="origin version, which contains the answer copy file.",
    default="12.0",
)
@click.option(
    "-t",
    "--target-version",
    type=str,
    required=True,
    help="target version to create.",
    default="16.0",
)
@click.option(
    "-r",
    "--remote",
    type=str,
    required=True,
    help="Remote name. If the reference repository is"
    " https://github.com/OCA/pos, set 'OCA'.",
    default="grap",
)
@click.option(
    "-u",
    "--copier-url",
    type=str,
    required=True,
    help="Git URL of the copier template to use for the new branch.",
    default="https://github.com/grap/oca-addons-repo-template-v16",
)
@click.option("-f", "--force", is_flag=True, show_default=True, default=False)
@click.pass_context
def create_branch(ctx, initial_version, target_version, remote, copier_url, force):
    """Create a new branch for Odoo addons"""

    # recover Copier answers from initial version
    git_checkout(initial_version)
    copier_file = Path(".copier-answers.yml").resolve()
    if copier_file.exists():
        with copier_file.open(mode="r") as file:
            copier_content = file.read()
    else:
        copier_content = ""

    # create empty git branch
    git_checkout(target_version, mode="create_orphan")
    if copier_content:
        with copier_file.open(mode="w") as file:
            copier_content = file.write(copier_content)

        git_commit_all(
            "[INIT] initialize .copier-answers.yml file"
            f" with file present in {initial_version}."
        )

    # Adapt copier-answers.yml file to recent GRAP convention
    logger.info("Adapt copier answers file to new conventions ...")
    replace_expression(copier_file, "odoo_real_version: 12.0", "")
    ensure_line(copier_file, "convert_readme_fragments_to_markdown: true")
    ensure_line(copier_file, "odoo_test_flavor: Odoo")
    ensure_line(copier_file, "use_ruff: true")

    git_commit_all(
        f"[INIT] Update .copier-answers.yml answers"
        f" with {remote} conventions for {target_version} version."
    )

    subprocess.check_call(["copier", "copy", copier_url, ".", "--trust"])

    git_commit_all("[INIT] Initialize repo with copier template.", verify=True)

    git_push(remote, target_version, force)
