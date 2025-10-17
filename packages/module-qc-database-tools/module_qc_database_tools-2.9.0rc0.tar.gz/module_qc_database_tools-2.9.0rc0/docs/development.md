# For Developer

## Branches

Any planned developments and features, when ready, shall be merged into the
`main` branch. Any bugfixes should be deployed in a timely fashion. Bugfixes
should be based on the last tagged version and developed on a `release` branch,
which then will be tagged according to the versioning mentioned
[below](#versioning). Any changes made on the `release` branch shall be merged
back into `main` immediately after deploying the bugfix. The `release` branch
can then be deleted when a new minor version is released containing the bugfix.

## New releases

When making a new release, the following steps are taken:

1. update `docs/history.md` to document all the changes (added/fixed/changed)
2. following [versioning](#versioning) to create a new release
3. keep an eye on the pipelines and deployment to pypi to ensure everything went
   smoothly

## Versioning

To ensure we have stable software versions but also the ability to deploy
bugfixes quickly, we follow the semantic versioning and use `x.y.z` for
`major.minor.patch` versions.

Whenever a patch or bugfix should be released, only push and merge the isolated
patch or bugfix on top of the existing version `x.y.z`. And only increase the
`patch` version for a new release `x.y.z+1`. Tag release candicate accordingly,
e.g. as `x.y.z+1rc0`.

Whenever a planned feature release happens, the `minor` version is increased to
`x.y+1.0` where the `patch` version is reset to `0`. Tag release candidates
accordingly, e.g. as `x.y+1.0rc0`.

## Tagging a new version

In case you need to tag the version of the code, you need to have either `hatch`
or `pipx` installed.

1. Activate python environment, e.g. `source venv/bin/activate`.
2. Run `python -m pip install hatch` or `python -m pip install pipx`.

You can bump the version via:

```
pipx run hatch run tag x.y.z

# or

hatch run tag x.y.z
```

where `x.y.z` is the new version to use. This should be run from the default
branch (`main` / `master`) as this will create a commit and tag, and push for
you. So make sure you have the ability to push directly to the default branch.

## Pipeline

After pushing onto remote, the pipeline will run and do roughly the following
checks and tests in this order:

- lint
- pre-commit
- pytest

In order to save time and pipeline iterations, these tests can and should be be
run and fixed locally before pushing to remote.

### Pre-commit

Run this first as `pre-commit` will automatically fix some issues.

Install pre-commit to avoid CI failure. Once pre-commit is installed, a git hook
script will be run to identify simple issues before submission to code review.

Instruction for installing pre-commit in a python environment:

1. Activate python environment, e.g. `source venv/bin/activate`.
2. Run `python3 -m pip install pre-commit`.
3. Run `pre-commit install` to install the hooks in `.pre-commit-config.yaml`.

After installing pre-commit, `.pre-commit-config.yaml` will be run every time
`git commit` is done. Redo `git add` and `git commit`, if the pre-commit script
changes any files.

### Lint

Run `pipx run hatch run lint` or `hatch run lint` to ensure the code is up to
standard and fix according to suggestions.

### Pytest

Tests are located in the `tests` folder. All tests can be run with
`pipx run hatch run +py=${PYTHON_VERSION} dev:test` or
`hatch run +py=${PYTHON_VERSION} dev:test`, where `${PYTHON_VERSION}` can be
replaced with e.g. `3.9`.

Individual tests can also be run via `pytest tests/<test>.py` which uses your
current python version.
