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


def refine_segments(
    segments: list[Segment],
    *,
    merge_gap: float = 0.6,
    max_duration: float = 7.0,
    max_chars: int = 84,
) -> list[Segment]:
    """温和地整理片段,提升可读性(语言无关、不改时间戳来源)。

    规则:相邻两段间隔 ≤ merge_gap 秒、合并后总时长 ≤ max_duration、
    合并后字符数 ≤ max_chars、且语种相同 → 合并为一条。
    适合把 VAD 切得过碎的短碎片合并成更自然的整句。
    """
    if not segments:
        return []
    out: list[Segment] = [
        Segment(s.start, s.duration, s.text, s.lang, s.emotion, s.event) for s in segments
    ]
    merged = [out[0]]
    for cur in out[1:]:
        prev = merged[-1]
        gap = cur.start - prev.end
        joined_chars = len(prev.text) + len(cur.text) + (1 if prev.text and cur.text else 0)
        same_lang = (not prev.lang or not cur.lang) or prev.lang == cur.lang
        if (
            gap <= merge_gap
            and (cur.end - prev.start) <= max_duration
            and joined_chars <= max_chars
            and same_lang
        ):
            prev.duration = cur.end - prev.start
            prev.text = (prev.text + ("\n" if prev.text and cur.text else "") + cur.text).strip()
            # 合并后情感/事件若不一致则置空,避免给合并句误标
            if prev.emotion != cur.emotion:
                prev.emotion = ""
            if prev.event != cur.event:
                prev.event = ""
        else:
            merged.append(cur)
    return merged
