import json
import os
import shutil
from typing import Dict, List
from zipfile import ZipFile

from bestdori_voice_extractor import console
from bestdori_voice_extractor.config import CURRENT_LOCALE


class AssetMerger:
    chara_id: str
    lines: List[Dict[str, str]]
    voices: Dict[str, str]

    def __init__(self, chara_id: str, asset_json_path: str, voice_json_path: str):
        self.chara_id = str(chara_id)

        with open(asset_json_path, "r", encoding="utf-8") as f:
            self.lines = json.load(f)[chara_id]
        
        with open(voice_json_path, "r", encoding="utf-8") as f:
            self.voices = json.load(f)
    
    def merge(self):
        os.makedirs(f"output/{self.chara_id}", exist_ok=True)
        os.chdir(f"output/{self.chara_id}")
        with open(f"{self.chara_id}.list", mode="w", encoding="utf-8") as f:
            for line in self.lines:
                if line['voice_file'] in self.voices:
                    shutil.copyfile(f"../../{self.voices[line['voice_file']]}", f"{line['voice_file']}.mp3")
                    f.write(f"{line['voice_file']}.mp3|{self.chara_id}|{CURRENT_LOCALE}|{line['text']}\n")
                    console.print(f"{line['voice_file']}.mp3|{self.chara_id}|{CURRENT_LOCALE}|{line['text']}")
                else:
                    console.print(f"Voice file [yellow]{line['voice_file']}[/] not found. Skipping...")
        
        # Zip output/chara_id folder
        with ZipFile(f"../../{self.chara_id}.zip", "w") as zipf:
            for root, dirs, files in os.walk("."):
                for file in files:
                    zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), "."))
        
        # Clean up
        os.chdir("../")
        shutil.rmtree(self.chara_id)
        os.chdir("../")


    