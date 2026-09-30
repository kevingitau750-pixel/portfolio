"""Turn two clips' measurements into the sheet's three answers:
Preference Selection, Reason tags and a 1–3 sentence comment.

Each detected event is charged to one or more of the 12 reason dimensions
from the guidelines tab. The clip with the lower total penalty wins; the
dimensions where it beats the other clip by the most become the reasons.
Emotion & Style cannot be measured reliably from the signal, so it is never
auto-selected — the reviewer adds it after listening.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from .acoustics import ClipFeatures, Event, fmt_time

# (umbrella, specific) exactly as written in the guidelines tab
DIMENSIONS = {
    "articulation": ("Pronunciation & Articulation", "Clearer articulation and more accurate pronunciation"),
    "omissions": ("Pronunciation & Articulation", "Fewer word omissions, insertions, or misreadings"),
    "intelligibility": ("Pronunciation & Articulation", "Higher overall speech intelligibility"),
    "stress": ("Prosody: intonation, pause, stress", "More natural stress placement and emphasis"),
    "intonation": ("Prosody: intonation, pause, stress", "More human-like intonation flow and cadence"),
    "pacing": ("Prosody: intonation, pause, stress", "Better-paced pausing and speech rate"),
    "emotion_match": ("Emotion & Style", "Emotion/style better matches the text context"),
    "expressiveness": ("Emotion & Style", "Richer expressiveness and more consistent persona"),
    "human_likeness": ("Naturalness", "Higher human-likeness (less robotic/synthetic)"),
    "smoothness": ("Naturalness", "Smoother transitions between words and phrases"),
    "clean_audio": ("Audio Quality & Stability", "Cleaner audio with less noise or digital distortion"),
    "consistency": ("Audio Quality & Stability", "Better consistency in volume, timbre, and stability"),
}

# event kind -> {dimension: weight}
EVENT_DIMENSIONS: dict[str, dict[str, float]] = {
    "omission": {"omissions": 1.0, "intelligibility": 0.5},
    "insertion": {"omissions": 1.0, "intelligibility": 0.3},
    "misread": {"omissions": 0.7, "articulation": 0.7, "intelligibility": 0.5},
    "unclear": {"articulation": 1.0, "intelligibility": 0.5},
    "flat_stress": {"stress": 1.0, "human_likeness": 0.3},
    "monotone": {"intonation": 1.0, "human_likeness": 0.5},
    "erratic_pitch": {"intonation": 1.0, "human_likeness": 0.3},
    "slow": {"pacing": 1.0},
    "fast": {"pacing": 1.0, "intelligibility": 0.3},
    "odd_pause": {"pacing": 1.0, "smoothness": 0.5},
    "long_pause": {"pacing": 1.0},
    "rushed_boundary": {"pacing": 0.7},
    "pitch_glitch": {"human_likeness": 0.7, "smoothness": 0.7},
    "dropout": {"smoothness": 1.0, "clean_audio": 0.5},
    "cutoff": {"smoothness": 0.7, "consistency": 0.5},
    "noise": {"clean_audio": 1.0},
    "click": {"clean_audio": 0.7},
    "clipping": {"clean_audio": 1.0},
    "loudness": {"consistency": 1.0},
    "timbre": {"consistency": 1.0},
    "empty": {d: 1.0 for d in DIMENSIONS},
}

# how to praise the winner on each dimension (used in the comment)
PRAISE = {
    "articulation": "clear, accurate pronunciation",
    "omissions": "every word read correctly",
    "intelligibility": "speech that is easy to understand",
    "stress": "natural word emphasis",
    "intonation": "natural, human-like intonation",
    "pacing": "well-paced pauses and speech rate",
    "human_likeness": "a more human, less synthetic voice",
    "smoothness": "smooth transitions between words",
    "clean_audio": "clean audio",
    "consistency": "stable volume and timbre",
}

PREFERENCES = ("A is better than B", "A is much better than B",
               "B is better than A", "B is much better than A")

TIE_MARGIN = 0.5
MUCH_BETTER_MARGIN = 3.0
RECURRING = {"noise", "click", "dropout", "pitch_glitch", "odd_pause", "unclear"}
SERIOUS = {"omission", "misread", "insertion", "empty", "clipping"}


@dataclass
class Verdict:
    preference: str
    reasons: list[str]            # "Umbrella: specific" strings for the sheet
    comment: str
    confidence: str               # high / medium / low
    scores: dict[str, dict[str, float]] = field(default_factory=dict)  # side -> dim -> penalty
    review_notes: list[str] = field(default_factory=list)


def dimension_penalties(events: list[Event]) -> dict[str, float]:
    pen: dict[str, float] = defaultdict(float)
    for e in events:
        for dim, w in EVENT_DIMENSIONS.get(e.kind, {}).items():
            pen[dim] += w * e.severity
    return dict(pen)


def _describe(events: list[Event], limit: int = 3) -> str:
    """'X (e.g., 0:01.2); Y', most severe first, one mention per kind."""
    seen, parts = set(), []
    for e in sorted(events, key=lambda e: (-e.severity, e.time or 0)):
        if e.kind in seen:
            continue
        seen.add(e.kind)
        if e.time is None:
            parts.append(e.detail)
        else:
            lead = "e.g., " if e.kind in RECURRING else "at "
            parts.append(f"{e.detail} ({lead}{fmt_time(e.time)})")
        if len(parts) == limit:
            break
    return "; ".join(parts)


def judge(a: ClipFeatures, b: ClipFeatures, asr_available: bool = True) -> Verdict:
    pen = {"A": dimension_penalties(a.events), "B": dimension_penalties(b.events)}
    total = {s: sum(p.values()) for s, p in pen.items()}
    diff = total["A"] - total["B"]           # > 0 means B is better
    notes = ["Emotion & Style is not auto-scored: listen and add it if it decides the case."]
    if not asr_available:
        notes.append("Whisper was not run: word omissions/misreadings were NOT checked.")

    if abs(diff) < TIE_MARGIN:
        # Too close to call from measurements; fall back to Whisper confidence / SNR.
        key = lambda f: ((f.mean_word_prob or 0), f.snr_db)  # noqa: E731
        winner = "B" if key(b) > key(a) else "A"
        confidence = "low"
        notes.append("Measurements are nearly tied — decide by ear.")
    else:
        winner = "B" if diff > 0 else "A"
        confidence = "high" if abs(diff) >= MUCH_BETTER_MARGIN else "medium"
    loser = "A" if winner == "B" else "B"
    feats = {"A": a, "B": b}

    loser_serious = any(e.kind in SERIOUS for e in feats[loser].events)
    winner_serious = any(e.kind in SERIOUS for e in feats[winner].events)
    much = abs(diff) >= MUCH_BETTER_MARGIN or (loser_serious and not winner_serious and abs(diff) >= 1.5)
    preference = f"{winner} is {'much ' if much else ''}better than {loser}"

    gaps = {d: pen[loser].get(d, 0) - pen[winner].get(d, 0) for d in DIMENSIONS}
    top = [d for d, g in sorted(gaps.items(), key=lambda kv: -kv[1]) if g > 0][:3]
    if not top:
        top = ["human_likeness"]
        notes.append("No measurable dimension separates the clips; reason defaulted to Naturalness — confirm by ear.")
    reasons = [f"{DIMENSIONS[d][0]}: {DIMENSIONS[d][1]}" for d in top]

    # Talk about what separates the clips, not faults they share.
    kinds = {side: {e.kind for e in feats[side].events} for side in ("A", "B")}
    loser_only = [e for e in feats[loser].events if e.kind not in kinds[winner]]
    winner_only = [e for e in feats[winner].events if e.kind not in kinds[loser] and e.severity >= 1.0]
    shared = [e for e in feats[winner].events if e.kind in kinds[loser]]
    praise_items = [PRAISE[d] for d in top if d in PRAISE]
    praise = (", ".join(praise_items[:-1]) + " and " + praise_items[-1]) if len(praise_items) > 1 else praise_items[0]
    better = f"{'much ' if much else ''}better than Audio {loser} overall"

    sentences = []
    if loser_only:
        sentences.append(f"In Audio {loser}, {_describe(loser_only)}.")
    else:
        sentences.append(f"Audio {loser} has no distinct measurable faults but is slightly weaker overall.")
    if winner_only:
        sentences.append(f"Audio {winner} has {praise}; although {_describe(winner_only, 1)}, "
                         f"it is still {better}.")
    else:
        sentences.append(f"Audio {winner}, on the other hand, has {praise}, making it {better}.")
    if shared:
        sentences.append(f"In both clips, {_describe(shared, 1)}.")
    comment = " ".join(sentences)

    return Verdict(preference, reasons, comment, confidence, pen, notes)
