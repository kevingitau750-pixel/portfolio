"""TTS A/B listening-test assistant.

Reads an "Audio Evaluation" workbook (text, Audio_A, Audio_B columns),
analyses each audio pair automatically (Whisper transcription + acoustic
measurements), drafts the Preference / Reason / Comments answers, and writes
a completed workbook plus a cross-case summary. A human reviewer is expected to
listen and confirm or override the drafts — see ``audio_eval/README.md``.
"""

__version__ = "0.1.0"
