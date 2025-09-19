# github-action-toolkit - Developer README File

### Local Development Setup

* Create virtual environment.
```
conda create -n github_action_toolkit python=3.11
```

* Activate virtual environment.
```
conda activate github_action_toolkit
```

* Install dev dependencies:
```
python -m pip install -e '.[dev]'
```

* Add/update package dependencies:
    * Update `pyproject.toml` file's `[project]` section's `dependencies` parameter with new dependencies.

* Install/upgrade dependencies in local environment.
```
python -m pip install -e .
```

* Run Checks and Test Before Committing Changes
```
make
```

* Fix Import sorting (isort) issues automatically
    * For all files:
        ```
        isort .
        ```
    * For specific file:
        ```
        isort github_action_toolkit/abc.py
        ```

* Check for formatting issues (black)
```
black --check .
```

* Auto-fix formatting issues with black
```
black .
```

* Check for linting issues (ruff)
```
ruff check .
```

* Auto-fix linting issues with ruff
```
ruff check --fix .
```

* Check for static type checking issues (mypy)
```
mypy .
```


### Pypi Release Publish Setup

(Optional) If you plan on publishing your package to PyPI, add repository secrets for `PYPI_USERNAME` and `PYPI_PASSWORD`. To add these, go to "Settings" > "Secrets" > "Actions", and then click "New repository secret".

    *If you don't have PyPI account yet, you can [create one for free](https://pypi.org/account/register/).*


### readthedocs Doc Publish Setup

(Optional) If you want to deploy your API docs to [readthedocs.org](https://readthedocs.org), go to the [readthedocs dashboard](https://readthedocs.org/dashboard/import/?) and import your new project.

    Then click on the "Admin" button, navigate to "Automation Rules" in the sidebar, click "Add Rule", and then enter the following fields:

    - **Description:** Publish new versions from tags
    - **Match:** Custom Match
    - **Custom match:** v[vV]
    - **Version:** Tag
    - **Action:** Activate version

    Then hit "Save".

    *After your first release, the docs will automatically be published to [your-project-name.readthedocs.io](https://your-project-name.readthedocs.io/).*


### Creating Release Process

1. Update the version in `github_action_toolkit/version.py`.

3. Run the release script:

    ```bash
    ./scripts/release.sh
    ```

    This will commit the changes to the CHANGELOG and `version.py` files and then create a new tag in git
    which will trigger a workflow on GitHub Actions that handles the rest.

## Fixing a failed release

If for some reason the GitHub Actions release workflow failed with an error that needs to be fixed, you'll have to delete both the tag and corresponding release from GitHub. After you've pushed a fix, delete the tag from your local clone with

```bash
git tag -l | xargs git tag -d && git fetch -t
```

Then repeat the steps above.
