import subprocess
from datetime import datetime
from pathlib import Path

import click
from git import Repo
from github import Auth, Github, GithubException
from loguru import logger

from .tools import execute, git_push, git_switch


@click.command()
@click.option("-i", "--initial-version", type=str, required=True, default="12.0")
@click.option("-t", "--target-version", type=str, required=True, default="16.0")
@click.option("-r", "--distant-remote", type=str, required=True, default="grap")
@click.option("-l", "--local-remote", type=str, required=True)
@click.option("-m", "--modules", type=str)
@click.option(
    "-g",
    "--github-token-file",
    type=click.Path(
        exists=True,
        dir_okay=False,
        resolve_path=True,
    ),
)
@click.option("-f", "--force", is_flag=True, show_default=True, default=False)
@click.pass_context
def migrate(
    ctx,
    initial_version,
    target_version,
    distant_remote,
    local_remote,
    modules,
    github_token_file,
    force,
):
    """Migrate modules from a version X to version Y"""
    current_dir = Path("./").resolve()
    repo = Repo(str(current_dir))

    logger.info(f"Read github token in '{github_token_file}' ...")
    github_token_file = Path(github_token_file)
    with github_token_file.open(mode="r") as file:
        token = file.read()

    # Switch and pull last revision of initial version
    git_switch(repo, distant_remote, initial_version, do_pull=True)

    # Get modules, if not defined
    modules = modules and modules.split(",") or []
    modules_path = []

    if not modules:
        for directory in [x for x in current_dir.iterdir() if x.is_dir()]:
            if (directory / "__manifest__.py").exists():
                modules_path.append(directory)
    else:
        for module in modules:
            module_path = (Path("./") / module).resolve()
            if module_path.exists():
                modules_path.append(module_path)
            else:
                logger.warning(f"{module} not found in the branch {initial_version}")

    # Switch and pull last revision of target version
    git_switch(repo, distant_remote, target_version, do_pull=True)

    for module_path in modules_path:
        module_name = module_path.name
        patch_path = (
            Path("/tmp/") / datetime.utcnow().strftime("%Y-%m-%d__%H-%M-%S-%f")
        ).resolve()
        branch_name = f"{target_version}-mig-{module_name}"

        logger.info(f"Migrating {module_name} ...")
        git_switch(repo, distant_remote, target_version)
        if branch_name in repo.branches:
            if force:
                value = "D"
            else:
                value = click.prompt(
                    f"Branch {branch_name} exist:"
                    " [s]kip migration or [d]rop branch ?",
                    type=str,
                    default="s",
                )
            if value in ["s", "S"]:
                logger.info(f"Skipping migration of {module_name}")
                continue
            elif value in ["d", "D"]:
                logger.warning(f"Dropping branch {branch_name}")
                execute(["git", "branch", "-D", branch_name])
            else:
                logger.critical("Incorrect answer, exiting...")
                return

        logger.info(f"Creating new branch {branch_name} ...")
        execute(["git", "checkout", "-b", branch_name])

        logger.info(f"Creating patches in {patch_path} ...")
        patch_path.mkdir(parents=True, exist_ok=True)
        execute(
            [
                "git",
                "format-patch",
                "--keep-subject",
                f"--output-directory={patch_path}",
                f"{distant_remote}/{target_version}"
                f"..{distant_remote}/{initial_version}",
                "--",
                f"{module_name}",
            ]
        )
        patch_files = sorted([x for x in patch_path.iterdir()])

        subprocess.check_call(["pre-commit", "uninstall"])

        logger.info(f"Applying {len(patch_files)} patches ...")
        last_summary = ""
        for i, patch_file in enumerate(patch_files, 1):
            logger.info(
                f"{i:>02}/{len(patch_files):>02}"
                f" Applying patch {patch_file.name} ..."
            )
            execute(["git", "am", "-3", "--keep", str(patch_file)])
            current_summary = repo.head.commit.summary

            clean_current_summary = (
                current_summary.replace("fixup! ", "")
                .replace("squash! ", "")
                .replace("amend! ", "")
            )
            clean_last_summary = (
                last_summary.replace("fixup! ", "")
                .replace("squash! ", "")
                .replace("amend! ", "")
            )

            if clean_current_summary == clean_last_summary:
                logger.info(
                    "Merging the following commits:\n"
                    f"- commit 1: '{last_summary}'\n"
                    f"- commit 2: '{current_summary}'"
                )
                execute(["git", "reset", "--soft", "HEAD~1"])
                execute(
                    [
                        "git",
                        "commit",
                        "-a",
                        "--amend",
                        "--no-edit",
                        "--allow-empty",
                    ]
                )
            last_summary = current_summary

        logger.info("Call pre-commit ...")
        try:
            execute(["pre-commit", "run", "-a"])
        except Exception:
            try:
                execute(["pre-commit", "run", "-a"])
            except Exception:
                logger.warning("Some pre-commit stuff should be fixed manually.")

        logger.info("Add and commit pre-commit changes in no-verify mode ...")
        execute(["git", "add", "."])
        execute(
            [
                "git",
                "commit",
                "--no-verify",
                "--message",
                f"[IMP] {module_name}: pre-commit stuff",
            ]
        )

        logger.info("Call odoo-module-migrate ...")
        execute(
            [
                "odoo-module-migrate",
                f"--init-version-name={initial_version}",
                f"--target-version-name={target_version}",
                "--no-commit",
                "--no-pre-commit",
                f"--modules={module_name}",
            ]
        )

        logger.info("Add and commit migration changes in no-verify mode ...")
        execute(["git", "add", "."])
        execute(
            [
                "git",
                "commit",
                "--no-verify",
                "--message",
                f"[MIG] {module_name}: Migration to {target_version}"
                f" (from {initial_version})",
            ]
        )

        git_push(local_remote, branch_name)

        logger.info("Creating Pull Request ...")
        gh = Github(auth=Auth.Token(token))
        gh_repo = gh.get_repo(f"{distant_remote}/{current_dir.name}")
        try:
            pull_request = gh_repo.create_pull(
                base=target_version,
                head=f"{local_remote}:{branch_name}",
                title=f"[{target_version}][MIG] {module_name}:"
                f" Migration to {target_version} (from {initial_version})",
                draft=True,
            )
            logger.info(f"Pull request available on {pull_request.html_url}")
        except GithubException as e:
            message_text = "\n- ".join(
                [x.get("message", "") for x in e.data.get("errors", [])]
            )
            logger.error(
                f"Unable to create the pull request on github."
                f" Status: {e.status}"
                f"\n- {message_text}"
            )

    logger.info("End of the script !")
