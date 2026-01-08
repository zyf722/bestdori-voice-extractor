import json
import os
import argparse
import requests
import platform
from typing import Set, Tuple, List, Dict
from concurrent.futures import ThreadPoolExecutor

from bestdori_voice_extractor.downloader import load, session
from bestdori_voice_extractor.downloader.voice import VoiceDownloader
from bestdori_voice_extractor.downloader.asset import AssetDownloader
from bestdori_voice_extractor.analyzer.asset import AssetAnalyzer
from bestdori_voice_extractor.analyzer.voice import VoiceAnalyzer
from bestdori_voice_extractor.merger import AssetMerger
from bestdori_voice_extractor.config import MAX_WORKERS, CURRENT_LOCALE
from bestdori_voice_extractor import console

# --- Helper Functions ---

def clear_screen():
    system = platform.system()
    if system == 'Windows':
        os.system('cls')
    else:
        os.system('clear')

# --- Character Metadata Handling ---

def fetch_character_metadata():
    """Fetches character data from Bestdori API."""
    url = "https://bestdori.com/api/characters/all.5.json"
    print("Fetching character list from Bestdori...")
    try:
        response = requests.get(url)
        response.encoding = 'utf-8' 
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Failed to fetch character data: {e}")
    return None

def get_band_name(band_id):
    bands = {
        1: "Poppin'Party",
        2: "Afterglow",
        3: "Hello, Happy World!",
        4: "Pastel*Palettes",
        5: "Roselia",
        18: "RAISE A SUILEN",
        21: "Morfonica",
        45: "MyGO!!!!!",
        0: "Others"
    }
    return bands.get(band_id, "Others")

def display_characters(char_data):
    if not char_data:
        print("No character data available.")
        return

    # Group by band
    grouped = {}
    for cid, data in char_data.items():
        # Filter out invalid entries if any
        if not isinstance(data, dict): continue
        
        band_id = data.get("bandId", 0)
        if band_id is None: band_id = 0
            
        if band_id not in grouped:
            grouped[band_id] = []
        grouped[band_id].append((cid, data))

    # Sort bands
    sorted_band_ids = sorted(grouped.keys())

    print(f"\n{'='*60}")
    print(f"Select a Character ID from the list below (or 'q' to exit):")
    print(f"{'='*60}")

    for band_id in sorted_band_ids:
        band_name = get_band_name(band_id)
        print(f"\n--- {band_name} (Band ID: {band_id}) ---")
        
        # Sort characters by ID within band
        chars = sorted(grouped[band_id], key=lambda x: int(x[0]))
        for cid, cdata in chars:
            names = cdata.get("characterName", [])
            # Safe access to names
            name_jp = names[0] if len(names) > 0 and names[0] else "???"
            name_en = names[1] if len(names) > 1 and names[1] else "-"
            name_cn = names[3] if len(names) > 3 and names[3] else "-"
            
            # Simple format: [ID] JP Name / EN Name / CN Name
            print(f"[{cid:>3}] {name_jp}  /  {name_en}  /  {name_cn}")
    print(f"\n{'='*60}\n")

# --- Selective Download Logic (Reuse) ---

class SelectiveVoiceDownloader(VoiceDownloader):
    def __init__(self, wanted_voices: Set[str], save_path: str = "voices"):
        super().__init__(save_path)
        self.wanted_voices = wanted_voices

    def _process(self, prefix: Tuple[str, ...], directory: str, asset: str):
        url = f"https://bestdori.com/api/explorer/{CURRENT_LOCALE}/assets/{'/'.join(prefix)}/{directory}.json"
        try:
            asset_list: List[str] = load(url)
        except Exception as e:
            console.print(f"[red]Failed to load list {url}: {e}")
            return

        os.makedirs(f"{self.save_path}/{'/'.join(prefix)}/{directory}", exist_ok=True)
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            for asset_file in asset_list:
                if asset_file.endswith(self.EXTENSION_TYPE()):
                    name_without_ext = os.path.splitext(asset_file)[0]
                    if name_without_ext in self.wanted_voices:
                        executor.submit(self._download, prefix, directory, asset_file)

# --- Main Logic ---

def mode_cloud_download(chara_id):
    console.print(f"\n[bold cyan]--- Mode: Cloud Download for ID {chara_id} ---[/]")
    
    # 1. Download Assets (Required to know what to download)
    console.print(f"[bold cyan]Step 1: Checking Assets (Scenarios)...[/]")
    AssetDownloader("assets").run()
    
    # 2. Analyze to find voices
    console.print(f"[bold cyan]Step 2: Analyzing Assets...[/]")
    AssetAnalyzer().run("assets", "asset.json")
    
    # 3. Filter
    with open("asset.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    if chara_id not in data:
        console.print(f"[red]Error: Character ID {chara_id} not found in assets analysis.[/]")
        return

    character_data = data[chara_id]
    wanted_voices = set()
    for line in character_data:
        wanted_voices.add(line["voice_file"])
    
    console.print(f"[green]Found {len(wanted_voices)} voice lines to download.[/]")
    
    # 4. Selective Download
    console.print(f"[bold cyan]Step 3: Downloading Specific Voice Files...[/]")
    downloader = SelectiveVoiceDownloader(wanted_voices, "voices")
    downloader.run()
    
    # 5. Analyze Voices
    console.print(f"[bold cyan]Step 4: Mapping Local Voice Files...[/]")
    VoiceAnalyzer().run("voices", "voice.json")
    
    # 6. Merge
    console.print(f"[bold cyan]Step 5: Merging into Zip...[/]")
    merger = AssetMerger(chara_id, "asset.json", "voice.json")
    merger.merge()
    console.print(f"[bold green]Success! Output saved to {chara_id}.zip[/]")

    # Clean up empty output folder if it exists
    if os.path.exists("output") and not os.listdir("output"):
        os.rmdir("output")

def mode_local_parse(chara_id):
    console.print(f"\n[bold cyan]--- Mode: Local Parse for ID {chara_id} ---[/]")
    
    if not os.path.exists("assets"):
        console.print("[red]Error: 'assets' folder not found. Cannot parse local files.[/]")
        return
    if not os.path.exists("voices"):
        console.print("[red]Error: 'voices' folder not found. Cannot parse local files.[/]")
        return

    # Check for existing JSONs to save time, but offer rebuild
    skip_analysis = False
    if os.path.exists("asset.json") and os.path.exists("voice.json"):
        choice = input("Found existing asset.json and voice.json. Reuse them? (Y/n): ").strip().lower()
        if choice in ['', 'y', 'yes']:
            skip_analysis = True
            console.print("[green]Reusing existing analysis files.[/]")
        else:
            console.print("[yellow]Re-analyzing local files...[/]")

    if not skip_analysis:
        # Re-analyze ensures we catch all currently present files
        console.print(f"[bold cyan]Step 1: Analyzing Local Assets...[/]")
        AssetAnalyzer().run("assets", "asset.json")
        
        console.print(f"[bold cyan]Step 2: Analyzing Local Voices (This may take a while if you have many files)...[/]")
        VoiceAnalyzer().run("voices", "voice.json")
    
    console.print(f"[bold cyan]Step 3: Merging...[/]")
    # Check if char exists
    with open("asset.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        if chara_id not in data:
            console.print(f"[red]Error: Character ID {chara_id} has no lines in the local assets.[/]")
            return

    merger = AssetMerger(chara_id, "asset.json", "voice.json")
    merger.merge()
    console.print(f"[bold green]Success! Output saved to {chara_id}.zip[/]")

    # Clean up empty output folder if it exists
    if os.path.exists("output") and not os.listdir("output"):
        os.rmdir("output")

def main():
    # 1. Load Data Once
    char_data = fetch_character_metadata()
    if not char_data:
        console.print("[yellow]Could not fetch character list. Please use known ID.[/]")
    
    while True:
        clear_screen()
        if char_data:
            display_characters(char_data)
        
        # 2. Select Character
        selected_id = input("\nEnter Character ID to extract (or 'q' to quit): ").strip()
        if selected_id.lower() in ['q', 'quit', 'exit']:
            print("Exiting...")
            break
        
        if not selected_id:
            continue

        # 3. Select Mode
        print("\nSelect Mode:")
        print("1. [Cloud] Download & Extract (Downloads only needed files)")
        print("2. [Local] Parse & Extract (Uses existing files in 'assets' and 'voices')")
        mode = input("Choice (1/2): ").strip()

        if mode == "1":
            mode_cloud_download(selected_id)
        elif mode == "2":
            mode_local_parse(selected_id)
        else:
            print("Invalid choice. Please try again.")
            input("\nPress Enter to continue...")
            continue
        
        input("\nMission Complete! Press Enter to return to menu...")

if __name__ == "__main__":
    main()