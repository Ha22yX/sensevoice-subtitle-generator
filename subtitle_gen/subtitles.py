"""SRT / VTT 字幕格式化。"""
from __future__ import annotations

from .transcribe import Segment


def _fmt_srt_time(t: float) -> str:
    """秒 → SRT 时间码 HH:MM:SS,mmm。"""
    if t < 0:
        t = 0.0
    ms_total = int(round(t * 1000))
    h, ms_total = divmod(ms_total, 3_600_000)
    m, ms_total = divmod(ms_total, 60_000)
    s, ms = divmod(ms_total, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _fmt_vtt_time(t: float) -> str:
    """秒 → VTT 时间码 HH:MM:SS.mmm。"""
    return _fmt_srt_time(t).replace(",", ".")


def to_srt(segments: list[Segment]) -> str:
    """片段列表 → SRT 字幕字符串。"""
    lines: list[str] = []
    for i, seg in enumerate(segments, 1):
        lines.append(str(i))
        lines.append(f"{_fmt_srt_time(seg.start)} --> {_fmt_srt_time(seg.end)}")
        lines.append(seg.text.strip())
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def to_vtt(segments: list[Segment]) -> str:
    """片段列表 → WebVTT 字幕字符串。"""
    lines = ["WEBVTT", ""]
    for seg in segments:
        lines.append(f"{_fmt_vtt_time(seg.start)} --> {_fmt_vtt_time(seg.end)}")
        lines.append(seg.text.strip())
        lines.append("")
    return "\n".join(lines).strip() + "\n"
