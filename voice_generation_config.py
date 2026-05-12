#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AzureVoiceJob:
    csv_file: str
    voice: str
    langdir: str
    pitch: str | None = None
    rate: str | None = None

    @property
    def csv_path(self) -> Path:
        return Path(self.csv_file)


@dataclass(frozen=True)
class GladosVoiceJob:
    csv_file: str
    langdir: str

    @property
    def csv_path(self) -> Path:
        return Path(self.csv_file)


AZURE_VOICE_JOBS: tuple[AzureVoiceJob, ...] = (
    AzureVoiceJob("./voices/cs-CZ.csv", "cs-CZ-VlastaNeural", "cz"),
    AzureVoiceJob("./voices/da_DK.csv", "da-DK-ChristelNeural", "da"),
    AzureVoiceJob("./voices/da_DK_scripts.csv", "da-DK-ChristelNeural", "da/SCRIPTS"),
    AzureVoiceJob("./voices/de-DE.csv", "de-DE-KatjaNeural", "de"),
    AzureVoiceJob("./voices/en-GB.csv", "en-IE-EmilyNeural", "en", rate="1.10"),
    AzureVoiceJob("./voices/en-GB_scripts.csv", "en-IE-EmilyNeural", "en/SCRIPTS", rate="1.10"),
    AzureVoiceJob("./voices/en-GB.csv", "en-GB-LibbyNeural", "en_gb-libby"),
    AzureVoiceJob("./voices/en-GB_scripts.csv", "en-GB-LibbyNeural", "en_gb-libby/SCRIPTS"),
    AzureVoiceJob("./voices/en-GB.csv", "en-GB-RyanNeural", "en_gb-ryan"),
    AzureVoiceJob("./voices/en-GB_scripts.csv", "en-GB-RyanNeural", "en_gb-ryan/SCRIPTS"),
    AzureVoiceJob("./voices/en-US.csv", "en-US-GuyNeural", "en_us-guy"),
    AzureVoiceJob("./voices/en-US_scripts.csv", "en-US-GuyNeural", "en_us-guy/SCRIPTS"),
    AzureVoiceJob("./voices/en-US.csv", "en-US-MichelleNeural", "en_us-michelle"),
    AzureVoiceJob("./voices/en-US_scripts.csv", "en-US-MichelleNeural", "en_us-michelle/SCRIPTS"),
    AzureVoiceJob("./voices/en-US.csv", "en-US-SaraNeural", "en_us-sara"),
    AzureVoiceJob("./voices/en-US_scripts.csv", "en-US-SaraNeural", "en_us-sara/SCRIPTS"),
    AzureVoiceJob("./voices/es-CL.csv", "es-CL-CatalinaNeural", "es_cl-catalina"),
    AzureVoiceJob("./voices/es-ES.csv", "es-ES-ElviraNeural", "es"),
    AzureVoiceJob("./voices/fr-FR.csv", "fr-FR-DeniseNeural", "fr"),
    AzureVoiceJob("./voices/it-IT.csv", "it-IT-ElsaNeural", "it"),
    AzureVoiceJob("./voices/it-IT_scripts.csv", "it-IT-ElsaNeural", "it/SCRIPTS"),
    AzureVoiceJob("./voices/ja-JP.csv", "ja-JP-NanamiNeural", "jp"),
    AzureVoiceJob("./voices/ja-JP_scripts.csv", "ja-JP-NanamiNeural", "jp/SCRIPTS"),
    AzureVoiceJob("./voices/pt-PT.csv", "pt-BR-FranciscaNeural", "pt"),
    AzureVoiceJob("./voices/ru-RU.csv", "ru-RU-SvetlanaNeural", "ru"),
    AzureVoiceJob("./voices/sv-SE.csv", "sv-SE-SofieNeural", "se", pitch="dn10%", rate="0.9"),
    AzureVoiceJob("./voices/sv-SE_scripts.csv", "sv-SE-SofieNeural", "se/SCRIPTS", pitch="dn10%", rate="0.9"),
    AzureVoiceJob("./voices/uk-UA.csv", "uk-UA-OstapNeural", "ua-ostap"),
    AzureVoiceJob("./voices/uk-UA.csv", "uk-UA-PolinaNeural", "ua-polina"),
    AzureVoiceJob("./voices/zh-CN.csv", "zh-CN-XiaoxiaoNeural", "cn"),
    AzureVoiceJob("./voices/zh-TW.csv", "zh-TW-HsiaoChenNeural", "tw"),
    AzureVoiceJob("./voices/zh-HK.csv", "zh-HK-HiuGaaiNeural", "hk", rate="0.9"),
)


GLADOS_VOICE_JOBS: tuple[GladosVoiceJob, ...] = (
    GladosVoiceJob("./voices/en-GB.csv", "en_gb-glados"),
    GladosVoiceJob("./voices/en-GB_scripts.csv", "en_gb-glados/SCRIPTS"),
)
