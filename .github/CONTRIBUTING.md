# Contributing

Thanks for considering contributing! Please read this document to learn the various ways you can contribute to this project and how to go about doing it.

## Bug reports and feature requests

### Did you find a bug?

First, do [a quick search](https://github.com/VatsalJagani/github-action-toolkit-python/issues) to see whether your issue has already been reported.
If your issue has already been reported, please comment on the existing issue.

Otherwise, open [a new GitHub issue](https://github.com/VatsalJagani/github-action-toolkit-python/issues).  Be sure to include a clear title
and description.  The description should include as much relevant information as possible.  The description should
explain how to reproduce the erroneous behavior as well as the behavior you expect to see.  Ideally you would include a
code sample or an executable test case demonstrating the expected behavior.

### Do you have a suggestion for an enhancement or new feature?

We use GitHub issues to track feature requests. Before you create a feature request:

* Make sure you have a clear idea of the enhancement you would like. If you have a vague idea, consider discussing
it first on a GitHub issue.
* Check the documentation to make sure your feature does not already exist.
* Do [a quick search](https://github.com/VatsalJagani/github-action-toolkit-python/issues) to see whether your feature has already been suggested.

When creating your request, please:

* Provide a clear title and description.
* Explain why the enhancement would be useful. It may be helpful to highlight the feature in other libraries.
* Include code examples to demonstrate how the enhancement would be used.

## Making a pull request

When you're ready to contribute code to address an open issue, please follow these guidelines to help us be able to review your pull request (PR) quickly.

1. **Initial setup** (only do this once)

    <details><summary>Expand details 👇</summary><br/>

    If you haven't already done so, please [fork](https://help.github.com/en/enterprise/2.13/user/articles/fork-a-repo) this repository on GitHub.

    Then clone your fork locally with

        git clone https://github.com/USERNAME/github-action-toolkit-python.git

    or 

        git clone git@github.com:USERNAME/github-action-toolkit-python.git

    At this point the local clone of your fork only knows that it came from *your* repo, github.com/USERNAME/github-action-toolkit-python.git, but doesn't know anything the *main* repo, [https://github.com/VatsalJagani/github-action-toolkit-python.git](https://github.com/VatsalJagani/github-action-toolkit-python). You can see this by running

        git remote -v

    which will output something like this:

        origin https://github.com/USERNAME/github-action-toolkit-python.git (fetch)
        origin https://github.com/USERNAME/github-action-toolkit-python.git (push)

    This means that your local clone can only track changes from your fork, but not from the main repo, and so you won't be able to keep your fork up-to-date with the main repo over time. Therefore you'll need to add another "remote" to your clone that points to [https://github.com/VatsalJagani/github-action-toolkit-python.git](https://github.com/VatsalJagani/github-action-toolkit-python). To do this, run the following:

        git remote add upstream https://github.com/VatsalJagani/github-action-toolkit-python.git

    Now if you do `git remote -v` again, you'll see

        origin https://github.com/USERNAME/github-action-toolkit-python.git (fetch)
        origin https://github.com/USERNAME/github-action-toolkit-python.git (push)
        upstream https://github.com/VatsalJagani/github-action-toolkit-python.git (fetch)
        upstream https://github.com/VatsalJagani/github-action-toolkit-python.git (push)


**Then Read the `development.md` file on GitHub for this project for development guidelines.**

2. **Ensure your fork is up-to-date**

    <details><summary>Expand details 👇</summary><br/>

    Once you've added an "upstream" remote pointing to [https://github.com/VatsalJagani/github-action-toolkit-python.git](https://github.com/VatsalJagani/github-action-toolkit-python), keeping your fork up-to-date is easy:

        git checkout main  # if not already on main
        git pull --rebase upstream main
        git push

    </details>

3. **Create a new branch to work on your fix or enhancement**

    <details><summary>Expand details 👇</summary><br/>

    Committing directly to the main branch of your fork is not recommended. It will be easier to keep your fork clean if you work on a separate branch for each contribution you intend to make.

    You can create a new branch with

        # replace BRANCH with whatever name you want to give it
        git checkout -b BRANCH
        git push -u origin BRANCH

    </details>

4. **Test your changes**

    <details><summary>Expand details 👇</summary><br/>

    Before submitting a pull request:
    
    - Run tests: `uv run pytest`
    - Run linting: `make lint` or `uv run python devtools/lint.py`
    - Ensure your code builds: `uv build`
    
    </details>


**Then Read the `development.md` file on GitHub for this project for development guidelines.**


### Writing Tests

This project uses a comprehensive testing approach with multiple testing techniques:

#### Property-Based Testing with Hypothesis

For robust validation of edge cases, we use [Hypothesis](https://hypothesis.readthedocs.io/) for property-based testing. Property-based tests are particularly useful for:

- Input validation functions (testing with arbitrary strings, integers, floats)
- String escaping and formatting functions
- Type conversion functions
- Functions that should handle a wide range of inputs

Example:
```python
from hypothesis import given, strategies as st

@given(st.text(min_size=1, max_size=100))
def test_function_handles_arbitrary_strings(text: str):
    """Property test: function handles arbitrary string inputs."""
    result = my_function(text)
    assert isinstance(result, str)
```

When writing property-based tests:
- Use appropriate strategies that match your input domain
- Blacklist invalid characters (e.g., null bytes, surrogates)
- Test properties that should always hold true, not specific values
- Consider idempotency, commutativity, and other mathematical properties

#### Snapshot Testing with Syrupy

For validating formatted output consistency, we use [Syrupy](https://github.com/tophat/syrupy) for snapshot testing. Snapshot tests are ideal for:

- HTML/Markdown output
- Template rendering
- Complex formatted strings
- Command output that should remain stable

Example:
```python
def test_html_output_snapshot(snapshot):
    """Snapshot test for HTML output."""
    result = generate_html_report(data)
    assert result == snapshot
```

When writing snapshot tests:
- Use descriptive test names that indicate what's being tested
- Keep snapshots focused on one aspect of output
- Update snapshots when intentional changes are made: `pytest --snapshot-update`
- Review snapshot diffs carefully in PRs

#### Test Organization

- Place tests in the `tests/` directory matching the module structure
- Use descriptive test function names: `test_<function>_<scenario>`
- Group related tests using test classes when appropriate
- Use fixtures for common setup/teardown
- Add docstrings to complex tests explaining what property is being tested

#### Running Tests

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_input_output.py

# Run with verbose output
uv run pytest -v

# Update snapshots after intentional changes
uv run pytest --snapshot-update

# Run only property-based tests
uv run pytest -k "hypothesis"
```


### Writing docstrings

We use [Sphinx](https://www.sphinx-doc.org/en/master/index.html) to build our API docs, which automatically parses all docstrings
of public classes and methods using the [autodoc](https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html) extension.
Please refer to autoc's documentation to learn about the docstring syntax.
