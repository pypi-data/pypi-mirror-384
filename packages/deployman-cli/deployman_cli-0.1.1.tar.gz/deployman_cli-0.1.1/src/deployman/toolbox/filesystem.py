import os

from click import Path


class FileSystem:
    def read_file(self, path: Path) -> str:
        with open(path, 'r') as file:
            return file.read()

    def write_file(self, path: Path, content: str) -> None:
        with open(path, 'w') as file:
            file.write(content) 

    def dirname(self, path: Path) -> str:
        return os.path.dirname(str(path))
