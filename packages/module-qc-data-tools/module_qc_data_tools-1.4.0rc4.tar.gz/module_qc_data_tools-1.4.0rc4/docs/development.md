# For Developer

## new releases

When making a new release, the following steps are taken:

1. update `docs/history.md` to document all the changes (added/fixed/changed)
2. following [versioning](#versioning) to create a new release
3. keep an eye on the pipelines and deployment to pypi to ensure everything went
   smoothly

## versioning

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

## pre-commit

Install pre-commit to avoid CI failure. Once pre-commit is installed, a git hook
script will be run to identify simple issues before submission to code review.

Instruction for installing pre-commit in a python environment:

1. Activate python environment, e.g. `source venv/bin/activate`.
2. Run `python3 -m pip install pre-commit`.
3. Run `pre-commit install` to install the hooks in `.pre-commit-config.yaml`.

After installing pre-commit, `.pre-commit-config.yaml` will be run every time
`git commit` is done. Redo `git add` and `git commit`, if the pre-commit script
changes any files.
