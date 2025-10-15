# s2t

Record audio from your microphone, run Whisper to transcribe it, export common formats, and copy the .txt transcript to your clipboard.

## Install
- From local checkout:
  - Editable: `pip install -e .`
  - Standard: `pip install .`

Requirements: Python 3.11–3.12. No mandatory external binaries. ffmpeg is optional (only for MP3 encoding/decoding).

System requirements (Linux)
- Some environments need system libraries for audio I/O:
  - Debian/Ubuntu: `sudo apt-get install libportaudio2 libsndfile1`
  - Fedora/RHEL: `sudo dnf install portaudio libsndfile`
- Optional for MP3: ffmpeg (`sudo apt-get install ffmpeg` or `brew install ffmpeg`).

## Usage
- Start interactive recording and transcribe:
  - `s2t`
- Short options:
  - Language: `-l de` (long: `--lang de`)
  - Model: `-m large-v3` (long: `--model large-v3`)
  - Sample rate: `-r 48000` (long: `--rate 48000`)
  - Channels: `-c 2` (long: `--channels 2`)
  - Output dir: `-o transcripts` (long: `--outdir transcripts`) — default is `transcripts/` if omitted
  - Translate to English: `-t` (long: `--translate`). You may still provide `--lang` as an input-language hint if you want.
  - List available models and exit: `-L` (long: `--list-models`)
  - Recording format: `-f flac|wav|mp3` (long: `--recording-format`), default `flac`. MP3 requires ffmpeg; if absent, it falls back to FLAC with a warning.
  - Auto-split on silence: `--silence-sec 1.0` (default `1.0`; `0` disables). When continuous silence ≥ this many seconds is detected, the current chunk is ended automatically.
  - Minimum chunk length for auto-split: `--min-chunk-sec 5.0` (default `5.0`). Prevents very short chunks and avoids splitting early in a sentence.
  - Prompt mode (spoken prompt): `-p` (long: `--prompt`). Speak your prompt first, then press SPACE to use it as prompt and continue with your main content. If you press ENTER instead of SPACE, no prompt is used; the spoken audio is transcribed as normal payload and the session ends.
  - Keep chunk files: `--keep-chunks` — by default, per‑chunk audio and per‑chunk Whisper outputs are deleted after the final merge.
  - Open transcript for editing: `-e` (long: `--edit`) — opens the generated `.txt` in your shell editor (`$VISUAL`/`$EDITOR`).
- Examples:
  - Transcribe in German using large-v3: `s2t -l de -m large-v3`
  - Translate any input to English: `s2t -t`
  - Write outputs under transcripts/: `s2t -o transcripts`
  - List local model names: `s2t -L`

Outputs are written into a timestamped folder under the chosen output directory (default is `transcripts/`), e.g. `transcripts/2025-01-31T14-22-05+0200/`, containing:
- Per‑chunk outputs: `chunk_####.flac/.wav` plus `chunk_####.txt/.srt/.vtt/.tsv/.json` (deleted by default unless `--keep-chunks`)
- Final outputs: `recording.flac/.wav` (and `recording.mp3` if requested and ffmpeg available), plus `recording.txt/.srt/.vtt/.tsv/.json`
- Clipboard mirrors the combined `.txt` with blank lines between chunks.

Auto-splitting details
- SPACE always splits immediately; ENTER finishes the recording.
- With `--silence-sec > 0`, chunks end automatically after detected continuous silence of that many seconds.
- Auto-split only triggers once the current chunk has at least `--min-chunk-sec` seconds and after speech has been detected (to ignore leading silence). A short internal cooldown avoids duplicate splits.

## Makefile (optional)
- Setup venv + dev deps: `make setup`
- Lint/format/test: `make lint`, `make format`, `make test`; combined gate: `make check`
- Build sdist/wheel: `make build` (runs `check` first)
- Publish to PyPI/TestPyPI: `make publish`, `make publish-test` (run after `build`)
- Run CLI: `make record ARGS='-l de -t -o transcripts'`
- List models: `make list-models`
- Show package version: `make version`

Notes on models
- The local openai-whisper CLI supports models like: `tiny`, `base`, `small`, `medium`, `large-v1`, `large-v2`, `large-v3` and their `.en` variants.
- The name `turbo` refers to OpenAI’s hosted model family and is not provided by the local `whisper` CLI. If you pass `-m turbo`, the command may fail; choose a supported local model instead.

## Development & Release
- For developer setup and contribution guidelines, see `CONTRIBUTING.md`.
- For the release process, see `docs/RELEASING.md`.
