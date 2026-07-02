<div align="center">

# 🎬 SenseVoice Subtitle Generator

**Drop in a video → AI generates timed subtitles (SRT / VTT) — with an exclusive ♿ accessibility (SDH) mode that annotates sounds & emotions.**

[English](README.md) · [中文](README.zh-CN.md)

Powered by [SenseVoice](https://github.com/FunAudioLLM/SenseVoice) multilingual speech recognition, running **locally** via
[sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx) — no internet, no API key. Auto-detects Chinese / English / Japanese / Korean / Cantonese and 50+ languages.

![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/Code-MIT-green)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)
![Engine](https://img.shields.io/badge/engine-sherpa--onnx%20%2B%20SenseVoice-indigo)

</div>

---

## ✨ Features

- 🎞️ **Drag & drop** — upload a video in the browser, get subtitles in one click.
- ⚡ **Fast & accurate** — SenseVoice is non-autoregressive, ~10× faster than Whisper.
- 🌍 **Multilingual auto-detect** — Chinese, English, Japanese, Korean, Cantonese, 50+ languages.
- 🔒 **100% local** — audio never leaves your machine; no API key, no network.
- 📝 **Standard formats** — SRT + WebVTT, compatible with virtually every player.
- ♿ **Accessibility SDH subtitles (exclusive)** — uses SenseVoice's **emotion recognition + audio-event
  detection** to produce subtitles annotated with `[Applause]` `[Laughter]` `[Background Music]` and
  colored by emotion (ASS). A genuine need for deaf/hard-of-hearing viewers, content creators, and
  language learners — **no other open-source tool does this** (see below).
- 🔥 **Burn subtitles into video** — optionally render styled subtitles (including SDH emotion colors)
  directly into an MP4, ready to share.
- 🧩 **Zero-config deps** — ffmpeg is bundled via `imageio-ffmpeg`, no separate install.
- 💻 **Cross-platform** — Windows / macOS / Linux; runs on CPU by default, optional GPU.

## 🖼️ Screenshots

![Interface](docs/ui.png)

![SDH subtitles burned into video — emotion-colored text + sound tags](docs/sdh_demo.png)

> Above: SDH subtitles burned into the video. The happy greeting is rendered in **orange**, with a
> `[背景音乐]` (Background Music) sound tag.

## ♿ Accessibility SDH subtitles (exclusive)

SenseVoice differs from Whisper in one key way: a **single call returns text + language + emotion +
audio event** (Whisper returns text only). This tool maps those extra signals into **SDH**
(Subtitles for Deaf and Hard of Hearing) subtitles — **no other open-source project does this today.**

Select **"Subtitle mode → Accessibility SDH"** in the UI to get:

- **SDH · SRT** — speech lines augmented with sound & emotion tags:
  ```text
  1
  00:00:28,902 --> 00:00:35,676
  [背景音乐]

  2
  00:00:28,902 --> 00:00:35,676
  （开心）朋友们，晚上好，欢迎大家来参加今天晚上的活动，谢谢大家。
  ```
- **SDH · ASS** — speech **colored by emotion** (happy=orange, angry=red, sad=blue, surprised=yellow…),
  with sound tags in an italic secondary style. Needs an ASS-capable player (VLC / PotPlayer / mpv / MPC).

What SenseVoice detects and how it maps:

| Signal | Values | In the subtitle |
|---|---|---|
| **Audio event** | BGM / Applause / Laughter / Burst laughter / Cry / Sneeze | `[sound]`; BGM shown once per run |
| **Emotion** | Happy / Sad / Angry / Tense / Surprised / Disgusted | `（emotion）` prefix in SRT; color in ASS |
| **Language** | zh / en / ja / ko / yue / … | auto-detected (no manual pick) |

> 💡 Great for: making videos accessible (SDH) for deaf viewers, podcast/video content review with
> sentiment, language-learners matching tone, short-video creators spotting emotional highlights.

## 🛠️ How it works

```
video ──(ffmpeg → 16 kHz mono PCM)──► silero-vad segmentation
        └── per segment ► SenseVoice decode ► text + lang + emotion + event + segment timestamps
                                                        │
                                  ┌─────────────────────┴─────────────────────┐
                                  ▼                                           ▼
                        SRT / VTT                                  SDH SRT / emotion-colored ASS
                                                                      │
                                                              (optional) burn into MP4
```

We use **VAD segmentation + segment-level timestamps** — the stable, officially-recommended approach
(SenseVoice's native word-level timestamps in FunASR have a [known alignment issue](https://github.com/modelsize/FunASR/issues/2324),
so they're avoided here).

## 🚀 Quick start

### 1. Install

Requires **Python 3.10 – 3.14** (verified on Windows / 3.14).

```bash
git clone https://github.com/Ha22yX/sensevoice-subtitle-generator.git
cd sensevoice-subtitle-generator

python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Download models (first run, ~1.1 GB)

```bash
python download_models.py
```

Models are stored on an **ASCII-only path** (chosen automatically):

- If the project path is ASCII → `models/` inside the project.
- Otherwise (e.g. project inside a Chinese-named folder) → a user cache dir:
  - Windows: `%LOCALAPPDATA%\subtitle-generator\models`
  - macOS / Linux: `~/.cache/subtitle-generator/models`

> ⚠️ **Why?** ONNX Runtime on Windows **corrupts model loading for paths containing non-ASCII
> characters** (e.g. Chinese), causing an `invalid unordered_map key` error at decode time. This
> project detects and avoids that automatically. To set a custom location, use the `SUB_MODELS_DIR`
> environment variable (must be an ASCII path).

**Slow / failing downloads?** Point `SUB_MODELS_BASE` at a mirror:

```bash
# Windows PowerShell
$env:SUB_MODELS_BASE = "https://your-mirror/asr-models"
python download_models.py
# macOS / Linux
export SUB_MODELS_BASE="https://your-mirror/asr-models"
python download_models.py
```

### 3. Run

```bash
python app.py
```

Your browser opens <http://127.0.0.1:7860>. Upload a video → pick options → click **Generate** →
preview and download in the SRT / VTT (or SDH) tabs.

> 💡 You can **skip step 2** — the first click of "Generate" auto-downloads the models.

## ⚙️ Options

| Option | Description |
|---|---|
| **Subtitle mode** | `Normal` (SRT / VTT) or `Accessibility SDH` (sound/emotion-tagged SRT + emotion-colored ASS). |
| **Model precision** | `int8` (default, faster & smaller) or `full` (slightly more accurate). |
| **Inference threads** | CPU threads; auto-set from CPU cores by default. |
| **GPU acceleration** | Attempts CUDA; requires a CUDA build of sherpa-onnx (see below). Falls back to CPU on failure. |
| **Burn into video** | Renders the generated subtitles directly into an output MP4 (slower, since it re-encodes). |

### Optional: GPU acceleration (CUDA)

The default `sherpa-onnx` is CPU-only and runs everywhere. If you have an NVIDIA GPU and want a
speedup, install a CUDA build of sherpa-onnx and tick "GPU acceleration" (the code auto-detects and
falls back to CPU if unavailable):

```bash
pip uninstall sherpa-onnx
# Install the CUDA build matching your CUDA version per the official docs:
# https://k2-fsa.github.io/sherpa/onnx/install/index.html
```

## 📁 Project structure

```
.
├── app.py                 # Gradio web UI entry point
├── download_models.py     # model downloader (first run)
├── requirements.txt
├── subtitle_gen/          # core package
│   ├── audio.py           # ffmpeg audio extraction / duration probe
│   ├── transcribe.py      # VAD segmentation + SenseVoice (text/lang/emotion/event)
│   ├── subtitles.py       # SRT / VTT formatting + segment refinement
│   ├── sdh.py             # accessibility SDH (SRT + ASS with sound/emotion)
│   └── burn.py            # burn subtitles into video (libass)
├── docs/                  # screenshots
├── models/                # downloaded at runtime (not in repo; user cache if path is non-ASCII)
└── outputs/               # generated subtitles (not in repo)
```

## 🧰 Tech stack

- **[SenseVoice](https://github.com/FunAudioLLM/SenseVoice)** (FunAudioLLM) — multilingual ASR + emotion + event detection
- **[sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx)** (k2-fsa) — Next-gen Kaldi ONNX runtime
- **[silero-vad](https://github.com/snakers4/silero-vad)** — voice activity detection
- **[Gradio](https://gradio.app)** — web interface
- **[imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg)** — bundled ffmpeg binary

## ❓ FAQ

**Q: Why are timestamps per-segment rather than per-word?**
A: We use VAD segmentation for stable, reliable segment-level timestamps — enough for the vast
majority of subtitle use cases. Per-word (karaoke-style) is a possible future enhancement.

**Q: No punctuation / wrong punctuation?**
A: SenseVoice runs inverse text normalization (ITN), so it adds punctuation and normalizes numbers
automatically.

**Q: "ffmpeg not found"?**
A: Won't happen — ffmpeg is bundled via `imageio-ffmpeg` at `pip install` time. If it still errors,
make sure `requirements.txt` is fully installed.

**Q: `invalid unordered_map key` or model load failure?**
A: This is the known ONNX Runtime issue with **non-ASCII (e.g. Chinese) model paths** on Windows. The
tool already places models on an ASCII path. If it persists, set `SUB_MODELS_DIR` to an ASCII
directory and re-run `python download_models.py`.

**Q: Does it work on audio files?**
A: The UI is video-oriented, but the underlying pipeline is ffmpeg-based, so audio files work too
(you can call `subtitle_gen` directly).

## 🤝 Contributing

Issues and PRs welcome! Ideas: per-word timestamps, batch processing, more subtitle styles, a CLI.

## 📄 License

- **This project's code**: [MIT License](./LICENSE).
- **Models**: this project does **not** bundle or redistribute models — they're downloaded at runtime
  and remain under their own licenses, which you must comply with:
  [SenseVoice](https://github.com/FunAudioLLM/SenseVoice) ·
  [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx) ·
  [silero-vad](https://github.com/snakers4/silero-vad).

## 🙏 Acknowledgements

Thanks to the above open-source projects for making this possible.

<div align="center">

If this project helps you, a ⭐ Star is appreciated!

</div>
