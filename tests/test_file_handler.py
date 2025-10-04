import pytest

from github_action_toolkit.file_handler import File


def test_read_content(handler_with_file):
    handler, file_path = handler_with_file("Hello, world!")
    assert handler.read_content() == "Hello, world!"


def test_word_replacement(handler_with_file):
    handler, _ = handler_with_file("Hello, world!")
    replaced = handler.word_replacement({"world": "universe"})
    assert replaced == "Hello, universe!"


def test_write_content_overwrites_file(handler_with_file):
    handler, file_path = handler_with_file("Old content")
    handler.content = "New content"
    result = handler.write_content()
    assert result is True
    assert file_path.read_text() == "New content"


def test_write_content_to_custom_path(tmp_path, handler_with_file):
    handler, _ = handler_with_file("Unused")
    output_file = tmp_path / "subdir" / "output.txt"
    result = handler.write_content(content="Updated!", output_file_path=str(output_file))
    assert result is True
    assert output_file.read_text() == "Updated!"


def test_write_content_part_found(handler_with_file):
    initial = "Header\nStart\nOld content\nEnd\nFooter"
    handler, file_path = handler_with_file(initial)
    result = handler.write_content_part(
        "New content", start_markers=["Start\n"], end_markers=["End\n"]
    )
    assert result is True
    assert file_path.read_text() == "Header\nStart\nNew content\nEnd\nFooter"


def test_write_content_part_not_found_adds_new(handler_with_file):
    handler, file_path = handler_with_file("Initial content")
    result = handler.write_content_part(
        "Inserted",
        start_markers=["XX"],
        end_markers=["YY"],
        start_marker_to_add="\nXX",
        end_marker_to_add="YY\n",
    )
    assert result is True
    assert "XXInsertedYY" in file_path.read_text()


def test_write_content_part_no_change(handler_with_file):
    initial = "Header\nStart\nExact content\nEnd\nFooter"
    handler, file_path = handler_with_file(initial)
    result = handler.write_content_part(
        "Exact content",
        start_markers=["Start\n"],
        end_markers=["End\n"],
        start_marker_to_add="\n",
        end_marker_to_add="\n",
    )
    assert result is False


def test_write_content_part_file_not_exist(tmp_path):
    file_path = tmp_path / "missing.txt"
    with pytest.raises(FileNotFoundError):
        handler = File(str(file_path))
        handler.write_content_part("data", ["Start"], ["End"])
