import json
import yaml

__all__ = ['json', 'yaml']


class FileManager:
    def __init__(self, __manager):
        self._manager = __manager

    def loads(self, *args, **kwargs):
        return self._manager.loads(*args, **kwargs)

    def dumps(self, *args, **kwargs):
        return self._manager.dumps(*args, **kwargs)

    def load(self, file_path: str, *args, **kwargs):
        with open(file_path, 'r', encoding='utf-8') as f:
            return self._manager.load(f, *args, **kwargs)

    def dump(self, obj, file_path: str, *args, **kwargs):
        with open(file_path, 'w', encoding='utf-8') as f:
            self._manager.dump(obj, f, *args, **kwargs)

    def safe_load(self, file_path: str, *args, **kwargs):
        with open(file_path, 'r', encoding='utf-8') as f:
            return self._manager.safe_load(f, *args, **kwargs)

    def safe_dump(self, obj, file_path: str, *args, **kwargs):
        with open(file_path, 'w', encoding='utf-8') as f:
            self._manager.safe_dump(obj, f, *args, **kwargs)


json = FileManager(json)
yaml = FileManager(yaml)
