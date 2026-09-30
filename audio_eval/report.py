"""The "systematic conclusion feedback for all AB test cases": a cross-case
summary of which side won, why, and which problems keep recurring."""

from __future__ import annotations

from collections import Counter

from .pipeline import CaseResult

ISSUE_LABELS = {
    "omission": "skipped words", "insertion": "inserted words", "misread": "misread words",
    "unclear": "slurred / unclear words", "flat_stress": "flat word emphasis",
    "monotone": "monotone intonation", "erratic_pitch": "erratic pitch",
    "slow": "slow delivery", "fast": "rushed delivery", "odd_pause": "unnatural mid-phrase pauses",
    "long_pause": "overlong pauses", "rushed_boundary": "missing pauses at sentence ends",
    "pitch_glitch": "pitch breaks", "dropout": "signal dropouts", "cutoff": "cut-off endings",
    "noise": "background noise", "click": "clicks / pops", "clipping": "clipping distortion",
    "loudness": "uneven volume", "timbre": "timbre drift", "empty": "missing / silent audio",
}


def build_summary(results: list[CaseResult], overrides: dict[int, dict] | None = None) -> str:
    """``overrides`` (row -> {preference, reasons}) lets the reviewer's final
    answers, not the machine drafts, drive the summary."""
    overrides = overrides or {}
    done = [r for r in results if r.verdict]
    failed = [r for r in results if not r.verdict]

    prefs, reasons = [], Counter()
    for r in done:
        o = overrides.get(r.case.row, {})
        prefs.append(o.get("preference", r.verdict.preference))
        reasons.update(o.get("reasons", r.verdict.reasons))

    a_wins = sum(p.startswith("A") for p in prefs)
    b_wins = len(prefs) - a_wins
    strong = sum("much" in p for p in prefs)

    issues = {"A": Counter(), "B": Counter()}
    number_errors = 0
    for r in done:
        for side, clip in (("A", r.a), ("B", r.b)):
            issues[side].update({e.kind for e in clip.features.events})
            if clip.alignment and any(ch.isdigit() or ch in "$£€%" for ch in r.case.text):
                number_errors += sum(1 for o in clip.alignment.errors
                                     if o.ref and o.ref in _NUMBER_WORDS)

    lines = ["Systematic conclusion — all A/B test cases", ""]
    lines.append("Overall result:")
    if prefs:
        lead = "Audio B" if b_wins > a_wins else "Audio A" if a_wins > b_wins else "Neither side"
        lines.append(f"{len(prefs)} case(s) judged: A preferred in {a_wins}, B preferred in {b_wins} "
                     f"({strong} with a strong 'much better' margin). {lead} is preferred overall"
                     + ("." if lead == "Neither side" else f", winning {max(a_wins, b_wins)} of {len(prefs)} cases."))
    if failed:
        lines.append(f"{len(failed)} case(s) could not be analysed (rows "
                     f"{', '.join(str(r.case.row) for r in failed)}): {failed[0].error}")
    lines.append("")

    if reasons:
        lines.append("Most frequent deciding reasons:")
        for reason, n in reasons.most_common(4):
            lines.append(f"• {reason} — {n} case(s)")
        lines.append("")

    lines.append("Recurring issues by side:")
    for side in ("A", "B"):
        common = [f"{ISSUE_LABELS.get(k, k)} ({n}/{len(done)})" for k, n in issues[side].most_common(4)]
        lines.append(f"• Audio {side}: " + (", ".join(common) if common else "no recurring measurable issues"))
    lines.append("")

    lines.append("Observations:")
    obs = []
    if number_errors:
        obs.append(f"Numbers / currency are a weak spot: {number_errors} number word(s) were misread or "
                   "skipped in texts containing digits or symbols (e.g. '$20', '847').")
    content_issues = ("omission", "insertion", "misread")
    for side in ("A", "B"):
        n = sum(issues[side][k] for k in content_issues)
        if n:
            obs.append(f"Audio {side} has word-accuracy problems in {n} case-issue(s); accuracy errors "
                       "weigh most heavily because they change the message.")
    if any(issues[s]["noise"] + issues[s]["click"] + issues[s]["clipping"] for s in "AB"):
        obs.append("Audio-quality artefacts (noise, clicks or clipping) appear — check the vocoder / post-processing.")
    if any(issues[s]["odd_pause"] + issues[s]["rushed_boundary"] for s in "AB"):
        obs.append("Pause placement does not always follow punctuation — phrasing / prosody model needs work.")
    if not obs:
        obs.append("No systematic defect pattern stands out; the differences are mostly in naturalness and prosody.")
    obs.append("Emotion & Style was judged by ear only; A/B labels may map to different systems per row, "
               "so per-side trends are only meaningful if each side is the same model throughout.")
    lines.extend(f"• {o}" for o in obs)
    return "\n".join(lines)


_NUMBER_WORDS = set(
    "zero oh one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen "
    "sixteen seventeen eighteen nineteen twenty thirty forty fifty sixty seventy eighty ninety hundred "
    "thousand million billion point dollar dollars cent cents pound pounds percent".split())
