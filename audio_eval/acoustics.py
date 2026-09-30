"""Signal-level measurements for one clip: pauses, speaking rate, pitch
movement, noise, clipping, dropouts, loudness / timbre consistency.

Every threshold lives in ``THRESHOLDS`` so it can be tuned in one place.
Everything that looks like a defect is also recorded as an ``Event`` with a
timestamp, so the drafted comment can say *where* the problem is.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from .alignment import Alignment
from .asr import Word

SR = 16000
HOP = 160          # 10 ms
WIN = 400          # 25 ms

THRESHOLDS = {
    "speech_db_above_floor": 12.0,  # frame counts as speech this far above the noise floor…
    "speech_db_below_peak": 45.0,   # …and no further than this below the loudest frame
    "min_pause_s": 0.15,
    "unnatural_pause_s": 0.40,      # silence mid-phrase (no punctuation) longer than this
    "long_pause_s": 1.20,           # any pause longer than this
    "rushed_boundary_s": 0.06,      # sentence end (. ! ?) followed by less silence than this
    "rate_slow_wps": 2.0,           # words per second of speech
    "rate_fast_wps": 3.8,
    "flat_pitch_st": 1.8,           # std of pitch in semitones below this = monotone
    "wild_pitch_st": 6.0,           # above this = erratic
    "pitch_jump_st": 7.0,           # frame-to-frame jump that sounds like a glitch
    "noisy_snr_db": 30.0,
    "noisy_floor_db": -55.0,
    "clip_ratio": 1e-4,
    "burst_db": 15.0,               # short burst above floor inside a pause = click/pop
    "dropout_db": 25.0,             # sudden energy hole inside speech
    "loudness_std_db": 6.0,
    "fade_db": 6.0,                 # last third vs first third
    "centroid_drift": 0.25,         # relative change in spectral centroid (timbre)
    "min_drift_speech_s": 2.0,      # fade / timbre drift only judged on clips at least this long
    "low_conf_prob": 0.45,          # Whisper word probability below this = unclear word
    "flat_emphasis_db": 1.5,
    "edge_silence_s": 0.03,         # less than this at the end = likely cut off
}


@dataclass
class Event:
    kind: str            # key used by judge.py to map to a reason dimension
    time: float | None   # None = applies to the whole clip
    detail: str          # plain-English, used in the drafted comment
    severity: float = 1.0
    metric: str = ""     # the measurement behind it, shown in the Analysis sheet


@dataclass
class ClipFeatures:
    duration: float = 0.0
    speech_start: float = 0.0
    speech_end: float = 0.0
    words_per_sec: float | None = None
    pitch_std_st: float | None = None
    pitch_jumps: int = 0
    noise_floor_db: float = 0.0
    snr_db: float = 0.0
    clip_ratio: float = 0.0
    loudness_std_db: float = 0.0
    fade_db: float = 0.0
    centroid_drift: float = 0.0
    emphasis_std_db: float | None = None
    mean_word_prob: float | None = None
    pauses: list[tuple[float, float]] = field(default_factory=list)
    events: list[Event] = field(default_factory=list)

    def as_row(self) -> dict:
        r = lambda v, n=2: None if v is None else round(float(v), n)  # noqa: E731
        return {
            "duration_s": r(self.duration), "speech_start_s": r(self.speech_start),
            "speech_end_s": r(self.speech_end), "words_per_sec": r(self.words_per_sec),
            "pitch_std_semitones": r(self.pitch_std_st), "pitch_glitches": self.pitch_jumps,
            "noise_floor_db": r(self.noise_floor_db, 1), "snr_db": r(self.snr_db, 1),
            "clipping_ratio": r(self.clip_ratio, 6), "loudness_std_db": r(self.loudness_std_db),
            "fade_db": r(self.fade_db), "timbre_drift": r(self.centroid_drift, 3),
            "emphasis_std_db": r(self.emphasis_std_db), "mean_word_conf": r(self.mean_word_prob, 3),
            "pauses": ", ".join(f"{fmt_time(s)} ({d:.2f}s)" for s, d in self.pauses),
        }


def fmt_time(t: float) -> str:
    m, s = divmod(max(0.0, t), 60)
    return f"{int(m)}:{s:04.1f}"


def load_audio(path: Path) -> np.ndarray:
    import librosa

    y, _ = librosa.load(str(path), sr=SR, mono=True)
    return y.astype(np.float32)


def _runs(mask: np.ndarray) -> list[tuple[int, int]]:
    """[start, end) index pairs of consecutive True values."""
    if not mask.any():
        return []
    padded = np.concatenate([[False], mask, [False]])
    diff = np.flatnonzero(np.diff(padded.astype(np.int8)))
    return list(zip(diff[::2], diff[1::2]))


def _boundary_words(script: str) -> tuple[set[str], set[str]]:
    """Script words followed by a comma-like mark / a sentence-ending mark."""
    commas, stops = set(), set()
    for m in re.finditer(r"([A-Za-z0-9$']+)\s*([,;:\-–—]|[.!?]+)(?=\s|$)", script):
        target = stops if m.group(2)[0] in ".!?" else commas
        target.add(m.group(1).lower().strip("$"))
    return commas, stops


def analyse(y: np.ndarray, script: str, words: list[Word], alignment: Alignment | None) -> ClipFeatures:
    import librosa

    T = THRESHOLDS
    f = ClipFeatures(duration=len(y) / SR)
    if len(y) < WIN:
        f.events.append(Event("empty", None, "the audio is empty or too short", 3.0))
        return f

    rms = librosa.feature.rms(y=y, frame_length=WIN, hop_length=HOP)[0]
    db = 20 * np.log10(np.maximum(rms, 1e-6))
    times = librosa.frames_to_time(np.arange(len(db)), sr=SR, hop_length=HOP)
    floor = float(np.percentile(db, 10))
    peak = float(db.max())
    thresh = max(floor + T["speech_db_above_floor"], peak - T["speech_db_below_peak"])
    speech = db > thresh
    f.noise_floor_db = floor

    if not speech.any():
        f.events.append(Event("empty", None, "there is no audible speech", 3.0))
        return f

    idx = np.flatnonzero(speech)
    f.speech_start, f.speech_end = float(times[idx[0]]), float(times[idx[-1]] + WIN / SR)
    f.snr_db = float(np.median(db[speech]) - floor)

    # --- edges -----------------------------------------------------------
    if f.duration - f.speech_end < T["edge_silence_s"]:
        f.events.append(Event("cutoff", f.speech_end, "the last word sounds cut off"))

    # --- pauses (energy based) --------------------------------------------
    inner = ~speech
    inner[: idx[0]] = False
    inner[idx[-1]:] = False
    for s, e in _runs(inner):
        dur = (e - s) * HOP / SR
        if dur >= T["min_pause_s"]:
            f.pauses.append((float(times[s]), dur))
            if dur >= T["long_pause_s"]:
                f.events.append(Event("long_pause", float(times[s]), f"there is an overlong {dur:.1f}s silence", 1.5))
        # short loud burst inside the pause = click / pop / breath artefact
        seg = db[s:e]
        for bs, be in _runs(seg > floor + T["burst_db"]):
            if (be - bs) <= 3 and (e - s) >= 10:
                f.events.append(Event("click", float(times[s + bs]), "there is a click/pop between words"))

    # --- dropouts inside speech -------------------------------------------
    for s, e in _runs(speech):
        seg = db[s:e]
        for i in range(2, len(seg) - 6):
            if seg[i - 2] - seg[i] > T["dropout_db"] and any(seg[i + k] - seg[i] > T["dropout_db"] for k in range(1, 6)):
                f.events.append(Event("dropout", float(times[s + i]), "the signal briefly drops out (glitch)"))
                break

    # --- noise, clipping ---------------------------------------------------
    f.clip_ratio = float(np.mean(np.abs(y) >= 0.999))
    if f.clip_ratio > T["clip_ratio"]:
        at = float(np.flatnonzero(np.abs(y) >= 0.999)[0] / SR)
        f.events.append(Event("clipping", at, "the audio is distorted by clipping", 1.5, f"{f.clip_ratio:.2%} of samples clipped"))
    if f.snr_db < T["noisy_snr_db"] or floor > T["noisy_floor_db"]:
        loud_gap = max(f.pauses, key=lambda p: p[1])[0] if f.pauses else None
        where = ", most noticeable between words" if f.pauses else ""
        f.events.append(Event("noise", loud_gap, f"there is audible background noise{where}", 1.0,
                              f"noise floor {floor:.0f} dB, SNR {f.snr_db:.0f} dB"))

    # --- loudness / timbre consistency ------------------------------------
    sp_db = db[speech]
    chunk = max(1, len(sp_db) // 8)
    chunk_means = [sp_db[i:i + chunk].mean() for i in range(0, len(sp_db) - chunk + 1, chunk)]
    f.loudness_std_db = float(np.std(chunk_means)) if len(chunk_means) > 1 else 0.0
    thirds = np.array_split(sp_db, 3)
    f.fade_db = float(thirds[0].mean() - thirds[-1].mean()) if len(sp_db) >= 30 else 0.0
    if f.loudness_std_db > T["loudness_std_db"]:
        f.events.append(Event("loudness", None, "the volume is uneven", 1.0, f"±{f.loudness_std_db:.1f} dB"))
    long_enough = (f.speech_end - f.speech_start) >= T["min_drift_speech_s"]
    if long_enough and abs(f.fade_db) > T["fade_db"]:
        word = "drops" if f.fade_db > 0 else "rises"
        f.events.append(Event("loudness", float(times[idx[len(idx) * 2 // 3]]), f"the volume {word} noticeably towards the end", 1.0, f"{abs(f.fade_db):.0f} dB"))
    cent = librosa.feature.spectral_centroid(y=y, sr=SR, n_fft=512, hop_length=HOP)[0][: len(speech)]
    cent_sp = np.array_split(cent[speech[: len(cent)]], 3)
    if len(cent_sp[0]) and len(cent_sp[-1]):
        a, b = np.median(cent_sp[0]), np.median(cent_sp[-1])
        f.centroid_drift = float(abs(b - a) / max(a, 1.0))
        if long_enough and f.centroid_drift > T["centroid_drift"]:
            f.events.append(Event("timbre", float(times[idx[len(idx) * 2 // 3]]), "the voice quality (timbre) shifts mid-clip", 1.0, f"centroid drift {f.centroid_drift:.0%}"))

    # --- pitch ------------------------------------------------------------
    f0, voiced, _ = librosa.pyin(y, fmin=60, fmax=500, sr=SR, frame_length=1024, hop_length=HOP)
    f0v = f0[voiced & ~np.isnan(f0)]
    if len(f0v) > 10:
        st = 12 * np.log2(f0v / np.median(f0v))
        f.pitch_std_st = float(np.std(st))
        f0t = librosa.frames_to_time(np.flatnonzero(voiced & ~np.isnan(f0)), sr=SR, hop_length=HOP)
        jumps = np.flatnonzero((np.abs(np.diff(st)) > T["pitch_jump_st"]) & (np.diff(f0t) < 0.025))
        f.pitch_jumps = int(len(jumps))
        if f.pitch_std_st < T["flat_pitch_st"]:
            f.events.append(Event("monotone", None, "the intonation is flat and monotone", 1.0, f"pitch std {f.pitch_std_st:.1f} semitones"))
        elif f.pitch_std_st > T["wild_pitch_st"]:
            f.events.append(Event("erratic_pitch", None, "the pitch jumps around unnaturally", 1.0, f"pitch std {f.pitch_std_st:.1f} semitones"))
        if f.pitch_jumps >= 2:
            f.events.append(Event("pitch_glitch", float(f0t[jumps[0]]), "there are abrupt pitch breaks", 1.0 + 0.2 * min(f.pitch_jumps, 5), f"{f.pitch_jumps} breaks"))

    # --- word-level checks (need Whisper) ----------------------------------
    ref_len = len(alignment.ref_words) if alignment else len(script.split())
    span = f.speech_end - f.speech_start - sum(d for _, d in f.pauses if d >= T["long_pause_s"])
    if span > 0.3:
        f.words_per_sec = ref_len / span
        if f.words_per_sec < T["rate_slow_wps"]:
            f.events.append(Event("slow", None, "the delivery is too slow", 1.0, f"{f.words_per_sec:.1f} words/s"))
        elif f.words_per_sec > T["rate_fast_wps"]:
            f.events.append(Event("fast", None, "the delivery is rushed", 1.0, f"{f.words_per_sec:.1f} words/s"))

    if words:
        f.mean_word_prob = float(np.mean([w.prob for w in words]))
        for w in words:
            if w.prob < T["low_conf_prob"]:
                f.events.append(Event("unclear", w.start, f"'{w.text.strip('.,!?')}' is slurred / unclear", 1.0, f"Whisper confidence {w.prob:.2f}"))
        commas, stops = _boundary_words(script)
        for a, b in zip(words, words[1:]):
            gap = b.start - a.end
            key = re.sub(r"[^a-z0-9']", "", a.text.lower())
            if key in stops and gap < T["rushed_boundary_s"]:
                f.events.append(Event("rushed_boundary", a.end, f"there is no pause after '{a.text.strip('.,!?')}' at the end of the sentence"))
            elif key not in stops and key not in commas and gap > T["unnatural_pause_s"]:
                f.events.append(Event("odd_pause", a.end, f"there is an unnatural pause after '{a.text.strip('.,!?')}'", 1.0, f"{gap:.2f}s"))
        # emphasis: loudness spread across words
        wdb = []
        for w in words:
            s, e = int(w.start * SR / HOP), max(int(w.end * SR / HOP), int(w.start * SR / HOP) + 1)
            if s < len(db):
                wdb.append(float(db[s:e].max()))
        if len(wdb) >= 4:
            f.emphasis_std_db = float(np.std(wdb))
            if f.emphasis_std_db < T["flat_emphasis_db"]:
                f.events.append(Event("flat_stress", None, "every word gets the same stress, with no emphasis", 1.0, f"word loudness std {f.emphasis_std_db:.1f} dB"))

    if alignment:
        for op in alignment.errors:
            if op.kind == "del":
                f.events.append(Event("omission", op.time, f"'{op.ref}' is skipped", 2.0))
            elif op.kind == "ins":
                f.events.append(Event("insertion", op.time, f"an extra word '{op.hyp}' is inserted", 1.5))
            else:
                f.events.append(Event("misread", op.time, f"'{op.ref}' is misread as '{op.hyp}'", 1.5))
    return f
