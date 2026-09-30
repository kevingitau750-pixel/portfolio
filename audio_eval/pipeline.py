"""Glue: fetch audio -> transcribe -> align -> measure -> judge, per case."""

from __future__ import annotations

import hashlib
import shutil
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

from .acoustics import ClipFeatures, analyse, load_audio
from .alignment import Alignment, align
from .asr import NullTranscriber, Transcriber, Word
from .judge import Verdict, judge
from .sheet import Case

DEFAULT_CACHE = Path.home() / ".cache" / "audio_eval"


@dataclass
class ClipResult:
    source: str
    path: Path | None
    transcript: str = ""
    words: list[Word] = field(default_factory=list)
    alignment: Alignment | None = None
    features: ClipFeatures | None = None
    error: str | None = None


@dataclass
class CaseResult:
    case: Case
    a: ClipResult
    b: ClipResult
    verdict: Verdict | None
    error: str | None = None


def fetch_audio(source: str, row: int, side: str, audio_dir: Path | None, cache: Path) -> Path:
    """Local override first (``<audio_dir>/<row>_<side>.*``), then a local
    path in the cell, then download the URL (cached by URL hash)."""
    if audio_dir:
        hits = sorted(audio_dir.glob(f"{row}_{side}.*")) + sorted(audio_dir.glob(f"{row}_{side.lower()}.*"))
        if hits:
            return hits[0]
    if Path(source).expanduser().exists():
        return Path(source).expanduser()
    if not source.startswith(("http://", "https://")):
        raise FileNotFoundError(f"audio not found: {source}")
    cache.mkdir(parents=True, exist_ok=True)
    dest = cache / hashlib.sha1(source.encode()).hexdigest()[:16]
    if not dest.exists() or dest.stat().st_size == 0:
        req = urllib.request.Request(source, headers={"User-Agent": "audio-eval/0.1"})
        with urllib.request.urlopen(req, timeout=60) as resp, open(dest.with_suffix(".part"), "wb") as fh:
            shutil.copyfileobj(resp, fh)
        dest.with_suffix(".part").rename(dest)
    return dest


def analyse_clip(source: str, row: int, side: str, text: str, transcriber: Transcriber,
                 audio_dir: Path | None, cache: Path) -> ClipResult:
    res = ClipResult(source, None)
    try:
        res.path = fetch_audio(source, row, side, audio_dir, cache)
        y = load_audio(res.path)
        res.words = transcriber.transcribe(res.path)
        res.transcript = " ".join(w.text for w in res.words)
        res.alignment = align(text, res.words) if res.words else None
        res.features = analyse(y, text, res.words, res.alignment)
    except Exception as exc:  # keep going: one bad link must not sink the batch
        res.error = f"{type(exc).__name__}: {exc}"
    return res


def evaluate_case(case: Case, transcriber: Transcriber, audio_dir: Path | None = None,
                  cache: Path = DEFAULT_CACHE) -> CaseResult:
    a = analyse_clip(case.audio_a, case.row, "A", case.text, transcriber, audio_dir, cache)
    b = analyse_clip(case.audio_b, case.row, "B", case.text, transcriber, audio_dir, cache)
    if a.features is None or b.features is None:
        errs = "; ".join(f"Audio {s}: {r.error}" for s, r in (("A", a), ("B", b)) if r.error)
        return CaseResult(case, a, b, None, errs)
    asr_ok = not isinstance(transcriber, NullTranscriber)
    return CaseResult(case, a, b, judge(a.features, b.features, asr_available=asr_ok))


def analysis_rows(results: list[CaseResult]) -> list[dict]:
    """One row per clip for the 'Analysis' sheet."""
    rows = []
    for r in results:
        for side, clip in (("A", r.a), ("B", r.b)):
            f = clip.features
            row = {
                "sheet_row": r.case.row, "audio": side, "text": r.case.text,
                "whisper_transcript": clip.transcript,
                "word_error_rate": round(clip.alignment.wer, 3) if clip.alignment else None,
                "omissions": clip.alignment.count("del") if clip.alignment else None,
                "insertions": clip.alignment.count("ins") if clip.alignment else None,
                "misreadings": clip.alignment.count("sub") if clip.alignment else None,
            }
            row.update(f.as_row() if f else {})
            row["detected_issues"] = "\n".join(
                f"{e.detail}" + (f" @ {e.time:.1f}s" if e.time is not None else "")
                + (f" [{e.metric}]" if e.metric else "") for e in f.events) if f else ""
            row["penalty_total"] = round(sum(r.verdict.scores[side].values()), 2) if r.verdict else None
            row["error"] = clip.error
            rows.append(row)
    return rows
