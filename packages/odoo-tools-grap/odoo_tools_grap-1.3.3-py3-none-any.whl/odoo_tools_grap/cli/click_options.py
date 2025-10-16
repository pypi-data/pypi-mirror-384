import click


def option_repo_config_file(function):
    function = click.option(
        "-c",
        "--config-repo-file",
        default="repos.yml",
        type=click.Path(
            exists=True,
            dir_okay=False,
            resolve_path=True,
        ),
        help="Repositories file",
    )(function)
    return function
