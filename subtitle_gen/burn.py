"""把字幕烧录进视频(硬字幕),输出带字幕的 MP4。

使用 imageio-ffmpeg 自带的 ffmpeg + libass。为规避 `subtitles=` 滤镜对非 ASCII
(如中文)路径的读取问题,先把字幕复制到 ASCII 临时目录、再以相对文件名引用。
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from .audio import get_ffmpeg_exe


def burn_subtitles(
    video_path: str | Path,
    subtitle_path: str | Path,
    out_path: str | Path,
) -> str:
    """把 subtitle_path(.srt/.vtt/.ass)烧录进 video_path,输出 out_path(MP4)。

    - .ass 会带完整样式(SDH 的情感着色、声音斜体等都会保留)。
    - .srt/.vtt 用 libass 默认样式。
    返回输出文件路径。失败抛 RuntimeError。
    """
    ff = get_ffmpeg_exe()
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # 用纯 ASCII 临时目录 + 相对字幕文件名,规避 subtitles 滤镜的非 ASCII 路径问题
    tmp = Path(tempfile.mkdtemp(prefix="sg_burn_"))
    sub_name = "sub" + Path(subtitle_path).suffix
    shutil.copy(subtitle_path, tmp / sub_name)

    cmd = [
        ff, "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(video_path),
        "-vf", f"subtitles={sub_name}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium",
        "-c:a", "copy",
        str(out_path),
    ]
    try:
        r = subprocess.run(cmd, cwd=str(tmp), capture_output=True, text=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    if r.returncode != 0:
        raise RuntimeError(f"ffmpeg 烧录字幕失败:{r.stderr[-500:]}")
    return str(out_path)
