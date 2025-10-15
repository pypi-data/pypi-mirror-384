# MCLI (MosaicML Command Line Interface)

## Understanding MCLI

MCLI is a command line interface and python SDK for Databricks Mosaic AI training.

To understand MCLI use cases, read the [customer-facing docs](https://mcli.docs.mosaicml.com/) and go through installation and tutorials.

## Development environment setup

### Pre-requisites

**Git**

We’re using git and GitHub for source control. In case your laptop does not have git installed, [this is a good resource on installing git](https://github.com/git-guides/install-git#install-git) (and it has [even more resources](https://github.com/git-guides/) to help get started with git concepts and commands).

**Python**

MCLI requires Python 3.11 or higher. To install Python, start [here](https://www.python.org/downloads/).

### Setup steps

**Clone repository**

Clone the repo from GitHub and cd into the newly created project dir

```bash
$ git clone git@github.com:mosaicml/mosaicml-cli.git
$ cd mosaicml-cli
```

**Create a virtual environment and install dependencies**

You can either use (A) the automated Makefile set-up or (B) the manual set-up:

**(A) Makefile set-up**

Run this command from the project root:

```bash
$ make venv
```

This will create a new python virtual environment and install dependencies for the repo in a folder named "venv" under the current directory, and this folder is ignored by git via .gitignore.
You can also specify `venv` in a different location by updating the `VENV_FOLDER` env variable in `Makefile` relative to your current working directory.

Activate your new virtual environment with:

```bash
$ source venv/bin/activate
```

You will now see your terminal prompt being updated to start with the virtual environment name in parenthesis: "(venv)". This is how you know you are working in an activated virtual environment!

**(B) Manual installation**

Update pip to the latest version

```bash
$ pip install --upgrade pip
```

Create a venv directory with Python 3.11+. We recommend to create your venv directory in a parent folder to all your MosaicML git repos (i.e. `~/workspace`), so you can more easily locate your virtual env.

```bash
$ python3 -m venv ./venv
$ source venv/bin/activate
```

Install mcli dependencies (including dev dependencies)
Here we're using the `-e` flag to indicate this module is "editable", meaning changes to the source directory will immediately affect the installed package without requiring to re-install.

Run this command to install dependencies for mcli.

```bash
$ pip install -e ".[all]"
```

**Give `mcli` a quick test**

Check you have local mcli installed by running the command below, and ensuring you get the same version as in the file [`mcli/version.py`](https://github.com/mosaicml/mosaicml-cli/blob/dev/mcli/version.py)

```bash
$ mcli version
```

**Building and editing the docs**
We welcome any contributions to our [docs](docs)!
All markdowns can be found in the [docs/source](docs/source) folder.
If adding a new page, please make sure it is also indexed in [docs/source/index.rst](docs/source/index.rst).
We use [Sphinx documentation generator](https://www.sphinx-doc.org/en/master/) and host our docs using [Read the Docs](https://readthedocs.com/projects/mosaicml-mcli/) (Note: [Vercel](https://vercel.com/mosaicml/mosaicml-cli) has been deprecated!).

You can preview the docs build attached to your PR and/or commits through the github UI or [Read the Docs](https://readthedocs.com/projects/mosaicml-mcli/builds/) directly.
For quicker iteration, you can also build the docs locally:

```bash
make docs
```

**Run `mcli` tests**

Run tests to make sure setup in in order. All tests should either pass or configured to be ignored.

```bash
make test
```

This will locally trigger all tests that will run in github CI (integration, unit, docs, formatting and type checking).
You can also run individual tests within specific entrypoints (e.g. `make test-unit`) or call pytest directly (e.g. `pytest tests/utils/test_version_sorting.py::test_sorting`).

**Passing linting and formatting checks**
There are several options for automatically formatting and checking files locally. We encourage people to use what they prefer, and only enforce that everything is passing in CI before a PR is merged. Options include:

1. VSCode (or other IDE) "format on save". The python interpreter should be pointed at `venv/bin/python` and VSCode project/user settings should probably contain:

```json
"editor.formatOnSave": true,
"python.formatting.provider": "yapf",
"files.insertFinalNewline": true,
```

2. Pre-commit hooks. Follow [these](https://pre-commit.com/) instructions and use our `.pre-commit-config.yaml` file
3. Manually. Run `make format` before pushing changes

**And… you are done!**

A few notes for later on:

- To exit the virtual environment later on: `$ deactivate`
- To get back into your virtual environment: `$ source venv/bin/activate`

## Running against mcloud as a developer

There are currently several MCLI Modes. To use a mode other than the default `PROD`, set your local environment variable `MCLI_MODE` or specify the mode when you run MCLI commands (e.g. `MCLI_MODE=DEV mcli get runs`)

| Mode       | Used By         | MAPI Endpoint                            | Use cases                                              | API Key                                                      |
| ---------- | --------------- | ---------------------------------------- | ------------------------------------------------------ | ------------------------------------------------------------ |
| `PROD`     | Default         | https://api.mosaicml.com/graphql         | Demos, simulating customer behavior, integration tests | Create one [here](https://console.mosaicml.com/account#)     |
| `STAGING`  | Developers only | https://staging.api.mosaicml.com/graphql | Test changes queued for prod release                   | Testing api key                                              |
| `DEV`      | Developers only | https://dev.api.mosaicml.com/graphql     | Test against dev branch of mcloud                      | Create one [here](https://dev.cloud.mosaicml.com/account#) |
| `LOCAL`    | Developers only | http://localhost:3001/graphql            | Test local mcloud changes                              | Testing api key                                              |

Note for almost all of these modes, you need to set an api key to talk to MAPI:

```bash
mcli set api-key <value>
```

The `~/.mosaic/mcli_config` file will save unique api keys for each mode

**Running in `LOCAL` mode**

For local mode, you'll need to spin up mcloud on your local machine.
For instructions on how to do this, see [the mcloud repo](https://github.com/mosaicml/mcloud/blob/dev/README.md).
Once you have mcloud running locally, set your API key to the value shown in the table above and prefix your commands with `MCLI_MODE=LOCAL`.

**Running in `DBX_AWS_STAGING` mode**
We allow for custom code runs in the staging environment only within Databricks for fast iteration on KaaS clusters. In order to submit yaml's, you have to first set-up your Databricks API token and use the `MCLI_MODE=DBX_AWS_STAGING`.

1. First, navigate to the workspace you want to create a Databricks API token in the UI and create a developer key. You need admin privileges in order to create one. Go to user -> Settings -> Developer -> Manage Access Tokens -> Generate new token.

2. Then, save your databricks API token in some local file, say ~/token. 

3. Then, you can run MCLI commands in staging with:
```
export MCLI_MODE=DBX_AWS_STAGING
MOSAICML_ACCESS_TOKEN_FILE=~/token mcli g runs --limit 5

MOSAICML_ACCESS_TOKEN_FILE=~/token mcli run -f my-yaml.yaml
```
