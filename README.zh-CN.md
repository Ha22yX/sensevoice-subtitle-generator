<div align="center">
  <h1>SenseVoice Subtitle Generator</h1>
  <p>一个本地字幕生成器，使用 SenseVoice 和 sherpa-onnx 把音视频转换为 SRT/VTT 字幕。</p>

  <p>
    <a href="README.md">English</a>
    &middot;
    <a href="#快速开始">快速开始</a>
    &middot;
    <a href="#技术栈">技术栈</a>
  </p>

  <p>
    <img alt="Python: 3.10+" src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" />
    <img alt="Gradio: UI" src="https://img.shields.io/badge/Gradio-UI-f97316?style=for-the-badge" />
    <img alt="SenseVoice: local ASR" src="https://img.shields.io/badge/SenseVoice-local%20ASR-287866?style=for-the-badge" />
    <img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-6b7f73?style=for-the-badge" />
  </p>
</div>

<p align="center">
  <img src=".github/assets/readme-hero.svg" alt="SenseVoice Subtitle Generator 项目概览图" width="100%" />
</p>

## 项目价值

字幕生成不一定要把文件上传到云端。本应用下载本地模型后，即可通过 Gradio 界面生成字幕，并可选输出 SDH 风格字幕。

## 快速开始

```bash
git clone https://github.com/Ha22yX/sensevoice-subtitle-generator.git
cd sensevoice-subtitle-generator
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python download_models.py
python app.py
```

打开 `http://127.0.0.1:7860`。首次模型下载约 1.1 GB。

## 核心功能

- 从音频/视频文件生成 SRT 和 VTT。
- 模型下载后本地运行，无需云端 API key。
- 可选 SDH 风格标签、ASS 字幕和烧录流程。
- Gradio 界面封装模型路径和 ffmpeg 处理。

## 技术栈

| Layer | Technology | Role |
| --- | --- | --- |
| 语音识别 | SenseVoice via sherpa-onnx | 本地语音识别。 |
| 音频 | imageio-ffmpeg, VAD | 提取并切分语音片段。 |
| 界面 | Gradio | 上传文件并导出字幕。 |
| 输出 | SRT, VTT, ASS, MP4 burn-in | 字幕格式和可选视频烧录。 |


## 项目说明

用于公开发布的重要字幕，建议人工复核文字和 SDH 标签。


## 许可证

MIT License，见 [LICENSE](LICENSE)。
