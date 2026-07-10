<div align="center">
  <h1>SenseVoice Subtitle Generator</h1>
  <p>一个本地字幕生成工具，可用 SenseVoice 和 sherpa-onnx 把媒体文件转成 SRT/VTT/SDH 字幕。</p>

  <p>
    <a href="README.md">English</a>
    &middot;
    <a href="#快速开始">快速开始</a>
    &middot;
    <a href="#核心能力">核心能力</a>
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

<p align="center">
  <img src="docs/ui.png" alt="SenseVoice Subtitle Generator interface screenshot" width="49%" />
  <img src="docs/sdh_demo.png" alt="SDH subtitle output screenshot" width="49%" />
</p>

## 项目概览

字幕生成不应该必须把每个媒体文件上传到云 API。

这个应用下载一次本地模型后，就可以在 Gradio UI 中生成普通字幕和 SDH 风格字幕。

## 核心能力

- 从音频/视频文件生成 SRT 和 VTT。
- 模型下载后本地识别，不需要云端 API Key。
- 可选 SDH 标签、ASS 输出和字幕烧录路径。
- 包含模型下载器和 ffmpeg 处理。
- `docs/` 中保留截图和说明。

## 工作方式

1. 在 Gradio 中上传媒体文件。
2. 通过 ffmpeg 提取 16 kHz 单声道音频。
3. 使用 VAD 和 SenseVoice 转写带时间轴的片段。
4. 输出 SRT/VTT/SDH/ASS，并可选烧录到 MP4。

## 快速开始

可以用下面的命令在本地运行项目。

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

## 配置项

| 项目 | 作用 |
| --- | --- |
| 模型路径 | 由 `download_models.py` 下载；自定义模型不要提交进仓库。 |
| 线程数 | 应用默认使用较保守的 CPU 线程数。 |
| 输出目录 | 生成字幕和烧录视频属于运行时输出。 |
| 人工复核 | 公开发布字幕前应检查识别结果。 |

## 技术栈

| 层级 | 技术 | 作用 |
| --- | --- | --- |
| ASR | SenseVoice via sherpa-onnx | 本地语音识别。 |
| 音频 | imageio-ffmpeg, VAD | 提取并切分语音片段。 |
| UI | Gradio | 上传文件并导出字幕。 |
| 输出 | SRT, VTT, ASS, MP4 burn-in | 字幕格式和烧录预览视频。 |

## 项目结构

```text
app.py                    Gradio 界面
download_models.py        模型下载器
subtitle_gen/             音频、转写、字幕、SDH、烧录模块
docs/                     截图和文档
requirements.txt          Python 依赖
```

## 项目状态

本地优先的媒体工具。重要场景使用前请人工复核文本和 SDH 标签。

## 许可证

MIT License。见 [LICENSE](LICENSE)。
