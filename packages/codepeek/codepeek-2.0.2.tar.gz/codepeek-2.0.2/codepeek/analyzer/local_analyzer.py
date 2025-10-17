import os
import json
from pathlib import Path
from codepeek.constants import CODE_EXTENSIONS, IGNORE_PATTERNS
from codepeek.utils import get_file_size_mb, is_binary_file


class LocalAnalyzer:
    def __init__(self, project_path: str):
        self.root_path = Path(project_path)

    def _should_ignore(self, path: Path) -> bool:
        path_str = str(path).lower()
        name = path.name.lower()
        for pattern in IGNORE_PATTERNS:
            if pattern in path_str or pattern in name:
                return True
        return False

    def generate_summary(self) -> dict:
        summary = {"files": []}

        for folder_path, _, files in os.walk(self.root_path):
            current = Path(folder_path)
            if self._should_ignore(current):
                continue

            for file in files:
                file_path = current / file
                if self._should_ignore(file_path):
                    continue

                ext = file_path.suffix.lower()
                if ext not in CODE_EXTENSIONS:
                    continue

                file_info = {
                    "file": str(file_path.relative_to(self.root_path)),
                    "size_mb": get_file_size_mb(file_path),
                }

                if file_info["size_mb"] > 2.0 or is_binary_file(file_path):
                    file_info["content"] = ""
                else:
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            file_info["content"] = f.read()[:4000]  # limit for API
                    except Exception as e:
                        file_info["content"] = f"Error reading file: {e}"

                summary["files"].append(file_info)

        return summary
