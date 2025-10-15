import fnmatch
import os
import pathlib
import re
import uuid

from loguru import logger
from universal_mcp.applications.application import BaseApplication


class FileSystemApp(BaseApplication):
    """
    A class to safely interact with the filesystem within a specified working directory.
    """

    def __init__(self, working_dir: str | None = None, **kwargs):
        """
        Initializes the FileSystemApp with a working directory.

        Args:
            working_dir: The absolute path to the directory where all operations will be performed.
        """
        super().__init__(name="Filesystem")

        self.set_working_dir(working_dir or f"/tmp/{uuid.uuid4()}")

    def set_working_dir(self, working_dir: str):
        self.working_dir = pathlib.Path(working_dir).absolute()
        # Create dir if not exists
        self.working_dir.mkdir(parents=True, exist_ok=True)

    def _is_safe_path(self, path: str) -> bool:
        """
        Checks if the given path is within the working directory.

        Args:
            path: The path to check.

        Returns:
            True if the path is safe, False otherwise.
        """
        common_path = os.path.commonpath([self.working_dir, path])
        return common_path == str(self.working_dir)

    def create_file(self, path: str, content: str = "") -> None:
        """
        Creates a file with the given content.

        Args:
            path: The relative path to the file to create.
            content: The content to write to the file.

        Raises:
            ValueError: If the path is outside the working directory.
        """
        if not self._is_safe_path(path):
            error = f"Path is outside the working directory: {path} vs {self.working_dir}"
            logger.error(error)
            raise ValueError(error)

        full_path = os.path.join(self.working_dir, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w") as f:
            f.write(content)

    def read_file(self, path: str) -> str:
        """
        Reads the content of a file.

        Args:
            path: The relative path to the file to read.

        Returns:
            The content of the file.

        Raises:
            ValueError: If the path is outside the working directory.
            FileNotFoundError: If the file does not exist.
        """
        if not self._is_safe_path(path):
            raise ValueError("Path is outside the working directory.")

        full_path = os.path.join(self.working_dir, path)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {full_path}")

        with open(full_path) as f:
            return f.read()

    def list_files(self, path: str = ".", recursive: bool = False) -> list[str]:
        """
        Lists files in a directory.

        Args:
            path: The relative path to the directory to list.
            recursive: Whether to list files recursively.

        Returns:
            A list of file paths.

        Raises:
            ValueError: If the path is outside the working directory.
        """
        if not self._is_safe_path(path):
            raise ValueError("Path is outside the working directory.")

        full_path = os.path.join(self.working_dir, path)
        if not os.path.isdir(full_path):
            raise ValueError(f"Path '{path}' is not a directory.")

        files = []
        if recursive:
            for root, _, filenames in os.walk(full_path):
                for filename in filenames:
                    files.append(os.path.relpath(os.path.join(root, filename), self.working_dir))
        else:
            for item in os.listdir(full_path):
                item_path = os.path.join(full_path, item)
                if os.path.isfile(item_path):
                    files.append(os.path.relpath(item_path, self.working_dir))
        return files

    def grep(self, pattern: str, path: str = ".", file_pattern: str = "*") -> list[str]:
        """
        Searches for a pattern in files.

        Args:
            pattern: The regex pattern to search for.
            path: The relative path to the directory to search in.
            file_pattern: A glob pattern to filter files to search.

        Returns:
            A list of strings with "file:line_number:line" for each match.

        Raises:
            ValueError: If the path is outside the working directory.
        """
        if not self._is_safe_path(path):
            raise ValueError("Path is outside the working directory.")

        full_path = os.path.join(self.working_dir, path)
        if not os.path.isdir(full_path):
            raise ValueError(f"Path '{path}' is not a directory.")

        matches = []
        for root, _, filenames in os.walk(full_path):
            for filename in fnmatch.filter(filenames, file_pattern):
                file_path = os.path.join(root, filename)
                try:
                    with open(file_path, errors="ignore") as f:
                        for i, line in enumerate(f, 1):
                            if re.search(pattern, line):
                                relative_path = os.path.relpath(file_path, self.working_dir)
                                matches.append(f"{relative_path}:{i}:{line.strip()}")
                except OSError:
                    continue  # Skip files that can't be opened
        return matches

    def list_tools(self):
        return [self.create_file, self.grep, self.list_files, self.read_file]
