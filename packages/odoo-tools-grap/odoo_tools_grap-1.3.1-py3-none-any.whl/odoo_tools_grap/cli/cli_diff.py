from pathlib import Path

import click
import yaml
from git import Repo
from loguru import logger

from odoo_tools_grap.cli.click_options import option_repo_config_file


@click.command()
@option_repo_config_file
@click.pass_context
def diff(ctx, config_repo_file):
    """parse a repo.yml config file, and for each repo
    check if repo is clean, on a correct target branch, etc...
    """
    config_repo_file = Path(config_repo_file)

    # Compute Addons path
    stream = open(config_repo_file, "r")
    data = yaml.safe_load(stream)

    for addons_path, repo_data in data.items():
        path = config_repo_file.cwd() / addons_path
        logger.debug(f"Scanning repository '{addons_path}' ...")

        if not path.exists():
            logger.error(
                f"[NOT FOUND] The folder '{addons_path}' has not been found."
                " Maybe you could run:\n"
                f" gitaggregate -c repos.yml -d {addons_path}"
            )
            continue

        repo = Repo(str(path))

        # check if we are in the target repository
        current_branch = repo.active_branch.name
        target_branch = repo_data.get("target", " ").split(" ")[1]
        if current_branch != target_branch:
            logger.warning(
                f"[BAD BRANCH] {addons_path} is on {current_branch}."
                f"(Should be on {target_branch})"
            )

        # check local changes
        if repo.is_dirty():
            logger.warning(
                f"[LOCAL CHANGES] {addons_path} has"
                f" {len(repo.head.commit.diff(None))} local changes."
            )
        if repo.untracked_files:
            logger.warning(
                f"[UNTRACKED] {addons_path} has"
                f" {len(repo.untracked_files)} untracked files."
            )
