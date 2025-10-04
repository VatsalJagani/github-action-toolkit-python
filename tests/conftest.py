import pytest

from github_action_toolkit.file_handler import File


@pytest.fixture
def handler_with_file(tmp_path):
    def _create(content: str = "", file_name: str = "test_file.txt"):
        file_path = tmp_path / file_name
        file_path.write_text(content)
        return File(str(file_path)), file_path

    return _create
