# Typecast Python SDK

Python SDK for Typecast API integration. Convert text to lifelike speech using AI-powered voices with emotion, pitch, and tempo control.

For comprehensive API documentation, visit [Typecast Documentation](https://typecast.ai/docs/overview).

## Installation

```bash
pip install typecast-python
```

## Quick Start

```python
from typecast.client import Typecast
from typecast.models import TTSRequest

# Initialize client
cli = Typecast(api_key="YOUR_API_KEY")

# Convert text to speech
response = cli.text_to_speech(TTSRequest(
    text="Hello there! I'm your friendly text-to-speech agent.",
    model="ssfm-v21",
    voice_id="tc_62a8975e695ad26f7fb514d1"
))

# Save audio file
with open('output.wav', 'wb') as f:
    f.write(response.audio_data)

print(f"Duration: {response.duration}s, Format: {response.format}")
```

## Features

- 🎙️ **Multiple Voice Models**: Support for various AI voice models (ssfm-v21, v20, etc.)
- 🌍 **Multi-language Support**: 27+ languages including English, Korean, Spanish, Japanese, Chinese, and more
- 😊 **Emotion Control**: Adjust emotional expression (happy, sad, angry, normal) with intensity control
- 🎚️ **Audio Customization**: Control volume, pitch, tempo, and output format (WAV/MP3)
- ⚡ **Async Support**: Built-in async client for high-performance applications
- 🔍 **Voice Discovery**: List and search available voices by model

## Advanced Usage

### Emotion and Audio Control

```python
from typecast.client import Typecast
from typecast.models import TTSRequest, Prompt, Output

cli = Typecast()

response = cli.text_to_speech(TTSRequest(
    text="I am so excited to show you these features!",
    model="ssfm-v21",
    voice_id="tc_62a8975e695ad26f7fb514d1",
    language="eng",
    prompt=Prompt(
        emotion_preset="happy",      # Options: normal, happy, sad, angry
        emotion_intensity=1.5        # Range: 0.0 to 2.0
    ),
    output=Output(
        volume=120,                  # Range: 0 to 200
        audio_pitch=2,               # Range: -12 to +12 semitones
        audio_tempo=1.2,             # Range: 0.5x to 2.0x
        audio_format="mp3"           # Options: wav, mp3
    ),
    seed=42                          # For reproducible results
))
```

### Voice Discovery

```python
# List all voices
voices = cli.voices()

# Filter by model
v21_voices = cli.voices(model="ssfm-v21")

# Get specific voice
voice = cli.get_voice("tc_62a8975e695ad26f7fb514d1")
print(f"Voice: {voice.voice_name}")
print(f"Available emotions: {voice.emotions}")
```

### Async Client

```python
import asyncio
from typecast.async_client import AsyncTypecast
from typecast.models import TTSRequest, LanguageCode

async def main():
    async with AsyncTypecast() as cli:
        response = await cli.text_to_speech(TTSRequest(
            text="Hello from async!",
            model="ssfm-v21",
            voice_id="tc_62a8975e695ad26f7fb514d1",
            language=LanguageCode.ENG
        ))
        
        with open('async_output.wav', 'wb') as f:
            f.write(response.audio_data)

asyncio.run(main())
```

## Supported Languages

The SDK supports 27 languages with ISO 639-3 codes:

| Language | Code | Language | Code | Language | Code |
|----------|------|----------|------|----------|------|
| English | `eng` | Japanese | `jpn` | Ukrainian | `ukr` |
| Korean | `kor` | Greek | `ell` | Indonesian | `ind` |
| Spanish | `spa` | Tamil | `tam` | Danish | `dan` |
| German | `deu` | Tagalog | `tgl` | Swedish | `swe` |
| French | `fra` | Finnish | `fin` | Malay | `msa` |
| Italian | `ita` | Chinese | `zho` | Czech | `ces` |
| Polish | `pol` | Slovak | `slk` | Portuguese | `por` |
| Dutch | `nld` | Arabic | `ara` | Bulgarian | `bul` |
| Russian | `rus` | Croatian | `hrv` | Romanian | `ron` |

Use the `LanguageCode` enum for type-safe language selection:

```python
from typecast.models import LanguageCode

request = TTSRequest(
    text="Hello",
    language=LanguageCode.ENG,
    ...
)
```

## Error Handling

The SDK provides specific exceptions for different HTTP status codes:

```python
from typecast.exceptions import (
    BadRequestError,           # 400
    UnauthorizedError,         # 401
    PaymentRequiredError,      # 402
    NotFoundError,             # 404
    UnprocessableEntityError,  # 422
    InternalServerError,       # 500
    TypecastError              # Base exception
)

try:
    response = cli.text_to_speech(request)
except UnauthorizedError:
    print("Invalid API key")
except PaymentRequiredError:
    print("Insufficient credits")
except TypecastError as e:
    print(f"Error: {e.message}, Status: {e.status_code}")
```

## Examples

Check out the [examples](./examples) directory for more usage examples:

- [`simple.py`](./examples/simple.py) - Basic text-to-speech conversion
- [`advanced.py`](./examples/advanced.py) - Emotion, pitch, and tempo control
- [`voices_example.py`](./examples/voices_example.py) - Discovering available voices
- [`async_example.py`](./examples/async_example.py) - Async client usage

## Configuration

Set your API key via environment variable or constructor:

```bash
export TYPECAST_API_KEY="your-api-key-here"
```

```python
# From environment variable
cli = Typecast()

# Or pass directly
cli = Typecast(api_key="your-api-key-here")

# Custom host (optional)
cli = Typecast(host="https://custom-api.example.com")
```

## License

Apache License 2.0