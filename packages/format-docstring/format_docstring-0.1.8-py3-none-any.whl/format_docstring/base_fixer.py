from __future__ import annotations

import re
from pathlib import Path
from typing import Any


class BaseFixer:
    """Base class for fixing code formatting issues."""

    def __init__(
            self,
            path: str,
            exclude_pattern: str = r'\.git|\.tox|\.pytest_cache',
    ) -> None:
        """Initialize the fixer with a path and optional exclude pattern."""
        self.path = path
        self.exclude_pattern = exclude_pattern

    def _get_files_to_process(
            self, directory: Path, pattern: str
    ) -> list[Path]:
        """Get list of files to process, filtered by exclude pattern."""
        all_files = sorted(directory.rglob(pattern))
        return [
            f
            for f in all_files
            if not should_exclude_file(f, self.exclude_pattern)
        ]

    def fix_one_directory_or_one_file(self) -> int:
        """
        Fix formatting in a single file or all Python files in a directory.
        """
        path_obj = Path(self.path)

        if path_obj.is_file():
            if should_exclude_file(path_obj, self.exclude_pattern):
                return 0

            return self.fix_one_file(path_obj.as_posix())

        # Is a directory
        filenames = self._get_files_to_process(path_obj, '*.py')
        all_status = set()
        for filename in filenames:
            status = self.fix_one_file(filename.as_posix())
            all_status.add(status)

        return 0 if not all_status or all_status == {0} else 1

    def fix_one_file(self, *varargs: Any, **kwargs: Any) -> int:
        """Fix formatting in a single file."""
        raise NotImplementedError('Please implement this method')


def should_exclude_file(file_path: Path, exclude_pattern: str) -> bool:
    """Return True if `file_path` matches the provided exclude regex.

    If `exclude_pattern` is empty or invalid, no files are excluded.
    """
    if not exclude_pattern:
        return False

    try:
        exclude_regex = re.compile(exclude_pattern)
    except re.error:
        return False

    return bool(exclude_regex.search(file_path.as_posix()))
