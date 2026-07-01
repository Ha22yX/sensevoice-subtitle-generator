"""字幕生成器核心包:视频 → 带时间轴字幕(SRT/VTT/SDH/ASS)。"""

from .audio import extract_audio, probe_duration, get_ffmpeg_exe
from .subtitles import to_srt, to_vtt
from .sdh import to_srt_sdh, to_ass
from .transcribe import transcribe_media, Segment

__all__ = [
    "extract_audio",
    "probe_duration",
    "get_ffmpeg_exe",
    "to_srt",
    "to_vtt",
    "to_srt_sdh",
    "to_ass",
    "transcribe_media",
    "Segment",
]
