"""字幕生成器核心包:视频 → 带时间轴字幕(SRT/VTT/SDH/ASS)+ 烧录。"""

from .audio import extract_audio, probe_duration, get_ffmpeg_exe
from .subtitles import to_srt, to_vtt, refine_segments
from .sdh import to_srt_sdh, to_ass
from .burn import burn_subtitles
from .transcribe import transcribe_media, Segment

__all__ = [
    "extract_audio",
    "probe_duration",
    "get_ffmpeg_exe",
    "to_srt",
    "to_vtt",
    "refine_segments",
    "to_srt_sdh",
    "to_ass",
    "burn_subtitles",
    "transcribe_media",
    "Segment",
]
