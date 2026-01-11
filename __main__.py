from bestdori_voice_extractor.analyzer.asset import AssetAnalyzer
from bestdori_voice_extractor.analyzer.voice import VoiceAnalyzer
from bestdori_voice_extractor.downloader.asset import AssetDownloader
from bestdori_voice_extractor.downloader.voice import VoiceDownloader
from bestdori_voice_extractor.merger import AssetMerger

if __name__ == "__main__":
    # Step 1: Download assets
    asset_downloader = AssetDownloader("assets")
    asset_downloader.run()

    # Step 2: Download voices
    voice_downloader = VoiceDownloader("voices")
    voice_downloader.run()

    # Step 3: Analyze assets
    asset_analyzer = AssetAnalyzer()
    asset_analyzer.run("assets", "asset.json")

    # Step 4: Analyze voices
    voice_analyzer = VoiceAnalyzer()
    voice_analyzer.run("voices", "voice.json")