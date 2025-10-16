import re
from pathlib import Path
from typing import Union


def has_handler_class(file_path: Union[str, Path], class_name: str) -> bool:
    pattern = re.compile(rf"(?m)^\s*class\s+{class_name}\s*(?:\([^)]*\))?\s*:")
    with open(file_path) as file:
        for line in file:
            if pattern.search(line):
                return True
    return False
