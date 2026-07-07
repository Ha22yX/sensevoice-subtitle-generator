# SenseVoice Subtitle Generator

一个本地运行的视频/音频字幕生成工具。项目通过 `sherpa-onnx` 调用
SenseVoice，生成带时间轴的字幕；如果模型返回声音事件和情感信息，也可以输出
SDH 风格的字幕标注。

[English](README.md)

![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/Code-MIT-green)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)

## 功能

- 从视频或音频文件生成 `.srt` 和 `.vtt` 字幕。
- 本地运行；模型下载完成后不需要云端 API。
- 使用 SenseVoice 做多语种语音识别。
- 支持普通字幕，也支持带声音/情感标注的 SDH 模式。
- 可生成 `.ass` 字幕，并可选择把字幕烧录进 `.mp4`。
- 通过 `imageio-ffmpeg` 使用 ffmpeg，通常不需要单独安装 ffmpeg。

## 截图

![界面](docs/ui.png)

![SDH 字幕烧录效果](docs/sdh_demo.png)

## 工作流程

```text
媒体文件
  -> ffmpeg 抽取 16 kHz 单声道音频
  -> silero-vad 切分语音片段
  -> SenseVoice 逐段识别
  -> 写出 SRT、VTT，以及可选的 SDH/ASS 字幕
```

项目目前使用段级时间戳。它没有逐字时间戳那么细，但对普通字幕文件更稳定，也避开了
部分 SenseVoice 字级时间戳流程里的对齐问题。

## SDH 模式

SenseVoice 在部分片段上可以返回文本之外的信息，例如语种、情感和音频事件。SDH 模式会
把这些字段整理到字幕里：

- SDH 风格 SRT：加入 `[背景音乐]`、情感前缀等标注。
- ASS 字幕：按情感做简单样式区分。
- 可选烧录：把生成的字幕渲染进新的视频文件。

这些标注来自模型预测，适合辅助无障碍字幕制作、内容复核和视频剪辑。重要发布内容仍
建议人工检查一遍。

## 快速开始

### 1. 安装

建议使用 Python 3.10 或更新版本。

```bash
git clone https://github.com/Ha22yX/sensevoice-subtitle-generator.git
cd sensevoice-subtitle-generator

python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. 下载模型

首次运行需要下载约 1.1 GB 的模型文件。

```bash
python download_models.py
```

模型目录会自动选择：

- 仓库路径为纯 ASCII 时，模型放在项目内的 `models/`。
- 仓库路径包含中文等非 ASCII 字符时，模型放到用户缓存目录。

默认缓存位置：

```text
Windows:      %LOCALAPPDATA%\subtitle-generator\models
macOS/Linux:  ~/.cache/subtitle-generator/models
```

也可以用 `SUB_MODELS_DIR` 指定模型目录。Windows 上建议使用纯 ASCII 路径，避免
ONNX Runtime 加载模型时报错。

下载慢时可以设置 `SUB_MODELS_BASE` 指向镜像：

```powershell
# Windows PowerShell
$env:SUB_MODELS_BASE = "https://your-mirror/asr-models"
python download_models.py
```

```bash
# macOS / Linux
export SUB_MODELS_BASE="https://your-mirror/asr-models"
python download_models.py
```

### 3. 启动

```bash
python app.py
```

打开 <http://127.0.0.1:7860>，上传文件，选择需要的选项，然后生成字幕。

也可以不提前运行 `download_models.py`；第一次生成字幕时应用会自动下载模型。不过提前
下载更容易定位网络或路径问题。

## 选项

| 选项 | 说明 |
| --- | --- |
| 字幕模式 | 普通 SRT/VTT，或带声音/情感标注的 SDH 输出。 |
| 模型精度 | `int8` 更小更快，`full` 精度更高一些。 |
| 推理线程数 | CPU 线程数，通常保持自动即可。 |
| GPU 加速 | 已安装兼容 CUDA 版 `sherpa-onnx` 时可尝试启用。 |
| 烧录字幕到视频 | 把字幕渲染进新的 MP4，会重新编码视频。 |

## 可选 CUDA

默认安装的 `sherpa-onnx` 是 CPU 版。如果要尝试 GPU 推理，需要安装与本机环境匹配的
CUDA 版本，然后在界面里启用 GPU。不可用时应用会回退到 CPU。

```bash
pip uninstall sherpa-onnx
# 然后参考官方文档安装 CUDA 版:
# https://k2-fsa.github.io/sherpa/onnx/install/index.html
```

## 项目结构

```text
.
├── app.py                 # Gradio 网页界面
├── download_models.py     # 模型下载脚本
├── requirements.txt
├── subtitle_gen/          # 字幕生成核心包
│   ├── audio.py           # ffmpeg 抽音频和探测时长
│   ├── transcribe.py      # VAD 分段和 SenseVoice 识别
│   ├── subtitles.py       # SRT/VTT 格式化和片段整理
│   ├── sdh.py             # SDH SRT 和 ASS 字幕
│   └── burn.py            # ffmpeg/libass 字幕烧录
├── docs/                  # 截图
├── models/                # 运行时下载，git 忽略
└── outputs/               # 生成文件，git 忽略
```

## 常见问题

**模型加载报 `invalid unordered_map key`**

Windows 上，ONNX Runtime 在含中文等非 ASCII 字符的路径中加载模型时可能失败。把项目
移动到纯英文路径，或设置 `SUB_MODELS_DIR` 到纯 ASCII 目录，然后重新运行
`python download_models.py`。

**ffmpeg 报错**

项目通过 `imageio-ffmpeg` 提供 ffmpeg。若仍提示缺少 ffmpeg，重新安装依赖：

```bash
pip install -r requirements.txt
```

**为什么不是逐字时间戳**

当前输出是段级字幕。逐字或卡拉 OK 式时间戳需要额外对齐步骤，后续可以单独实现。

**是否支持纯音频文件**

界面主要按视频设计，但底层基于 ffmpeg，很多音频格式也可以作为输入。

## 许可证

项目代码使用 [MIT License](LICENSE)。

模型在运行时下载，仍遵循各自上游项目的许可证。重新分发模型前请确认对应许可：

- [SenseVoice](https://github.com/FunAudioLLM/SenseVoice)
- [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx)
- [silero-vad](https://github.com/snakers4/silero-vad)

## 致谢

本项目基于 SenseVoice、sherpa-onnx、silero-vad、Gradio 和 imageio-ffmpeg。
