import os
import pathlib

from .print_messages import debug


class File:
    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        self.content = self.read_content()

    def word_replacement(self, word_replacement_dict=dict()) -> str | None:
        if not self.content:
            return self.content

        for word, replacement in word_replacement_dict.items():
            self.content = self.content.replace(word, replacement)
        return self.content

    def read_content(self, input_file_path: str | None = None) -> str | None:
        if not input_file_path:
            input_file_path = self.file_path
        with open(input_file_path, "r") as fr:
            return fr.read()

    def write_content(
        self, content: str | None = None, output_file_path: str | None = None
    ) -> bool:
        if output_file_path:
            output_dir_path = os.path.dirname(output_file_path)
            pathlib.Path(output_dir_path).mkdir(parents=True, exist_ok=True)
        else:
            output_file_path = self.file_path

        if not content:
            content = self.content

        if content is None:
            return False  # No content to write

        with open(output_file_path, "w") as fw:
            fw.write(content)
        return True

    def write_content_part(
        self,
        content_part: str,
        start_markers: list[str],
        end_markers: list[str],
        start_marker_to_add: str = "",
        end_marker_to_add: str = "",
        output_file_path: str | None = None,
    ) -> bool:
        if not output_file_path:
            output_file_path = self.file_path

        content = ""
        lower_content = ""
        start_index = -1
        end_index = -1

        with open(output_file_path, "r") as file:
            content = file.read()
            lower_content = content.lower()

        for sm in start_markers:
            start_index = lower_content.find(sm.lower())
            if start_index >= 0:
                start_index += len(sm)
                break

        if start_index > 0:
            for em in end_markers:
                end_index = lower_content.find(em.lower(), start_index)
                if end_index >= 0:
                    break

        if start_index >= 0:
            # Content found
            if end_index < 0:
                end_index = len(lower_content) - 1

            debug(f"Found start_index={start_index}, end_index={end_index}")

            updated_content = content[:start_index] + content_part + content[end_index:]

        else:
            # Content not found in the file
            updated_content = content + start_marker_to_add + content_part + end_marker_to_add

        if updated_content != content:
            with open(output_file_path, "w") as fw:
                fw.write(updated_content)
            return True

        return False
