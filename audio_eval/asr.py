"""Speech-to-text with word timestamps, via faster-whisper (free, runs locally).

The script text is deliberately NOT passed to Whisper as a prompt: that would
bias it towards "hearing" the correct words and hide the TTS mistakes we are
trying to catch.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass
class Word:
    text: str
    start: float
    end: float
    prob: float = 1.0


class Transcriber(Protocol):
    name: str

    def transcribe(self, audio_path: Path) -> list[Word]: ...


class WhisperTranscriber:
    """faster-whisper wrapper. Model weights download once from Hugging Face
    (~250 MB for small.en) and are cached in ~/.cache/huggingface."""

    def __init__(self, model: str = "small.en", device: str = "auto", compute_type: str = "int8"):
        from faster_whisper import WhisperModel  # imported lazily: heavy

        self.name = f"whisper-{model}"
        self._model = WhisperModel(model, device=device, compute_type=compute_type)

    def transcribe(self, audio_path: Path) -> list[Word]:
        segments, _ = self._model.transcribe(
            str(audio_path),
            language="en",
            beam_size=5,
            temperature=0.0,
            word_timestamps=True,
            condition_on_previous_text=False,
            vad_filter=False,  # keep noise / odd gaps visible to the analysis
        )
        return [Word(w.word.strip(), float(w.start), float(w.end), float(w.probability))
                for seg in segments for w in (seg.words or []) if w.word.strip()]


class NullTranscriber:
    """Used when Whisper is unavailable: skips the word-accuracy checks."""

    name = "none"

    def transcribe(self, audio_path: Path) -> list[Word]:
        return []
