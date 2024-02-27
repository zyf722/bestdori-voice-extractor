from typing import Dict, List, Tuple

from bestdori_voice_extractor.downloader import bestdori_info
from bestdori_voice_extractor.downloader.base import BaseTraverseDownloader


class AssetDownloader(BaseTraverseDownloader):
    """
    Asset downloader.
    """

    def __init__(self, save_path: str = "assets", skip_list: List[Tuple[Tuple[str, ...], str]] = [
            (("scenario", ), "effects")
        ]):
        super().__init__(save_path, skip_list)

    @staticmethod
    def EXTENSION_TYPE() -> str:
        return ".asset"

    @staticmethod
    def ENTRYPOINT() -> Tuple[Dict, Tuple[str, ...], str]:
        return bestdori_info, (), "scenario"