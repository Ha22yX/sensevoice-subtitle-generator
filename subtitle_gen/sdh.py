"""无障碍(SDH)字幕:把 SenseVoice 的音频事件与情感标注进字幕。

SDH(Subtitles for Deaf and Hard of Hearing)在普通字幕基础上额外标注:
- 非语音声音:`[掌声]` `[笑声]` `[背景音乐]` `[哭声]` 等 —— 对听障观众至关重要。
- 说话情感:在 ASS 里按情感着色,在 SRT 里以 `（激动）` 等前缀提示。

这是 SenseVoice 相对 Whisper 的独特能力(Whisper 只输出纯文本),目前没有开源项目
把它的情感/事件映射成无障碍字幕。
"""
from __future__ import annotations

from .transcribe import Segment

# ---- SenseVoice 事件 -> 中文 SDH 声音标签 ----
EVENT_SOUNDS: dict[str, str] = {
    "BGM": "背景音乐",
    "Applause": "掌声",
    "Laughter": "笑声",
    "Burst_laughter": "哄堂大笑",
    "Cry": "哭声",
    "Sneeze": "喷嚏声",
}

# ---- SenseVoice 情感 -> 中文标签(NEUTRAL / EMO_UNKNOWN 不标注)----
EMOTION_LABELS: dict[str, str] = {
    "HAPPY": "开心",
    "SAD": "难过",
    "ANGRY": "激动",      # SenseVoice 对中文激情演讲常判为 ANGRY,标"激动"更贴切
    "FEARFUL": "紧张",
    "SURPRISED": "惊讶",
    "DISGUSTED": "厌恶",
}

# ---- 情感 -> ASS 颜色(&HAABBGGRR,AB=透明度,00=不透明)----
EMOTION_ASS_COLORS: dict[str, str] = {
    "HAPPY": "&H000099FF",      # 暖橙
    "SAD": "&H00CC6600",        # 蓝
    "ANGRY": "&H004040FF",      # 红
    "FEARFUL": "&H00AA33CC",    # 紫
    "SURPRISED": "&H0000D0FF",  # 金黄
    "DISGUSTED": "&H0040B040",  # 绿
    "NEUTRAL": "&H00FFFFFF",    # 白
}


def _is_notable_sound(event: str) -> bool:
    return event in {"Applause", "Laughter", "Burst_laughter", "Cry", "Sneeze"}


def _emotion_prefix(emotion: str) -> str:
    label = EMOTION_LABELS.get(emotion)
    return f"（{label}）" if label else ""


# --------------------------------------------------------------------------- #
# 时间码
# --------------------------------------------------------------------------- #
def _fmt_srt_time(t: float) -> str:
    if t < 0:
        t = 0.0
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:01d}:{m:02d}:{s:02d},{ms:03d}" if h else f"{m:02d}:{s:02d},{ms:03d}"


def _fmt_ass_time(t: float) -> str:
    """ASS 时间码 H:MM:SS.cc(百分秒)。"""
    if t < 0:
        t = 0.0
    cs = int(round(t * 100))
    h, cs = divmod(cs, 3_600_000)
    m, cs = divmod(cs, 60_000)
    s, cs = divmod(cs, 100)
    return f"{h:01d}:{m:02d}:{s:02d}.{cs:02d}"


# --------------------------------------------------------------------------- #
# SDH SRT
# --------------------------------------------------------------------------- #
def to_srt_sdh(segments: list[Segment], annotate_emotion: bool = True) -> str:
    """生成带声音与情感标注的 SRT。

    - 非语音声音(掌声/笑声/哭声…)标注为 `[声音]`;纯声音段作为独立字幕条。
    - 背景音乐(BGM)只在连续片段开头标注一次 `[背景音乐]`,避免刷屏。
    - 非中性情感在台词前加 `（激动）` 等提示(可关闭)。
    """
    lines: list[str] = []
    idx = 0
    prev_event = ""
    bgm_open = False  # 当前是否处于一段背景音乐连续区间

    for seg in segments:
        ev = seg.event
        is_bgm = ev == "BGM"
        # BGM 区间:仅在进入时标注一次
        if is_bgm and not bgm_open:
            bgm_open = True
            idx += 1
            lines += [str(idx), f"{_fmt_srt_time(seg.start)} --> {_fmt_srt_time(seg.end)}", "[背景音乐]", ""]
        elif not is_bgm:
            bgm_open = False

        if _is_notable_sound(ev):
            idx += 1
            sound = f"[{EVENT_SOUNDS[ev]}]"
            if seg.text:
                body = "\n".join([sound, (_emotion_prefix(seg.emotion) if annotate_emotion else "") + seg.text])
            else:
                body = sound
            lines += [str(idx), f"{_fmt_srt_time(seg.start)} --> {_fmt_srt_time(seg.end)}", body, ""]
        elif seg.text:
            idx += 1
            body = (_emotion_prefix(seg.emotion) if annotate_emotion else "") + seg.text
            lines += [str(idx), f"{_fmt_srt_time(seg.start)} --> {_fmt_srt_time(seg.end)}", body, ""]

        prev_event = ev

    return "\n".join(lines).strip() + "\n"


# --------------------------------------------------------------------------- #
# ASS(高级字幕:按情感着色、声音斜体)
# --------------------------------------------------------------------------- #
_ASS_HEADER = """[Script Info]
Title: SDH 字幕(SenseVoice)
ScriptType: v4.00+
WrapStyle: 0
PlayResX: {w}
PlayResY: {h}
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Microsoft YaHei,{fs},&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,{ol},1,2,90,90,60,1
Style: Sound,Microsoft YaHei,{sfs},&H00BFEAFF,&H000000FF,&H00000000,&H80000000,0,-1,0,0,100,100,0,0,1,{ol},1,2,90,90,40,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def _ass_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}").replace("\n", "\\N")


def to_ass(
    segments: list[Segment],
    *,
    width: int = 1920,
    height: int = 1080,
    annotate_emotion: bool = True,
) -> str:
    """生成 ASS 字幕:台词按情感着色,声音标注用斜体副样式。

    需支持 ASS 的播放器(VLC、mpv、MPC、PotPlayer 等)才能看到样式效果。
    """
    fs = max(28, round(width * 0.038))      # 字号随分辨率缩放
    sfs = round(fs * 0.82)
    outline = max(2, round(width / 640))
    out = [_ASS_HEADER.format(w=width, h=height, fs=fs, sfs=sfs, ol=outline)]

    prev_event = ""
    bgm_open = False
    for seg in segments:
        ev = seg.event
        is_bgm = ev == "BGM"
        if is_bgm and not bgm_open:
            bgm_open = True
            out.append(_ass_dialogue(seg.start, seg.end, "Sound", f"[{EVENT_SOUNDS['BGM']}]"))
        elif not is_bgm:
            bgm_open = False

        if _is_notable_sound(ev):
            sound_txt = f"[{EVENT_SOUNDS[ev]}]"
            if seg.text:
                out.append(_ass_dialogue(seg.start, seg.end, "Sound", sound_txt))
            else:
                out.append(_ass_dialogue(seg.start, seg.end, "Sound", sound_txt))
        if seg.text:
            color = EMOTION_ASS_COLORS.get(seg.emotion, EMOTION_ASS_COLORS["NEUTRAL"]) if annotate_emotion else EMOTION_ASS_COLORS["NEUTRAL"]
            prefix = _emotion_prefix(seg.emotion) if annotate_emotion else ""
            text = f"{{\\c{color}}}{_ass_escape(prefix + seg.text)}"
            out.append(_ass_dialogue(seg.start, seg.end, "Default", text))

        prev_event = ev

    return "\n".join(out) + "\n"


def _ass_dialogue(start: float, end: float, style: str, text: str) -> str:
    return f"Dialogue: 0,{_fmt_ass_time(start)},{_fmt_ass_time(end)},{style},,0,0,0,,{text}"
