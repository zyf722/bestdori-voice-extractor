import os
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Tuple

import requests

from bestdori_voice_extractor import console
from bestdori_voice_extractor.config import (
    CURRENT_LOCALE,
    MAX_RETRY,
    MAX_WORKERS,
    PROXY,
)
from bestdori_voice_extractor.downloader import load


class BaseTraverseDownloader(ABC):
    """
    Base class for downloaders.
    """

    dir_executor: ThreadPoolExecutor
    save_path: str
    skip_list: List[Tuple[Tuple[str, ...], str]]

    @staticmethod
    @abstractmethod
    def EXTENSION_TYPE() -> str:
        raise NotImplementedError
    
    @staticmethod
    @abstractmethod
    def ENTRYPOINT() -> Tuple[Dict, Tuple[str, ...], str]:
        raise NotImplementedError

    def __init__(self, save_path: str, skip_list: List[Tuple[Tuple[str, ...], str]]):
        self.dir_executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
        self.save_path = save_path
        self.skip_list = skip_list

    @staticmethod
    def download(url: str, save_path: str):
        with open(save_path, "wb") as f:
            f.write(requests.get(url, proxies=PROXY).content)

    def _download(self, prefix: Tuple[str, ...], directory: str, asset: str):
        download_path = f"{self.save_path}/{'/'.join(prefix)}/{directory}/{asset}"
        console.print(f"Downloading to [yellow]{download_path}[/] ...")
        for _ in range(MAX_RETRY):
            try:
                self.download(f"https://bestdori.com/assets/{CURRENT_LOCALE}/{'/'.join(prefix)}/{directory}_rip/{asset}", download_path)
                break
            except Exception as e:
                console.print(f"[red]Failed to download {asset}[/]: {e}")

    def _process(self, prefix: Tuple[str, ...], directory: str, asset: str):
        asset_list: List[str] = load(f"https://bestdori.com/api/explorer/{CURRENT_LOCALE}/assets/{'/'.join(prefix)}/{directory}.json")
        os.makedirs(f"{self.save_path}/{'/'.join(prefix)}/{directory}", exist_ok=True)
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            for asset in asset_list:
                if asset.endswith(self.EXTENSION_TYPE()):
                    executor.submit(self._download, prefix, directory, asset)
    
    def walk(self, parent: Dict, prefix: Tuple[str, ...], asset_name: str):
        if (prefix, asset_name) in self.skip_list:
            return

        if asset_name in parent:
            if isinstance(parent[asset_name], dict):
                for k in parent[asset_name].keys():
                    self.walk(parent[asset_name], (*prefix, asset_name), k)
            else:
                self.dir_executor.submit(self._process, prefix, asset_name, parent[asset_name])

    def run(self):
        console.print("[yellow bold]Launching download...")
        if not os.path.exists(self.save_path):
            console.print(f"[yellow]Creating [bold]{self.save_path}[/] directory...")
            os.mkdir(self.save_path)
            self.walk(*self.ENTRYPOINT())
        else:
            console.print(f"[yellow]Directory [bold]{self.save_path}[/] already exists, skipping...")
        console.print("[yellow]Shutting down executor...")
        self.dir_executor.shutdown()
        console.print("[green bold]Download complete!")