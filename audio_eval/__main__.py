"""Command line: ``python -m audio_eval sheet.xlsx [-o answered.xlsx]``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .asr import NullTranscriber, WhisperTranscriber
from .pipeline import DEFAULT_CACHE, analysis_rows, evaluate_case
from .report import build_summary
from .sheet import EvalSheet


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="audio_eval", description="Draft answers for a TTS A/B evaluation sheet.")
    p.add_argument("sheet", type=Path, help="the evaluation .xlsx")
    p.add_argument("-o", "--output", type=Path, help="where to write the answered workbook "
                   "(default: <sheet>_answered.xlsx)")
    p.add_argument("--audio-dir", type=Path, help="folder with local audio named <row>_A.wav / <row>_B.wav "
                   "(row = spreadsheet row number); used before downloading the URLs")
    p.add_argument("--model", default="small.en", help="Whisper model (tiny.en, base.en, small.en, medium.en…)")
    p.add_argument("--no-asr", action="store_true", help="skip Whisper (no word-accuracy checks)")
    p.add_argument("--cache", type=Path, default=DEFAULT_CACHE, help="download cache folder")
    args = p.parse_args(argv)

    sheet = EvalSheet(args.sheet)
    cases = sheet.cases()
    print(f"{len(cases)} case(s) in '{sheet.ws.title}'")

    transcriber = NullTranscriber() if args.no_asr else WhisperTranscriber(args.model)
    results = []
    for case in cases:
        print(f"  row {case.row}: {case.text[:60]}…", flush=True)
        r = evaluate_case(case, transcriber, args.audio_dir, args.cache)
        results.append(r)
        if r.verdict:
            v = r.verdict
            sheet.write_answer(case.row, v.preference, v.reasons, v.comment)
            print(f"    -> {v.preference}  [{v.confidence} confidence]")
        else:
            print(f"    !! skipped: {r.error}", file=sys.stderr)

    sheet.write_summary(build_summary(results))
    sheet.write_table("Analysis", analysis_rows(results))
    sheet.write_table("Review notes", [
        {"sheet_row": r.case.row, "confidence": r.verdict.confidence if r.verdict else "n/a",
         "check_by_ear": "\n".join(r.verdict.review_notes) if r.verdict else r.error}
        for r in results])
    out = sheet.save(args.output or args.sheet.with_name(args.sheet.stem + "_answered.xlsx"))
    print(f"wrote {out}")
    return 0 if all(r.verdict for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
