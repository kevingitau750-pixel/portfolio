"""Review UI:  streamlit run audio_eval/app.py   (from the repo root)

Upload the evaluation workbook, let the tool draft answers, then listen to
each A/B pair, confirm or override the drafts and download the completed
workbook. Standalone — not part of the portfolio site's navigation.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from audio_eval.acoustics import fmt_time  # noqa: E402
from audio_eval.asr import NullTranscriber, WhisperTranscriber  # noqa: E402
from audio_eval.judge import DIMENSIONS, PREFERENCES  # noqa: E402
from audio_eval.pipeline import DEFAULT_CACHE, analysis_rows, evaluate_case  # noqa: E402
from audio_eval.report import build_summary  # noqa: E402
from audio_eval.sheet import EvalSheet  # noqa: E402

REASON_OPTIONS = [f"{u}: {s}" for u, s in DIMENSIONS.values()]
st.set_page_config(page_title="TTS A/B evaluation", page_icon="🎧", layout="wide")


@st.cache_resource(show_spinner="Loading Whisper model (first run downloads it)…")
def get_transcriber(model: str):
    return WhisperTranscriber(model)


def workdir() -> Path:
    if "workdir" not in st.session_state:
        st.session_state.workdir = Path(tempfile.mkdtemp(prefix="audio_eval_"))
    return st.session_state.workdir


st.title("🎧 TTS A/B listening-test assistant")
st.caption("The tool drafts Preference, Reason and Comments from Whisper + acoustic analysis. "
           "**You** listen, confirm or change each answer, then download the finished sheet.")

with st.sidebar:
    upload = st.file_uploader("Evaluation workbook (.xlsx)", type=["xlsx"])
    audio_files = st.file_uploader("Optional: local audio (name files `<row>_A.wav`, `<row>_B.wav`)",
                                   type=["wav", "mp3", "flac", "ogg", "m4a"], accept_multiple_files=True)
    model = st.selectbox("Whisper model", ["small.en", "base.en", "tiny.en", "medium.en"],
                         help="Bigger = more accurate but slower. small.en is a good default on CPU.")
    no_asr = st.checkbox("Skip Whisper (acoustics only)", help="Word omissions/misreadings will not be checked.")
    run = st.button("Analyse", type="primary", disabled=upload is None, width="stretch")

if upload is None:
    st.info("Upload the evaluation workbook in the sidebar to start.")
    st.stop()

wd = workdir()
src = wd / "input.xlsx"
if run:
    src.write_bytes(upload.getvalue())
    audio_dir = wd / "audio"
    audio_dir.mkdir(exist_ok=True)
    for f in audio_files or []:
        (audio_dir / f.name).write_bytes(f.getvalue())
    transcriber = NullTranscriber() if no_asr else get_transcriber(model)
    cases = EvalSheet(src).cases()
    results, bar = [], st.progress(0.0, "Analysing…")
    for i, case in enumerate(cases, 1):
        bar.progress(i / len(cases), f"Row {case.row}: {case.text[:50]}…")
        results.append(evaluate_case(case, transcriber, audio_dir, DEFAULT_CACHE))
    bar.empty()
    # fresh drafts: drop answers the widgets remembered from a previous run
    for key in [k for k in st.session_state if k.startswith("row") or k == "summary"]:
        del st.session_state[key]
    st.session_state.results = results
    st.session_state.src_name = upload.name

if "results" not in st.session_state:
    st.info("Press **Analyse** in the sidebar.")
    st.stop()
if st.session_state.src_name != upload.name:
    st.warning(f"Showing results for **{st.session_state.src_name}** — press Analyse to process the new file.")

results = st.session_state.results
answers: dict[int, dict] = {}

for r in results:
    c, v = r.case, r.verdict
    with st.container(border=True):
        head, badge = st.columns([6, 1])
        head.markdown(f"**Row {c.row}** — “{c.text}”")
        if v:
            badge.markdown({"high": "🟢", "medium": "🟡", "low": "🔴"}[v.confidence] + f" {v.confidence}")
        else:
            badge.markdown("⚠️ not analysed")
            st.warning(f"Automatic analysis failed ({r.error}). You can still listen and answer by hand.")

        cols = st.columns(2)
        for col, side, clip in ((cols[0], "A", r.a), (cols[1], "B", r.b)):
            with col:
                st.markdown(f"**Audio {side}**")
                st.audio(str(clip.path) if clip.path else clip.source)
                if clip.transcript:
                    st.caption(f"Whisper heard: “{clip.transcript}”")
                if clip.features:
                    for e in clip.features.events:
                        where = "" if e.time is None else f" `{fmt_time(e.time)}`"
                        st.markdown(f"- {e.detail}{where}" + (f" <small>({e.metric})</small>" if e.metric else ""),
                                    unsafe_allow_html=True)
                    if not clip.features.events:
                        st.markdown("- no measurable issues")

        k = f"row{c.row}"
        pref = st.selectbox("Preference Selection", PREFERENCES, key=f"{k}_pref",
                            index=PREFERENCES.index(v.preference) if v else 0)
        reasons = st.multiselect("Reason(s)", REASON_OPTIONS, key=f"{k}_reasons",
                                 default=[x for x in (v.reasons if v else []) if x in REASON_OPTIONS])
        comment = st.text_area("Comments", key=f"{k}_comment", value=v.comment if v else "", height=100)
        if v and v.review_notes:
            st.caption("Check by ear: " + " ".join(v.review_notes))
        answers[c.row] = {"preference": pref, "reasons": reasons, "comment": comment}

st.subheader("Systematic conclusion (all cases)")
if st.button("Regenerate from my answers") or "summary" not in st.session_state:
    st.session_state.summary = build_summary(results, answers)
summary = st.text_area("Summary", key="summary", height=320)

sheet = EvalSheet(src)
for row, a in answers.items():
    sheet.write_answer(row, a["preference"], a["reasons"], a["comment"])
sheet.write_summary(summary)
sheet.write_table("Analysis", analysis_rows(results))
out = sheet.save(wd / "answered.xlsx")
missing = [row for row, a in answers.items() if not a["reasons"] or not a["comment"].strip()]
if missing:
    st.warning(f"Rows {', '.join(map(str, missing))} still need a reason and a comment.")
st.download_button("⬇️ Download completed workbook", out.read_bytes(),
                   file_name=Path(upload.name).stem + "_answered.xlsx", type="primary",
                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

with st.expander("Raw measurements"):
    st.dataframe(pd.DataFrame(analysis_rows(results)), width="stretch")
