"""Word-level alignment of the script against a Whisper transcript.

Produces the list of omissions, insertions and misreadings (each with a
timestamp) that feed the "Pronunciation & Articulation" reasons and the
comment text.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .asr import Word
from .text_norm import normalize_hypothesis_word, spoken_variants


@dataclass
class HypWord:
    text: str          # normalised spoken word
    raw: str           # Whisper's original token
    start: float
    end: float
    prob: float


@dataclass
class EditOp:
    kind: str          # "match" | "sub" | "del" | "ins"
    ref: str | None
    hyp: str | None
    time: float        # seconds; for deletions, where the word should have been
    prob: float | None = None


@dataclass
class Alignment:
    ref_words: list[str]
    ops: list[EditOp] = field(default_factory=list)

    @property
    def errors(self) -> list[EditOp]:
        return [o for o in self.ops if o.kind != "match"]

    def count(self, kind: str) -> int:
        return sum(o.kind == kind for o in self.ops)

    @property
    def wer(self) -> float:
        return len(self.errors) / max(1, len(self.ref_words))


def expand_hypothesis(words: list[Word]) -> list[HypWord]:
    """Split Whisper tokens into normalised words, spreading each token's
    time span evenly across the words it expands to ('$20' -> 2 words)."""
    out: list[HypWord] = []
    for w in words:
        parts = normalize_hypothesis_word(w.text)
        if not parts:
            continue
        step = (w.end - w.start) / len(parts)
        for i, p in enumerate(parts):
            out.append(HypWord(p, w.text.strip(), w.start + i * step,
                               w.start + (i + 1) * step, w.prob))
    return out


def _levenshtein_ops(ref: list[str], hyp: list[HypWord]) -> tuple[int, list[tuple[str, int | None, int | None]]]:
    n, m = len(ref), len(hyp)
    d = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        d[i][0] = i
    for j in range(m + 1):
        d[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = 0 if ref[i - 1] == hyp[j - 1].text else 1
            d[i][j] = min(d[i - 1][j - 1] + cost, d[i - 1][j] + 1, d[i][j - 1] + 1)
    ops: list[tuple[str, int | None, int | None]] = []
    i, j = n, m
    while i or j:
        if i and j and d[i][j] == d[i - 1][j - 1] + (ref[i - 1] != hyp[j - 1].text):
            ops.append(("match" if ref[i - 1] == hyp[j - 1].text else "sub", i - 1, j - 1))
            i, j = i - 1, j - 1
        elif i and d[i][j] == d[i - 1][j] + 1:
            ops.append(("del", i - 1, None))
            i -= 1
        else:
            ops.append(("ins", None, j - 1))
            j -= 1
    return d[n][m], ops[::-1]


def align(script: str, words: list[Word]) -> Alignment:
    """Align against whichever spoken reading of the script fits best
    (so "847" read as "eight four seven" is not counted as an error)."""
    hyp = expand_hypothesis(words)
    best = None
    for ref in spoken_variants(script):
        dist, raw_ops = _levenshtein_ops(ref, hyp)
        if best is None or dist < best[0]:
            best = (dist, ref, raw_ops)
    assert best is not None
    _, ref, raw_ops = best

    result = Alignment(ref_words=ref)
    last_t = 0.0
    for idx, (kind, ri, hj) in enumerate(raw_ops):
        if hj is not None:
            h = hyp[hj]
            result.ops.append(EditOp(kind, ref[ri] if ri is not None else None, h.raw, h.start, h.prob))
            last_t = h.end
        else:
            # deletion: place it at the start of the next heard word, if any
            nxt = next((hyp[o[2]].start for o in raw_ops[idx + 1:] if o[2] is not None), last_t)
            result.ops.append(EditOp("del", ref[ri], None, nxt))
    return result
