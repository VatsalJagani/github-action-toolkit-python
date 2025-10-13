# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

## [v0.5.1](https://github.com/VatsalJagani/github-action-toolkit-python/releases/tag/v0.5.1) - 2025-10-13

### Fixed

- get_user_input_as function's default value recognition when not defined in the environment variable issue is fixed.
- devtools reorganized.


## [v0.5.0](https://github.com/VatsalJagani/github-action-toolkit-python/releases/tag/v0.5.0) - 2025-10-11

### Added

- Added GitHubArtifacts class with following functions
    - get_artifacts
    - get_artifact
    - download_artifact
    - delete_artifact

### Improvement

- Code cleanup.


## [v0.4.0](https://github.com/VatsalJagani/github-action-toolkit-python/releases/tag/v0.4.0) - 2025-10-10

### Code Improvement

- Linting issues fixed.
- Code annotation updated.

### Improvements for Better Python Package Management

- Added Agent instruction for Code Editors and AI tools.
- Developer Docs improved.
- Contributor notes improved.
- Document Contributor notes improved.
- Release publication document added.
- GitHub Workflow - Build and Test updated.
- New Github Workflow for publishing Release and Docs added.
- Make file improved.
- Adding linting checks and other code checking file.
- `pyproject.toml` file improved.


## [v0.3.0](https://github.com/VatsalJagani/github-action-toolkit-python/releases/tag/v0.3.0) - 2025-09-20

### Added

- New class `Repo` added with relevant functions.
    - get_current_branch
    - create_new_branch
    - add
    - commit
    - add_all_and_commit
    - push
    - pull
    - create_pr



## [v0.2.0](https://github.com/VatsalJagani/github-action-toolkit-python/releases/tag/v0.2.0) - 2025-09-20

### Added

- Following new print messages related functions have been added.
    - info

- Following new user input related function has been added.
    - get_all_user_inputs
    - print_all_user_inputs
    - get_user_input_as


## [v0.1.0](https://github.com/VatsalJagani/github-action-toolkit-python/releases/tag/v0.1.0) - 2025-09-20

### Added

- Following print messages related functions have been added.
    - echo
    - debug
    - notice
    - warning
    - error
    - add_mask
    - start_group
    - end_group
    - group

- Following job summary related functions have been added.
    - append_job_summary
    - overwrite_job_summary
    - remove_job_summary

- Following input, output, environment variable and state related functions have been added.
    - get_state
    - save_state
    - get_user_input
    - set_output
    - get_workflow_environment_variables
    - get_env
    - set_env

- Following event_payload related function has been added.
    - event_payload
