#!/usr/bin/env python3
"""视频自动字幕生成器 —— Gradio 网页界面。

导入视频 → silero-vad 分段 → SenseVoice 识别 → 生成带时间轴的 SRT / VTT。

运行:
    python app.py
然后浏览器打开 http://127.0.0.1:7860
"""
from __future__ import annotations

import os
from pathlib import Path

import gradio as gr

from download_models import ensure_models, model_paths
from subtitle_gen import (
    probe_duration,
    to_srt, to_vtt, to_srt_sdh, to_ass,
    transcribe_media,
)

# 推理线程数默认值(不超过 4,避免在小机器上反而变慢)
DEFAULT_THREADS = min(4, max(1, (os.cpu_count() or 4) - 1))

# GitHub 仓库地址(创建后填入;README 链接也用这个)
REPO_URL = "https://github.com/Ha22yX/sensevoice-subtitle-generator"

OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"

# --------------------------------------------------------------------------- #
# 主题与样式
# --------------------------------------------------------------------------- #
def build_theme() -> gr.themes.Base:
    """靛蓝强调色 + 柔和圆角 + 系统字体(离线自动回退)。"""
    return gr.themes.Soft(
        primary_hue="indigo",
        secondary_hue="slate",
        neutral_hue="slate",
        radius_size="lg",
        text_size="md",
        font=[
            "ui-sans-serif", "system-ui", "-apple-system", "Segoe UI",
            "PingFang SC", "Microsoft YaHei", "Noto Sans SC", "sans-serif",
        ],
        font_mono=[
            "ui-monospace", "SFMono-Regular", "Menlo", "Consolas", "monospace",
        ],
    ).set(
        body_background_fill="#F6F7FB",
        body_text_color="#0F172A",
        block_background_fill="#FFFFFF",
        block_border_color="#E7E9F3",
        block_border_width="1px",
        block_radius="18px",
        block_shadow="0 1px 2px rgba(15,23,42,.04), 0 12px 32px rgba(15,23,42,.05)",
        block_title_text_weight="600",
        button_primary_background_fill="linear-gradient(135deg,#4F46E5 0%,#7C3AED 100%)",
        button_primary_background_fill_hover="linear-gradient(135deg,#4338CA 0%,#6D28D9 100%)",
        button_primary_text_color="#FFFFFF",
        button_primary_border_color="transparent",
        button_large_padding="14px 24px",
        input_background_fill="#FFFFFF",
        input_border_color="#E2E8F0",
        input_radius="12px",
        checkbox_background_color="#FFFFFF",
    )


CSS = """
/* 全局 */
.gradio-container { max-width: 1120px !important; }
footer { display: none !important; }

/* Hero */
#hero { text-align:center; padding: 30px 12px 10px; }
#hero .logo { font-size: 46px; line-height: 1; }
#hero h1 {
  font-size: 32px; font-weight: 800; letter-spacing: -0.02em; margin: 10px 0 8px;
  background: linear-gradient(135deg,#4F46E5,#7C3AED);
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
#hero .sub { color:#64748B; font-size: 15px; margin: 0 auto; max-width: 620px; line-height: 1.65; }
#hero .pills { margin-top: 14px; display:flex; gap:8px; justify-content:center; flex-wrap:wrap; }
#hero .pill {
  font-size: 12px; color:#475569; background:#EEF0F8; border:1px solid #E2E8F0;
  padding:5px 11px; border-radius:999px; font-weight:500;
}

/* 主按钮:渐变阴影 + 悬停微动 */
button.primary {
  box-shadow: 0 8px 22px rgba(79,70,229,.28) !important;
  transition: transform .16s ease, filter .16s ease, box-shadow .16s ease !important;
}
button.primary:hover { transform: translateY(-1px); filter: brightness(1.04); }

/* 视频预览圆角 */
video { border-radius: 14px !important; }

/* 字幕预览:等宽 */
.srt-preview textarea {
  font-family: 'JetBrains Mono', ui-monospace, Consolas, monospace !important;
  font-size: 13px !important; line-height: 1.65 !important;
}

/* 选项卡标题 */
.tab-nav { border-bottom: 1px solid #E7E9F3 !important; }

/* Footer */
#foot { text-align:center; color:#94A3B8; font-size:12px; padding: 16px 0 4px; }
#foot a { color:#6366F1; text-decoration:none; font-weight:500; }
#foot a:hover { text-decoration: underline; }
"""


HERO_HTML = """
<div class="logo">🎬</div>
<h1>视频自动字幕生成器</h1>
<p class="sub">导入视频,AI 自动生成带时间轴的字幕。基于 SenseVoice 多语种语音识别,
全程本地运行,无需联网、无需 API Key。</p>
<div class="pills">
  <span class="pill">⚡ SenseVoice</span>
  <span class="pill">🌍 中 · 英 · 日 · 韩 · 粤</span>
  <span class="pill">♿ 无障碍 SDH</span>
  <span class="pill">🔒 100% 本地</span>
  <span class="pill">💚 开源</span>
</div>
"""

FOOTER_HTML = f"""
基于 <a href="https://github.com/k2-fsa/sherpa-onnx" target="_blank">sherpa-onnx</a> ·
<a href="https://github.com/FunAudioLLM/SenseVoice" target="_blank">SenseVoice</a> ·
silero-vad 构建 &nbsp;|&nbsp;
<a href="{REPO_URL}" target="_blank">GitHub 项目</a>
<div style="margin-top:6px;">模型在运行时下载,使用即代表你同意其各自的许可协议。</div>
"""


# --------------------------------------------------------------------------- #
# 业务逻辑
# --------------------------------------------------------------------------- #
def generate(video_path, mode, quality, num_threads, use_gpu, progress=gr.Progress()):
    """点击"生成字幕"的处理函数。

    mode:
      - 普通字幕:输出 SRT + VTT
      - 无障碍 SDH:输出带声音/情感标注的 SDH-SRT + 按情感着色的 ASS
    """
    if not video_path:
        raise gr.Error("请先上传一个视频文件 🎬")

    sdh = "SDH" in str(mode)

    # 1) 确保模型就绪(首次会下载,约 1.1GB)
    progress(0.02, desc="检查模型(首次将自动下载,请耐心)…")
    try:
        paths = ensure_models()
    except Exception as e:  # noqa: BLE001
        raise gr.Error(
            f"模型下载失败:{e}\n"
            "可设置环境变量 SUB_MODELS_BASE 指向镜像后重试。"
        )

    want_int8 = str(quality).startswith("int8")
    model_file = paths["model_int8"] if want_int8 else paths["model_full"]
    if not model_file.is_file():           # 退而求其次,用存在的那个
        model_file = paths["model_full"] if paths["model_full"].is_file() else paths["model_int8"]
    if not model_file.is_file():
        raise gr.Error("找不到 SenseVoice 模型,请重新运行 python download_models.py")

    # 2) 探测时长(用于进度)
    progress(0.08, desc="分析视频…")
    total = probe_duration(video_path)

    def _p(ratio: float, msg: str) -> None:
        progress(0.1 + 0.85 * ratio, desc=msg)

    # 3) 转写(同时获取 语种 / 情感 / 音频事件)
    progress(0.1, desc="加载模型并识别(首次加载需数秒)…")
    segs = transcribe_media(
        video_path,
        sense_voice_model=model_file,
        tokens=paths["tokens"],
        silero_vad=paths["vad"],
        num_threads=int(num_threads),
        use_gpu=bool(use_gpu),
        total_duration=total,
        progress=_p,
    )
    if not segs:
        raise gr.Error("未识别到任何语音,请确认视频里有人声。")

    # 4) 按模式生成字幕并落盘
    progress(0.96, desc="生成字幕文件…")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    base = Path(video_path).stem or "subtitle"
    if sdh:
        text1 = to_srt_sdh(segs)
        text2 = to_ass(segs)
        ext1, ext2 = "srt", "ass"
        lab1 = "SDH · SRT 预览(含声音 / 情感标注)"
        lab2 = "SDH · ASS 预览(按情感着色,需 VLC/PotPlayer/mpv 等)"
        file_lab1, file_lab2 = "下载 .srt(SDH)", "下载 .ass(SDH)"
        tab1, tab2 = "SDH · SRT", "SDH · ASS"
    else:
        text1 = to_srt(segs)
        text2 = to_vtt(segs)
        ext1, ext2 = "srt", "vtt"
        lab1, lab2 = "SRT 预览", "VTT 预览"
        file_lab1, file_lab2 = "下载 .srt", "下载 .vtt"
        tab1, tab2 = "SRT", "VTT"

    f1 = OUTPUT_DIR / f"{base}.{ext1}"
    f2 = OUTPUT_DIR / f"{base}.{ext2}"
    f1.write_text(text1, encoding="utf-8")
    f2.write_text(text2, encoding="utf-8")

    progress(1.0, desc="完成 🎉")
    dur_txt = f" · 时长 {total:.0f}s" if total else ""
    if sdh:
        n_emo = sum(1 for s in segs if s.emotion and s.emotion not in ("NEUTRAL", "EMO_UNKNOWN"))
        n_snd = sum(1 for s in segs if s.event and s.event != "Speech")
        extra = f" · 标注情感 {n_emo} 条、声音 {n_snd} 条"
    else:
        extra = ""
    status_md = (
        f"### ✅ 完成:共 **{len(segs)}** 条字幕{dur_txt}{extra}\n\n"
        f"已生成 **{ext1.upper()}** 与 **{ext2.upper()}**,可在上方标签页预览或下载。"
    )
    return (
        gr.update(value=text1, label=lab1),
        gr.update(value=str(f1), label=file_lab1),
        gr.update(value=text2, label=lab2),
        gr.update(value=str(f2), label=file_lab2),
        gr.update(label=tab1),
        gr.update(label=tab2),
        status_md,
    )


def startup_hint() -> str:
    """启动时给一句模型状态提示。"""
    p = model_paths()
    ready = (p["model_full"].is_file() or p["model_int8"].is_file()) and p["vad"].is_file()
    if ready:
        return "_✅ 模型已就绪,上传视频后点击「生成字幕」即可。_"
    return (
        "_⏳ 模型尚未下载(首次约 1.1GB)。可先运行 `python download_models.py`,"
        "或直接点击「生成字幕」会自动下载。_"
    )


# --------------------------------------------------------------------------- #
# 界面
# --------------------------------------------------------------------------- #
def build_ui() -> gr.Blocks:
    # 注意:Gradio 6.0 起 theme / css 从 Blocks() 移到了 launch()
    with gr.Blocks(title="字幕生成器 · SenseVoice") as demo:
        gr.HTML(HERO_HTML, elem_id="hero")

        with gr.Row(equal_height=False):
            # 左:上传 + 预览
            with gr.Column(scale=5, min_width=360):
                video = gr.Video(
                    label="上传视频",
                    sources=["upload"],
                    height=300,
                    interactive=True,
                )
            # 右:选项 + 按钮
            with gr.Column(scale=4, min_width=320):
                gr.Markdown("### ⚙️ 选项")
                mode = gr.Radio(
                    choices=["普通字幕 (SRT/VTT)", "无障碍 SDH 字幕 (声音+情感标注)"],
                    value="普通字幕 (SRT/VTT)",
                    label="字幕模式",
                )
                quality = gr.Radio(
                    choices=["int8(更快·默认)", "全量(略准)"],
                    value="int8(更快·默认)",
                    label="模型精度",
                )
                threads = gr.Slider(
                    minimum=1, maximum=16, step=1,
                    value=DEFAULT_THREADS, label="推理线程数",
                )
                use_gpu = gr.Checkbox(
                    value=False,
                    label="GPU 加速(需自行安装 CUDA 版 sherpa-onnx)",
                )
                gen_btn = gr.Button("✨ 生成字幕", variant="primary", size="lg")
                status = gr.Markdown(startup_hint())

        with gr.Tabs():
            with gr.Tab("SRT", id="tab1") as tab1:
                srt_box = gr.Textbox(
                    label="SRT 预览", lines=14, max_lines=40,
                    elem_classes="srt-preview", interactive=False,
                )
                srt_file = gr.File(label="下载 .srt", file_types=[".srt", ".vtt", ".ass"])
            with gr.Tab("VTT", id="tab2") as tab2:
                vtt_box = gr.Textbox(
                    label="VTT 预览", lines=14, max_lines=40,
                    elem_classes="srt-preview", interactive=False,
                )
                vtt_file = gr.File(label="下载 .vtt", file_types=[".srt", ".vtt", ".ass"])

        gr.HTML(FOOTER_HTML, elem_id="foot")

        gen_btn.click(
            fn=generate,
            inputs=[video, mode, quality, threads, use_gpu],
            outputs=[srt_box, srt_file, vtt_box, vtt_file, tab1, tab2, status],
        )

    return demo


if __name__ == "__main__":
    app = build_ui()
    app.queue().launch(
        theme=build_theme(),
        css=CSS,
        server_name="127.0.0.1",
        server_port=7860,
        inbrowser=True,
        show_error=True,
    )
