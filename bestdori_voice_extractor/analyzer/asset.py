import json
from dataclasses import dataclass
from typing import Dict, List

from bestdori_voice_extractor import console
from bestdori_voice_extractor.analyzer.base import BaseAnalyzer


@dataclass
class Asset:
    text: str
    voice_file: str

    def __json__(self):
        return {
            "text": self.text,
            "voice_file": self.voice_file
        }

class AssetDict:
    def __init__(self):
        self._data: Dict[int, List[Asset]] = {}
    
    def add(self, character_id: int, asset: Asset):
        if character_id in self._data:
            self._data[character_id].append(asset)
        else:
            self._data[character_id] = [asset]

    def __getitem__(self, character_id: int) -> List[Asset]:
        return self._data[character_id]
    
    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)
    
    def __json__(self):
        return self._data

class AssetAnalyzer(BaseAnalyzer):
    """
    Analyzer for asset files.
    """
    data: AssetDict

    def __init__(self) -> None:
        super().__init__()
        self.data = AssetDict()
    
    def _analyze(self, file_path: str):
        console.print(f"Analyzing [yellow]{file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            talks = json.load(f)["Base"]["talkData"]
            for talk in talks:
                # Remove newline characters
                text = talk["body"].replace("\n", "")
                for voice in talk["voices"]:
                    self.data.add(voice["characterId"], Asset(text, voice["voiceId"]))