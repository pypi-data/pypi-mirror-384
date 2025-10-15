from enum import Enum
from typing import Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class TTSModel(str, Enum):
    SSFM_V21 = "ssfm-v21"


class LanguageCode(str, Enum):
    """ISO 639-3 language codes supported by Typecast API"""

    ENG = "eng"  # English
    KOR = "kor"  # Korean
    SPA = "spa"  # Spanish
    DEU = "deu"  # German
    FRA = "fra"  # French
    ITA = "ita"  # Italian
    POL = "pol"  # Polish
    NLD = "nld"  # Dutch
    RUS = "rus"  # Russian
    JPN = "jpn"  # Japanese
    ELL = "ell"  # Greek
    TAM = "tam"  # Tamil
    TGL = "tgl"  # Tagalog
    FIN = "fin"  # Finnish
    ZHO = "zho"  # Chinese
    SLK = "slk"  # Slovak
    ARA = "ara"  # Arabic
    HRV = "hrv"  # Croatian
    UKR = "ukr"  # Ukrainian
    IND = "ind"  # Indonesian
    DAN = "dan"  # Danish
    SWE = "swe"  # Swedish
    MSA = "msa"  # Malay
    CES = "ces"  # Czech
    POR = "por"  # Portuguese
    BUL = "bul"  # Bulgarian
    RON = "ron"  # Romanian


class Prompt(BaseModel):
    emotion_preset: Optional[str] = Field(
        default="normal",
        description="Emotion preset",
        examples=["normal", "happy", "sad", "angry"],
    )
    emotion_intensity: Optional[float] = Field(default=1.0, ge=0.0, le=2.0)


class Output(BaseModel):
    volume: Optional[int] = Field(default=100, ge=0, le=200)
    audio_pitch: Optional[int] = Field(default=0, ge=-12, le=12)
    audio_tempo: Optional[float] = Field(default=1.0, ge=0.5, le=2.0)
    audio_format: Optional[str] = Field(
        default="wav", description="Audio format", examples=["wav", "mp3"]
    )


class TTSRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"exclude_none": True})

    voice_id: str = Field(
        description="Voice ID", examples=["tc_62a8975e695ad26f7fb514d1"]
    )
    text: str = Field(description="Text", examples=["Hello. How are you?"])
    model: TTSModel = Field(description="Voice model name", examples=["ssfm-v21"])
    language: Optional[Union[LanguageCode, str]] = Field(
        None, description="Language code (ISO 639-3)", examples=["eng"]
    )
    prompt: Optional[Prompt] = None
    output: Optional[Output] = None
    seed: Optional[int] = None


class TTSResponse(BaseModel):
    audio_data: bytes
    duration: float
    format: str = "wav"
