<div align="center">

# 🎬 视频自动字幕生成器

**导入视频 → AI 自动生成带时间轴字幕(SRT / VTT),并独家支持 ♿ 无障碍 SDH 字幕(声音与情感标注)**

基于 [SenseVoice](https://github.com/FunAudioLLM/SenseVoice) 多语种语音识别,
经 [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx) 在**本地**推理 ——
无需联网、无需 API Key,中 / 英 / 日 / 韩 / 粤自动识别。

![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/Code-MIT-green)
![Platform](https://img.shields.io/badge/平台-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)
![Engine](https://img.shields.io/badge/引擎-sherpa--onnx%20%2B%20SenseVoice-indigo)

</div>

---

## ✨ 特性

- 🎞️ **拖入即用**:网页上传视频,一键生成字幕。
- ⚡ **又快又准**:SenseVoice 非自回归模型,比 Whisper 快约 10×。
- 🌍 **多语种自动识别**:中文、英语、日语、韩语、粤语等 50+ 语言。
- 🔒 **完全本地**:音频不离开你的电脑,无需 API Key、无需联网。
- 📝 **双格式输出**:标准 SRT + WebVTT,兼容几乎所有播放器。
- ♿ **无障碍 SDH 字幕(独家)**:利用 SenseVoice 的**情感识别 + 音频事件检测**,生成带
  `[掌声]` `[笑声]` `[背景音乐]` 等声音标注、并按情感着色(ASS)的字幕 ——
  这是听障人士、内容创作者、语言学习者的刚需,**目前没有同类开源工具**(见下)。
- 🧩 **零配置依赖**:ffmpeg 由 `imageio-ffmpeg` 自带,无需单独安装。
- 💻 **跨平台**:Windows / macOS / Linux,默认纯 CPU 即可运行;可选 GPU 加速。

## 🖼️ 截图

![界面预览](docs/ui.png)

拖入视频 → 选择选项 → 一键「生成字幕」→ SRT / VTT 标签页预览并下载,全程本地运行。

## 🛠️ 工作原理

```
视频 ──(ffmpeg 抽 16kHz 单声道 PCM)──► silero-vad 语音分段
        └── 每段 ► SenseVoice 解码 ► 文本 + 段级时间戳
                                          │
                            ┌─────────────┴─────────────┐
                            ▼                           ▼
                         SRT 字幕                    VTT 字幕
```

采用 **VAD 分段 + 段级时间戳** 的方案 —— 这是 sherpa-onnx 官方推荐的稳定做法
(SenseVoice 在 FunASR 中的原生字级时间戳存在[已知对齐问题](https://github.com/modelsize/FunASR/issues/2324),
故不采用)。

## ♿ 无障碍 SDH 字幕(独家功能)

SenseVoice 与 Whisper 最大的不同:它**一次调用同时输出 文本 + 语种 + 情感 + 音频事件**
(Whisper 只输出纯文本)。本工具把这些额外信息映射成 **SDH(Subtitles for Deaf and Hard of Hearing)**
无障碍字幕 —— 目前**没有其他开源项目**做这件事。

在界面选择 **「字幕模式 → 无障碍 SDH 字幕」**,即可得到:

- **SDH · SRT**:在台词里加入声音与情感标注。
  ```text
  1
  00:00:28,902 --> 00:00:35,676
  [背景音乐]

  2
  00:00:28,902 --> 00:00:35,676
  （开心）朋友们，晚上好，欢迎大家来参加今天晚上的活动，谢谢大家。
  ```
- **SDH · ASS**:台词按情感着色(开心=橙、生气=红、难过=蓝、惊讶=黄…),
  声音标注用斜体副样式。需支持 ASS 的播放器(VLC / PotPlayer / mpv / MPC)才能看到效果。
  ```text
  Dialogue: ... Default ... {\c&H000099FF}（开心）朋友们，晚上好…
  Dialogue: ... Sound  ... [背景音乐]
  ```

SenseVoice 可识别的标注来源:

| 类型 | 取值 | 字幕里的体现 |
|------|------|--------------|
| **音频事件** | 背景音乐 / 掌声 / 笑声 / 哄堂大笑 / 哭声 / 喷嚏声 | `[声音]`,BGM 连续段只标一次 |
| **情感** | 开心 / 难过 / 激动 / 紧张 / 惊讶 / 厌恶 | SRT 加 `（情感）` 前缀;ASS 着色 |
| **语种** | zh / en / ja / ko / yue / … | 自动识别(无需手选) |

> 💡 适合场景:为听障观众制作无障碍字幕(SDH)、为视频/播客做内容审核与情绪分析、
> 语言学习者对照语气、短视频创作者快速定位高光情绪片段。

## 🚀 快速开始

### 1. 安装依赖

需要 **Python 3.10 – 3.14**(已在 Windows / 3.14 验证)。

```bash
# 克隆
git clone https://github.com/Ha22yX/sensevoice-subtitle-generator.git
cd sensevoice-subtitle-generator

# 创建虚拟环境(任选其一)
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 下载模型(首次,约 1.1 GB)

```bash
python download_models.py
```

模型默认存放在**纯 ASCII 路径**下(自动选择):

- 项目路径为纯 ASCII 时 → 项目下的 `models/`
- 否则(例如项目放在中文文件夹里)→ 用户缓存目录
  - Windows:`%LOCALAPPDATA%\subtitle-generator\models`
  - macOS / Linux:`~/.cache/subtitle-generator/models`

> ⚠️ **为什么?** ONNX Runtime 在 Windows 上对**含中文等非 ASCII 字符的模型路径**加载会损坏,
> 导致解码时报 `invalid unordered_map key`。本项目会自动检测并规避此问题。
> 如需自定义模型位置,设置环境变量 `SUB_MODELS_DIR`(须为 ASCII 路径)。

**国内下载缓慢或失败**时,可设置环境变量 `SUB_MODELS_BASE` 指向镜像:

```powershell
# Windows PowerShell
$env:SUB_MODELS_BASE = "https://你的镜像地址/asr-models"
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

浏览器会自动打开 <http://127.0.0.1:7860>。上传视频 → 选择选项 → 点 **「生成字幕」** →
在 SRT / VTT 标签页预览并下载。

> 💡 也可以**跳过第 2 步**,首次点击「生成字幕」时会自动下载模型。

## ⚙️ 选项说明

| 选项 | 说明 |
|------|------|
| **字幕模式** | `普通字幕`(SRT / VTT)或 `无障碍 SDH`(带声音/情感标注的 SRT + 按情感着色的 ASS),详见上节。 |
| **模型精度** | `int8`(默认,更快、更小)或 `全量`(略准)。 |
| **推理线程数** | CPU 推理线程数,默认按 CPU 核数自动取值。 |
| **GPU 加速** | 勾选后尝试用 CUDA;需自行安装带 CUDA 的 sherpa-onnx(见下),失败自动回退 CPU。 |

### 可选:GPU 加速(CUDA)

默认的 `sherpa-onnx` 是 CPU 版,任何电脑都能跑。若你有 NVIDIA 显卡并希望加速,
安装 CUDA 版 sherpa-onnx 后勾选「GPU 加速」即可(代码会自动探测、失败回退 CPU):

```bash
pip uninstall sherpa-onnx
# 按你的 CUDA 版本参考官方文档安装 GPU 版:
# https://k2-fsa.github.io/sherpa/onnx/install/index.html
```

## 📁 项目结构

```
.
├── app.py                 # Gradio 网页界面入口
├── download_models.py     # 模型下载(首次运行)
├── requirements.txt
├── subtitle_gen/          # 核心包
│   ├── audio.py           # ffmpeg 抽音频 / 探测时长
│   ├── transcribe.py      # VAD 分段 + SenseVoice 转写(含情感/事件)
│   ├── subtitles.py       # SRT / VTT 格式化
│   └── sdh.py             # 无障碍 SDH(SRT + ASS,声音/情感标注)
├── models/                # 运行时下载(不入库;项目路径含非 ASCII 时改用用户缓存目录)
└── outputs/               # 生成的字幕(不入库)
```

## 🧰 技术栈

- **[SenseVoice](https://github.com/FunAudioLLM/SenseVoice)**(FunAudioLLM)—— 多语种语音识别模型
- **[sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx)**(k2-fsa)—— Next-gen Kaldi 的 ONNX 推理引擎
- **[silero-vad](https://github.com/snakers4/silero-vad)** —— 语音活动检测
- **[Gradio](https://gradio.app)** —— 网页界面
- **[imageio-ffmpeg](https://github.com/imageio/imageio-ffmpeg)** —— 自带 ffmpeg 二进制

## ❓ 常见问题

**Q:时间戳为什么是"一句一段",而不是逐字?**
A:本工具采用 VAD 分段产生段级时间戳,稳定可靠,足以满足绝大多数字幕场景。
逐字(卡拉 OK 式)需要逐字时间戳,目前作为后续可选增强。

**Q:识别结果没有标点 / 标点不对?**
A:SenseVoice 已开启逆文本正则化(ITN),会自动加标点与数字归一化。

**Q:报错"找不到 ffmpeg"?**
A:不会。ffmpeg 由 `imageio-ffmpeg` 在 pip 安装时自带,无需单独安装。
若仍报错,确认 `requirements.txt` 已完整安装。

**Q:报错 `invalid unordered_map key` 或模型加载失败?**
A:这是 ONNX Runtime 在 Windows 上对**含中文等非 ASCII 字符的模型路径**的已知问题。
本工具已自动把模型放到纯 ASCII 路径(项目路径含中文时用用户缓存目录)。
若仍遇到,确认用环境变量 `SUB_MODELS_DIR` 指定一个纯 ASCII 目录后重跑
`python download_models.py`。

**Q:支持音频文件吗?**
A:界面面向视频;底层基于 ffmpeg,音频文件同样可被处理(可参考 `subtitle_gen` 自行调用)。

## 🤝 贡献

欢迎提 Issue 与 PR!例如:逐字时间戳、批量处理、更多字幕样式、CLI 工具等。

## 📄 许可证

- **本项目代码**:[MIT License](./LICENSE)。
- **模型**:本项目**不**内置或分发模型,模型在运行时下载,版权归各自所有,
  请遵守其各自许可:[SenseVoice](https://github.com/FunAudioLLM/SenseVoice) ·
  [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx) ·
  [silero-vad](https://github.com/snakers4/silero-vad)。

## 🙏 致谢

感谢以上开源项目让本工具成为可能。

<div align="center">

如果这个项目对你有帮助,欢迎 ⭐ Star 支持!

</div>
