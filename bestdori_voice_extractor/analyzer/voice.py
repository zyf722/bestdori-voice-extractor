import os
from typing import Dict

# from bestdori_voice_extractor import console
from bestdori_voice_extractor.analyzer.base import BaseAnalyzer


class VoiceAnalyzer(BaseAnalyzer):
    """
    Analyzer for asset files.
    """
    data: Dict[str, str]

    def __init__(self) -> None:
        super().__init__()
        self.data = {}
    
    def _analyze(self, file_path: str):
        # console.print(f"Analyzing [yellow]{file_path}")
        self.data[os.path.splitext(os.path.basename(file_path))[0]] = file_path