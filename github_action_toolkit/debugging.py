import os

from .print_messages import group, info


def print_directory_tree(max_level: int = 3) -> None:
    """Print directory structure in a visually appealing tree format."""
    with group(f'DEBUG: Printing Directory Structure. CWD="{os.getcwd()}"'):
        startpath = os.getcwd()
        prefix_map = {"branch": "├── ", "last_branch": "└── ", "indent": "│   ", "empty": "    "}

        for root, dirs, files in os.walk(startpath):
            level = root.replace(startpath, "").count(os.sep)
            if level > max_level:
                continue

            # Sort directories and files for consistent output
            dirs.sort()
            files.sort()

            # Print directory name
            if level == 0:
                info(os.path.basename(root) + "/")
            else:
                # Create the prefix based on level
                indent = ""
                for _ in range(level - 1):
                    indent += prefix_map["indent"]

                is_last_dir = (
                    os.path.basename(root) == sorted(os.listdir(os.path.dirname(root)))[-1]
                )
                prefix = prefix_map["last_branch"] if is_last_dir else prefix_map["branch"]
                info(f"{indent}{prefix}{os.path.basename(root)}/")

            # Print files
            base_indent = prefix_map["indent"] * (level)
            for i, f in enumerate(files):
                is_last = i == len(files) - 1 and not dirs
                prefix = prefix_map["last_branch"] if is_last else prefix_map["branch"]
                info(f"{base_indent}{prefix}{f}")
