[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

![PyPI - Python Version](https://img.shields.io/pypi/pyversions/odoo-tools-grap)
![PyPI - Downloads](https://img.shields.io/pypi/dm/odoo-tools-grap)
![GitLab last commit](https://img.shields.io/gitlab/last-commit/34780558)
![GitLab stars](https://img.shields.io/gitlab/stars/34780558?style=social)

# odoo-tools-grap

This tools provide extra cli commands to simplify recurring operations for Odoo developers.

- To develop and contribute to the library, refer to the `DEVELOP.md` file.
- Refer to the `ROADMAP.md` file to see the current limitation, bugs, and task to do.
- See authors in the `CONTRIBUTORS.md` file.

# Table of Contents

- [Installation](#installation)
- [Usage](#usage)
  - [Command `diff` (View repositories status)](#command-diff)
  - [Command `generate` (Generate Odoo config File)](#command-generate)
  - [Command `create-branch` (Create new Orphan Branch)](#command-create-branch)
  - [Command: `migrate` (Migrate module from a version to another)](#command-migrate)
- [Prerequites](#prerequites)

<a name="installation"/>

# Installation

The library is available on [PyPI](https://pypi.org/project/odoo-tools-grap/).

To install it simply run :

```console
pipx install odoo-tools-grap
```

(See alternative installation in `DEVELOP.md` file.)

<a name="usage"/>

# Usage

**Note:**

The term `odoo-tools-grap` can be replaced by `otg` in all the command lines below.

<a name="command-diff"/>

## Command: `diff` (View repositories status)

Based on a repos config file (`repos.yml file`, used by gitaggregate by
exemple), this script will display the result of the `git diff` for each
repository.

```console
odoo-tools-grap diff --config repos.yml
```

**Result Sample**

```
2024-03-27 16:37:24.725 | WARNING  | odoo_tools_grap.cli.cli_diff:diff:31 - [BAD BRANCH] ./src/OCA/product-attribute is on 16.0-product_pricelist_simulation-various-fixes.(Should be on 16.0-current)
2024-03-27 16:37:25.395 | WARNING  | odoo_tools_grap.cli.cli_diff:diff:38 - [LOCAL CHANGES] ./src/OCA/sale-workflow has 1 local changes.
2024-03-27 16:37:25.444 | WARNING  | odoo_tools_grap.cli.cli_diff:diff:43 - [UNTRACKED] ./src/OCA/sale-workflow has 2 untracked files.
```

<a name="command-generate"/>

## Command: `generate` (Generate Odoo config File)

Base on a repos config file, (`repos.yml file`, used by gitaggregate by exemple),
and template(s) of odoo config file, this script will generate a complete config file for Odoo
with addons_path depending on the repos config file.

```console
odoo-tools-grap generate\
    --config repos.yml\
    --input-files ./template.config.cfg\
    --output-file ./odoo.cfg
```

<a name="command-create-branch"/>

## Command: `create-branch` (Create new Orphan Branch)

This command will:

- create a new orphan target version
- add a `copier-answers.yml` file base on the previous copier answers in the initial version and commit it
- Adapt copier answers to new GRAP conventions
- Ask for copier answers. (At this step, answer default value to all questions)
- Run pre-commit
- Push the new branch on github

Before using this command, clone your repo in the previous existing branch.
for exemple:

```
git clone git@github.com:grap/grap-odoo-custom --origin=grap --branch 12.0
cd grap-odoo-custom
```

Example:

```console
odoo-tools-grap create-branch\
    --initial-version 12.0\
    --target-version 16.0\
    --remote grap\
    --copier-url https://github.com/grap/oca-addons-repo-template-v16
```

<a name="command-migrate"/>

## Command: `migrate` (Migrate module from a version to another)

This command will:

- Pull the last commits of the initial version
- Pull the last commits of the target version
- Create a new branch named for the module to migrate
- Cherry pick commits of the module to migrate. See OCA Documentation: https://github.com/OCA/maintainer-tools/wiki/Migration-to-version-16.0#technical-method-to-migrate-a-module-from-150-to-160-branch
- Eventually merge neighboring commits. (if the commit contains --fixup, or have the same name)
- Run pre-commit and commit changes
- Call odoo-module-migrate (https://github.com/OCA/odoo-module-migrator)
- (At this step, please note warning and error that should be fixed in a second step)
- Commit changes
- Push the new branch on github
- Create a new draft Pull Request

Before using this command:

- you should be in the folder of the repository. (created with `create-branch` command.)
- having added your personal remote with
  `git remote add YOUR-GITHUB-ACCOUNT git@github.com:YOUR-GITHUB-ACCOUNT/grap-odoo-custom`

```console
odoo-tools-grap migrate\
    --initial-version 12.0\
    --target-version 16.0\
    --modules grap_cooperative\
    --distant-remote grap\
    --local-remote YOUR-GITHUB-ACCOUNT\
    --github-token-file ABSOLUTE-PATH-TO-A-FILE-THAT-CONTAINS-GITHUB-TOKEN
```

<a name="prerequites"/>

# Prerequites

To understand this tool:

- You need to know the following tools:
  - `gitaggregate` tools (https://github.com/acsone/git-aggregator)
  - `odoo-module-migrate` tools (https://github.com/OCA/odoo-module-migrator)
- Understand the following processes:
  - https://github.com/OCA/maintainer-tools/wiki/Migration-to-version-17.0#technical-method-to-migrate-a-module-from-160-to-170-branch
