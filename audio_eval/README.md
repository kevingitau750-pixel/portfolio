# audio_eval — TTS A/B listening-test assistant

Answers an **"Audio Evaluation test"** workbook: for every row (`text`,
`Audio_A`, `Audio_B`) it drafts

| Column | What the tool fills in |
|---|---|
| **Preference Selection** | one of the four dropdown values (`A is better than B`, `A is much better than B`, …) |
| **Reason (Multiple-choice)** | 1–3 of the 12 reason tags from the `guidelines` tab, as `Umbrella: specific dimension` |
| **Comments** | 1–3 sentences in the guideline style: what is wrong in the weaker clip, with timestamps, and why the other wins |

…plus a **Summary** sheet (the "systematic conclusion feedback for all AB
test cases"), an **Analysis** sheet with every measurement, and a **Review
notes** sheet listing what to double-check by ear.

It is an *assistant*, not an oracle: listening tests are subjective, so the
intended workflow is **tool drafts → you listen and confirm/override → export**.

## Quick start (no terminal needed)

1. Download the repository as a ZIP and unzip it.
2. Double-click the launcher in the top folder:
   - **Windows:** `Start Audio Evaluation (Windows).bat`
     (if Windows shows "Windows protected your PC", click *More info* → *Run anyway*)
   - **Mac:** `Start Audio Evaluation (Mac).command`
     (the first time: right-click → *Open* → *Open*, because it is not from the App Store)
3. The first run installs everything (and Python itself on Windows if it is
   missing), which takes a few minutes. Your browser then opens the app. Keep the
   black window open while you work, and close it when you are done.
4. In the app: upload the `.xlsx` → **Analyse** → listen to A and B for each row,
   confirm or change the answers → **Download completed workbook**.

The first **Analyse** also downloads the Whisper speech model once (~250 MB).

## Install (manual)

```bash
pip install -r audio_eval/requirements.txt
# ffmpeg is recommended (lets librosa read mp3/m4a and extension-less files)
```

Whisper runs locally and for free (faster-whisper). The model downloads once
from Hugging Face on first use (`small.en` ≈ 250 MB) and is cached.

## Use

**Review UI (recommended)**

```bash
streamlit run audio_eval/app.py
```

Upload the workbook → *Analyse* → for each row listen to A and B (players
stream straight from the links), read the detected issues, adjust the
drafted answers → edit the summary → *Download completed workbook*.

**Command line (batch)**

```bash
python -m audio_eval "Audio_Evaluation_test.xlsx"            # -> *_answered.xlsx
python -m audio_eval sheet.xlsx --model base.en -o out.xlsx  # faster model
python -m audio_eval sheet.xlsx --audio-dir ./clips          # use local files
python -m audio_eval sheet.xlsx --no-asr                     # skip Whisper
```

`--audio-dir` / the UI's audio upload take files named `<row>_A.wav` and
`<row>_B.wav`, where *row* is the spreadsheet row (the first case is row 2).
Use it when the links have expired or your network blocks them.

## How it decides

1. **Transcribe** each clip with Whisper (word timestamps). The script is *not*
   given to Whisper as a hint — that would hide the TTS's mistakes.
2. **Align** the transcript to the script word by word. Numbers are compared in
   every valid spoken form ("847" = "eight hundred forty seven" = "eight four
   seven"; "$20" = "twenty dollars"), so only real errors count →
   omissions, insertions, misreadings, low-confidence (slurred) words.
3. **Measure the signal** (`acoustics.py`): pauses vs punctuation, speaking
   rate, pitch range and pitch breaks, noise floor / SNR, clicks, clipping,
   dropouts, cut-off endings, volume and timbre drift, word emphasis.
4. **Judge** (`judge.py`): each issue adds a penalty to one or more of the 12
   reason dimensions. The lower total wins; a margin ≥ 3 (or a word error only
   in the loser) makes it "much better". The dimensions with the biggest gap
   become the reasons, and the comment names the loser's issues that the
   winner doesn't share.

Thresholds are in `THRESHOLDS` (acoustics.py) and the weights in
`EVENT_DIMENSIONS` (judge.py) — tune them after comparing with your own ears
on a few sheets.

## Known limits

- **Emotion & Style is never auto-selected.** Whether the tone fits the text
  needs a human; the Review notes remind you to add it.
- Whisper has a language-model prior: it sometimes "hears" the right word
  even when the TTS mispronounced it slightly. Treat "no word errors" as
  "nothing obvious", and listen.
- Absolute naturalness ("sounds robotic") is only approximated through pitch
  range, emphasis and glitches. Close calls are marked 🔴 *low confidence*.
- The signed audio links in the sheet expire (`x-expires`). Download them
  while they are valid, or supply local files.

## Tests

```bash
python -m pytest audio_eval/tests -q
```

The tests synthesise speech with `espeak-ng` (skipped if it's missing) and use
a fake transcriber, so they need no Whisper download.
