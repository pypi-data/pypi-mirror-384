<img alt="butler2fox logo" width="128px" src="https://gitlab.com/pismy/butler2fox/-/raw/main/logo.png">

[![pypi](https://img.shields.io/pypi/v/butler2fox.svg)](https://pypi.org/project/butler2fox/)
[![python](https://img.shields.io/pypi/pyversions/butler2fox.svg)](https://pypi.org/project/butler2fox/)

# Butler2Fox

**Butler2Fox** is a CLI tool that helps you migrate your CI/CD pipelines from **Jenkins** to **GitLab**.  
It automatically converts your `Jenkinsfile` into the equivalent `.gitlab-ci.yml`.

> [!IMPORTANT] Scope and Limitations
> 1. Among the [different ways to define a Jenkins pipeline](https://www.jenkins.io/doc/book/pipeline/getting-started/#defining-a-pipeline),
> Butler2Fox only supports the [**Declarative Pipeline**](https://www.jenkins.io/doc/book/pipeline/syntax/#declarative-pipeline) syntax.
> 2. Currently, Butler2Fox does **not** support Groovy code ([`script` steps](https://www.jenkins.io/doc/book/pipeline/syntax/#script)
> and any free-form Groovy statements).
> These unsupported code blocks will be copied **as-is** into the generated `.gitlab-ci.yml`, preceded by a warning comment:
>
>    ```yaml
>    # 🚨 NOT MIGRATED: unsupported Groovy
>    ```

## Install

Butler2Fox requires Python 3.12 or higher and can be installed using pip package manager:

```bash
pip install butler2fox
```

## Usage

```bash
usage: butler2fox [-h] [--debug] [--no-color] [-i INPUT] [-o OUTPUT] [-nc NAMING_CONVENTION]

This tool can be used to migrate your Jenkins pipelines to GitLab CI/CD

options:
  -h, --help            show this help message and exit
  --debug               Enable debugging
  --no-color            Disable colored output
  -i INPUT, --input INPUT
                        Input Jenkinsfile (default: stdin)
  -o OUTPUT, --output OUTPUT
                        Output GitLab CI YAML file (default: same dir as input or stdout)
  -nc NAMING_CONVENTION, --naming-convention NAMING_CONVENTION
                        Jobs and stages naming convention (one of 'unchanged', 'snake', 'kebab', 'camel' or 'pascal')
```

## Initial inspirations

- GitLab's [Migrating from Jenkins](https://docs.gitlab.com/ee/ci/migration/jenkins.html) guide
- GitLab's [Jenkins-to-GitLab migration made easy](https://about.gitlab.com/blog/2024/02/01/jenkins-to-gitlab-migration-made-easy/) blog post
- [Some Jenkinsfile examples](https://gist.github.com/merikan/228cdb1893fca91f0663bab7b095757c) for GitHub Gists

## Developers

Butler2Fox is developed in Python (3.12 or higher), and is based on [Poetry](https://python-poetry.org/)
as packaging and dependency management system:

```bash
# install dependencies
poetry install

# run the tool
poetry run butler2fox ...
```

It uses [Ruff](https://docs.astral.sh/ruff/) for formatting and linting:

```bash
# format code
poetry run ruff format

# lint (and fix) code
poetry run ruff check --fix
```

And it uses [pytest](https://docs.pytest.org/) for unit testing:

```bash
# run tests
poetry run pytest
```
