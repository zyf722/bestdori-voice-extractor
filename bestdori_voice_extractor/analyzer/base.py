import json
import os
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor

from bestdori_voice_extractor import console
from bestdori_voice_extractor.config import MAX_WORKERS


def _dumper(obj):
    if "__json__" in dir(obj) and callable(obj.__json__):
        return obj.__json__()
    return obj.__dict__

def dumps(obj, *args, **kwargs):
    return json.dumps(obj, default=_dumper, *args, **kwargs)


class BaseAnalyzer(ABC):
    """
    Base class for analyzers.
    """
    data: object
    executor: ThreadPoolExecutor

    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)

    def walk(self, dir_path: str):
        """
        Walk through the directory and analyze the files.
        """
        for root, dirs, files in os.walk(dir_path):
            for dir in dirs:
                self.walk(dir)
            for file in files:
                file_path = os.path.join(root, file)
                self.executor.submit(self._analyze, file_path)

    @abstractmethod
    def _analyze(self, file_path: str):
        raise NotImplementedError
    
    def dump(self, file_path: str):
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(dumps(self.data, ensure_ascii=False, indent=4))
    
    def run(self, dir_path: str, file_path: str):
        console.print("[yellow bold]Launching analyzing...")
        self.walk(dir_path)
        console.print("[yellow]Shutting down executor...")
        self.executor.shutdown()
        self.dump(file_path)
        console.print("[green bold]Analyze complete!")
