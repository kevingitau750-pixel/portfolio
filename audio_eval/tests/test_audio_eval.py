"""Run with:  python -m pytest audio_eval/tests -q   (from the repo root)

Audio fixtures are synthesised with espeak-ng (tests that need it are skipped
if it is not installed). Whisper itself is replaced by a fake transcriber so
the tests are fast and need no model download.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import numpy as np
import openpyxl
import pytest
import soundfile as sf
from openpyxl.worksheet.datavalidation import DataValidation

from audio_eval.alignment import align
from audio_eval.asr import Word
from audio_eval.judge import DIMENSIONS, PREFERENCES
from audio_eval.pipeline import evaluate_case
from audio_eval.report import build_summary
from audio_eval.sheet import Case, EvalSheet
from audio_eval.text_norm import number_variants, spoken_words

DRIVER = "Your driver Alex is 3 minutes away in a white Toyota Corolla, license ending in 847"
TURKEY = "First, you'll need a big turkey. A 15 - pound one might cost around $20. Then there are side dishes."
needs_espeak = pytest.mark.skipif(not shutil.which("espeak-ng"), reason="espeak-ng not installed")


def words(*tokens: str, start: float = 0.2, step: float = 0.3, prob: float = 0.95) -> list[Word]:
    return [Word(t, start + i * step, start + i * step + step * 0.8, prob) for i, t in enumerate(tokens)]


class FakeTranscriber:
    """Returns pre-set words per file name."""
    name = "fake"

    def __init__(self, by_name: dict[str, list[Word]]):
        self.by_name = by_name

    def transcribe(self, audio_path: Path) -> list[Word]:
        return self.by_name[Path(audio_path).name]


# --- text normalisation ---------------------------------------------------------

def test_currency_and_numbers_are_spoken():
    assert spoken_words("around $20.") == ["around", "twenty", "dollars"]
    assert spoken_words("A 15 - pound one") == ["a", "fifteen", "pound", "one"]
    assert spoken_words("you'll") == ["you", "will"]
    assert spoken_words("$1.50") == ["one", "dollar", "and", "fifty", "cents"]


def test_number_readings_include_digit_by_digit():
    v = number_variants("847")
    assert "eight hundred forty seven" in v
    assert "eight four seven" in v
    assert "nineteen eighty five" in number_variants("1985")


# --- alignment ------------------------------------------------------------------

def test_perfect_reading_has_no_errors_even_with_other_number_forms():
    hyp = words(*"Your driver Alex is three minutes away in a white Toyota Corolla, license ending in 8 4 7".split())
    assert align(DRIVER, hyp).errors == []
    hyp2 = words(*"First, you'll need a big turkey. A 15-pound one might cost around $20. Then there are side dishes.".split())
    assert align(TURKEY, hyp2).errors == []


def test_omission_and_misreading_are_located():
    hyp = words(*"Your driver Alex is 3 minutes away in a Toyota Corolla, license ending in 874".split())
    al = align(DRIVER, hyp)
    dels = [o for o in al.errors if o.kind == "del"]
    assert [o.ref for o in dels] == ["white"]
    assert dels[0].time == pytest.approx(hyp[9].start)   # where "Toyota" starts
    assert al.count("sub") >= 1                           # 874 vs 847


# --- end to end on synthetic audio ----------------------------------------------

def _tts(path: Path, text: str) -> Path:
    subprocess.run(["espeak-ng", "-w", str(path), "-s", "165", text], check=True)
    return path


def _add_noise(path: Path, level: float = 0.02) -> None:
    y, sr = sf.read(path)
    y = y + np.random.default_rng(0).normal(0, level, len(y))
    sf.write(path, y, sr)


@needs_espeak
def test_skipped_word_loses_and_comment_names_it(tmp_path):
    _tts(tmp_path / "2_A.wav", DRIVER)
    _tts(tmp_path / "2_B.wav", DRIVER.replace("white ", ""))
    good = words(*DRIVER.split())
    bad = words(*DRIVER.replace("white ", "").split())
    tr = FakeTranscriber({"2_A.wav": good, "2_B.wav": bad})
    res = evaluate_case(Case(2, DRIVER, "x", "y"), tr, audio_dir=tmp_path, cache=tmp_path)

    v = res.verdict
    assert v.preference in PREFERENCES and v.preference.startswith("A")
    assert any(DIMENSIONS["omissions"][1] in r for r in v.reasons)
    assert "'white' is skipped" in v.comment
    assert v.comment.startswith("In Audio B")


@needs_espeak
def test_noisy_clip_loses_on_audio_quality(tmp_path):
    _tts(tmp_path / "4_A.wav", "They can do a lot.")
    _tts(tmp_path / "4_B.wav", "They can do a lot.")
    _add_noise(tmp_path / "4_A.wav")
    same = words("They", "can", "do", "a", "lot.")
    tr = FakeTranscriber({"4_A.wav": same, "4_B.wav": same})
    v = evaluate_case(Case(4, "They can do a lot.", "x", "y"), tr, audio_dir=tmp_path, cache=tmp_path).verdict
    assert v.preference.startswith("B")
    assert v.reasons[0].endswith(DIMENSIONS["clean_audio"][1])
    assert "background noise" in v.comment


def test_unreachable_audio_is_reported_not_raised(tmp_path):
    tr = FakeTranscriber({})
    res = evaluate_case(Case(2, "hi", str(tmp_path / "missing.wav"), "not-a-url"), tr, cache=tmp_path)
    assert res.verdict is None and "FileNotFoundError" in res.error
    assert "could not be analysed" in build_summary([res])


# --- workbook round trip ----------------------------------------------------------

def test_sheet_answers_written_and_dropdown_kept(tmp_path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Worksheet"
    ws.append(["text", "Audio_A", "Audio_B", "Preference Selection", "Reason(Multiple-choice)", "Comments"])
    ws.append([DRIVER, "a.wav", "b.wav"])
    dv = DataValidation(type="list", formula1='"' + ",".join(PREFERENCES) + '"')
    dv.add("D2:D2")
    ws.add_data_validation(dv)
    src = tmp_path / "in.xlsx"
    wb.save(src)

    sheet = EvalSheet(src)
    assert [c.row for c in sheet.cases()] == [2]
    sheet.write_answer(2, PREFERENCES[0], ["R1", "R2"], "comment")
    sheet.write_summary("Title\n\nOverall result:\nline")
    out = sheet.save(tmp_path / "out.xlsx")

    ws2 = openpyxl.load_workbook(out)["Worksheet"]
    assert ws2["D2"].value == PREFERENCES[0]
    assert ws2["E2"].value == "R1\nR2"
    assert ws2["F2"].value == "comment"
    assert ws2.data_validations.dataValidation[0].formula1 == dv.formula1
