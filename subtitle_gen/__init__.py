"""字幕生成器核心包:视频 → 带时间轴字幕(SRT/VTT)。"""

from .audio import extract_audio, probe_duration, get_ffmpeg_exe
from .subtitles import to_srt, to_vtt
from .transcribe import transcribe_media, Segment

__all__ = [
    "extract_audio",
    "probe_duration",
    "get_ffmpeg_exe",
    "to_srt",
    "to_vtt",
    "transcribe_media",
    "Segment",
]
