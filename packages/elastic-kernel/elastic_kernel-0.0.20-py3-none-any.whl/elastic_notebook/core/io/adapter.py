from pathlib import Path


class Adapter:
    def __init__(self):
        pass

    def read_all(self, path: Path):
        raise NotImplementedError()

    def create(self, path: Path):
        raise NotImplementedError()

    def write_all(self, path: Path, buf):
        raise NotImplementedError()

    def remove(self, path: Path):
        raise NotImplementedError()
