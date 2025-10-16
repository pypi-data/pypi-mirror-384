import fileinput
import subprocess
import sys

from loguru import logger


def git_commit_all(message, verify=False):
    if verify:
        logger.info("Verify All changes ...")
        subprocess.check_call(["pre-commit", "install"])
        subprocess.check_call(["git", "add", "."])
        subprocess.check_call(["pre-commit", "run", "-a"])

    logger.info("Add and commit all changes ...")
    subprocess.check_call(["git", "add", "."])
    subprocess.check_call(
        [
            "git",
            "commit",
            "--verify" if verify else "--no-verify",
            "-am",
            message,
        ]
    )


def git_checkout(branch_name, mode="switch"):
    if mode == "switch":
        logger.info(f"Switch to branch {branch_name}...")
        subprocess.check_call(["git", "checkout", branch_name])
    elif mode == "create":
        logger.info(
            f"Create a new branch {branch_name}" " based on the current one ..."
        )
        subprocess.check_call(["git", "checkout", "-b", branch_name])
    elif mode == "create_orphan":
        logger.info(f"Create a new orphan branch {branch_name} ...")
        subprocess.check_call(["git", "checkout", "--orphan", branch_name])
        subprocess.check_call(["git", "reset", "--hard"])


def git_push(remote, branch_name, force_push=False):
    logger.info(f"Force Push on {remote}/{branch_name}...")
    commands = ["git", "push", remote, branch_name]
    if force_push:
        commands.append("--force")
    logger.debug(f"Calling: {commands}")
    subprocess.check_call(commands)


def git_switch(repo, remote, version, do_pull=False):
    if repo.active_branch.name != version:
        try:
            logger.info(f"Switching on {version} ...")
            subprocess.check_call(["git", "switch", version])
        except Exception:
            logger.error(f"The branch '{version}' doesn't exist.")
            return

    try:
        logger.info(f"Pulling last revision of {version} ...")
        subprocess.check_call(["git", "pull", remote, version])
    except Exception:
        logger.error(f"Pulling '{remote}/{version}' failed.")
        return


def execute(command):
    logger.debug(f"run command\n{' '.join(command)}")
    stdout = subprocess.run(command, check=True, stdout=subprocess.PIPE)
    logger.debug(stdout)


def replace_expression(file, search_expression, replace_expression):
    for line in fileinput.input(file, inplace=1):
        if search_expression in line:
            if replace_expression:
                line = line.replace(search_expression, replace_expression)
            else:
                continue
        sys.stdout.write(line)


def ensure_line(file_path, required_line):
    file = file_path.open(mode="r")
    lines = file.readlines()
    file.close()
    for line in lines:
        if line == required_line:
            return

    file = file_path.open(mode="a")
    file.write(str(f"{required_line}\n"))
    file.close()
