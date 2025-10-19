# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Added

- Fluent Job Summary Builder API (`JobSummary` class) for constructing rich GitHub Actions job summaries
  - Support for headings, text, line breaks, and separators
  - Support for ordered and unordered lists
  - Support for tables with headers, rows, and advanced cell options (colspan, rowspan)
  - Support for code blocks with optional syntax highlighting
  - Support for images with alt text and dimensions
  - Support for collapsible details sections
  - Support for quotes and links
  - Automatic content sanitization to prevent XSS attacks
  - Size limit enforcement (1 MiB maximum)
  - Buffer management with `write()`, `clear()`, `is_empty()`, and `stringify()` methods
- Template API (`JobSummaryTemplate` class) with pre-built templates for:
  - Test reports with pass/fail/skip counts
  - Code coverage reports with per-module breakdowns
  - Deployment reports with environment and version details
  - Benchmark reports with performance metrics
  - Comprehensive documentation for Job Summary API with examples
- Added `export_variable` function as an alias for `set_env` to match Node.js @actions/core naming convention
- Added `add_path` function to prepend directories to the system PATH for subsequent workflow steps

### Changed

- Enhanced all environment file operations (`GITHUB_OUTPUT`, `GITHUB_ENV`, `GITHUB_STATE`, `GITHUB_PATH`) with thread-safe atomic writes
- Improved security with delimiter injection prevention and enhanced input validation
- All file operations now use `fsync()` for atomic writes ensuring data durability
- Added strongly typed event models using Pydantic for common GitHub Actions events:
  - `PushEvent` for push events
  - `PullRequestEvent` for pull_request events
  - `IssueCommentEvent` for issue_comment events
  - `WorkflowRunEvent` for workflow_run events
- Added supporting typed models: `Actor`, `Repository`, `Commit`, `Label`, `PullRequest`, `Issue`, `Comment`, `WorkflowRun`, `BaseEvent`
- Added `get_typed_event()` function to parse event payload into typed models
- Added convenience helper functions:
  - `get_event_name()` - get the name of the triggering event
  - `is_pr()` - check if current event is a pull request
  - `get_pr_number()` - get PR number for pull request events
  - `head_ref()` - get head reference for push/PR events
  - `base_ref()` - get base reference for PR events
  - `get_changed_files()` - get list of changed files for push events
  - `get_labels()` - get list of labels for PR/issue events


## [v0.6.0](https://github.com/VatsalJagani/github-action-toolkit-python/releases/tag/v0.6.0) - 2025-10-15

### Added

- Added a new debugging function `print_directory_tree`

### Changed

- `Repo` class: Introduced shared cleanup helper to synchronize to base branch. Cleanup job runs on both context enter and exit (fetch, checkout, hard reset, clean, pull). To use it you can use the new parameter added to Repo constructor `cleanup`.


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
