"""音频处理工具。

依赖 imageio-ffmpeg 自带的 ffmpeg 二进制,因此用户**无需单独安装 ffmpeg** ——
这是保证"所有电脑开箱即用"的关键。

提供:
- get_ffmpeg_exe() :返回 ffmpeg 可执行文件路径
- probe_duration() :解析媒体时长(秒)
- extract_audio()  :把视频/音频抽取为 16kHz 单声道 WAV(SenseVoice 要求)
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import imageio_ffmpeg

# SenseVoice / silero-vad 统一使用 16kHz 单声道音频
SAMPLE_RATE = 16000


def get_ffmpeg_exe() -> str:
    """返回 ffmpeg 可执行文件路径。

    imageio-ffmpeg 在 pip 安装时已附带一个跨平台的 ffmpeg 二进制,
    所以无需用户额外安装系统 ffmpeg。
    """
    return imageio_ffmpeg.get_ffmpeg_exe()


_DURATION_RE = re.compile(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)")


def probe_duration(media_path: str | Path) -> float | None:
    """解析媒体时长(秒),失败返回 None。

    实现:运行 `ffmpeg -i <file>`(不指定输出),从 stderr 正则匹配
    `Duration: HH:MM:SS.ss`。注意:不带输出参数时 ffmpeg 退出码非 0 属正常。
    """
    try:
        proc = subprocess.run(
            [get_ffmpeg_exe(), "-hide_banner", "-i", str(media_path)],
            capture_output=True,
            text=True,
            timeout=120,
        )
    except Exception:
        return None
    text = (proc.stderr or "") + (proc.stdout or "")
    m = _DURATION_RE.search(text)
    if not m:
        return None
    h, mi, s = m.groups()
    return int(h) * 3600 + int(mi) * 60 + float(s)


def extract_audio(media_path: str | Path, out_wav: str | Path) -> str:
    """把视频/音频抽取为 16kHz 单声道 16-bit PCM WAV,返回输出路径。

    这是 SenseVoice 期望的输入格式。主流程(流式转写)不需要落盘 WAV,
    此函数作为独立工具/测试用途保留。
    """
    out_wav = Path(out_wav)
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        get_ffmpeg_exe(), "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(media_path),
        "-vn",            # 丢弃视频轨
        "-ac", "1",       # 单声道
        "-ar", str(SAMPLE_RATE),
        "-f", "wav", "-acodec", "pcm_s16le",
        str(out_wav),
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return str(out_wav)
