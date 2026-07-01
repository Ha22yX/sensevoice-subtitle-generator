"""VAD 分段 + SenseVoice 解码 → 带时间戳的片段。

核心流程直接对齐 sherpa-onnx 官方示例 generate-subtitles.py:

    视频/音频
      →(ffmpeg 流式取 16k 单声道 PCM)
      → silero-vad 分段
      → 每段送 SenseVoice(OfflineRecognizer)解码
      → [(start, duration, text), ...]

这种"VAD 分段 + 段级时间戳"的方案稳定可靠,是官方推荐做法
(SenseVoice 在 FunASR 里的原生字级时间戳存在已知对齐问题,故不采用)。
"""
from __future__ import annotations

import dataclasses
import subprocess
from pathlib import Path
from typing import Callable, Optional

import numpy as np
import sherpa_onnx

from .audio import SAMPLE_RATE, get_ffmpeg_exe

# 单句最大时长(秒)。VAD 在检测到超过此时长的连续语音时会内部提高阈值强制切段,
# 避免一条字幕过长、不便阅读。官方示例默认 5 秒。
DEFAULT_MAX_SPEECH_DURATION = 5.0


@dataclasses.dataclass
class Segment:
    """一条字幕片段。"""

    start: float           # 起始时间(秒)
    duration: float        # 持续时长(秒)
    text: str = ""         # 识别文本

    @property
    def end(self) -> float:
        return self.start + self.duration


def _build_recognizer(
    model: str | Path,
    tokens: str | Path,
    num_threads: int,
    use_gpu: bool,
) -> sherpa_onnx.OfflineRecognizer:
    """构建 SenseVoice 识别器;GPU 不可用时自动回退 CPU。"""
    kwargs = dict(
        model=str(model),
        tokens=str(tokens),
        num_threads=int(num_threads),
        use_itn=True,        # 逆文本正则化:加标点 / 数字归一化
        debug=False,
    )
    if use_gpu:
        try:
            # provider="cuda" 仅在带 CUDA 的 sherpa-onnx 构建上有效;
            # 普通的 CPU 轮子(本项目默认)会抛异常 → 回退到下方 CPU 调用。
            return sherpa_onnx.OfflineRecognizer.from_sense_voice(provider="cuda", **kwargs)
        except Exception:
            pass
    return sherpa_onnx.OfflineRecognizer.from_sense_voice(**kwargs)


def transcribe_media(
    media_path: str | Path,
    *,
    sense_voice_model: str | Path,
    tokens: str | Path,
    silero_vad: str | Path,
    num_threads: int = 2,
    use_gpu: bool = False,
    max_speech_duration: float = DEFAULT_MAX_SPEECH_DURATION,
    total_duration: Optional[float] = None,
    progress: Optional[Callable[[float, str], None]] = None,
) -> list[Segment]:
    """对视频/音频做 VAD 分段 + SenseVoice 转写,返回带时间戳的片段列表。

    参数
    ----
    sense_voice_model / tokens / silero_vad :模型文件路径
    num_threads        :神经网络推理线程数
    use_gpu            :是否尝试用 CUDA(失败自动回退 CPU)
    max_speech_duration:单条字幕最长时长(秒),超过则强制切段
    total_duration     :媒体总时长(秒),用于计算进度比例;None 则不上报比例
    progress           :可选回调 progress(ratio_0_1, message)
    """
    recognizer = _build_recognizer(sense_voice_model, tokens, num_threads, use_gpu)

    # ---- silero VAD 配置(参数取自官方示例)----
    vad_cfg = sherpa_onnx.VadModelConfig()
    vad_cfg.silero_vad.model = str(silero_vad)
    vad_cfg.silero_vad.threshold = 0.2
    vad_cfg.silero_vad.min_silence_duration = 0.25   # 秒
    vad_cfg.silero_vad.min_speech_duration = 0.25     # 秒
    vad_cfg.silero_vad.max_speech_duration = float(max_speech_duration)
    vad_cfg.sample_rate = SAMPLE_RATE
    window_size = vad_cfg.silero_vad.window_size
    vad = sherpa_onnx.VoiceActivityDetector(vad_cfg, buffer_size_in_seconds=100)

    # ---- ffmpeg 流式输出 16k 单声道 PCM ----
    cmd = [
        get_ffmpeg_exe(), "-hide_banner", "-loglevel", "error",
        "-i", str(media_path),
        "-f", "s16le", "-acodec", "pcm_s16le",
        "-ac", "1", "-ar", str(SAMPLE_RATE), "-",
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    frames_per_read = SAMPLE_RATE * 100  # 每次读取 100 秒音频

    segments: list[Segment] = []
    buffer = np.zeros(0, dtype=np.float32)
    num_processed = 0
    is_eof = False

    if progress is not None:
        progress(0.0, "开始读取音频…")

    while not is_eof:
        # int16 每样本 2 字节
        data = proc.stdout.read(frames_per_read * 2)
        if not data:
            vad.flush()
            is_eof = True
        else:
            samples = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
            num_processed += samples.shape[0]
            buffer = np.concatenate([buffer, samples])
            while len(buffer) > window_size:
                vad.accept_waveform(buffer[:window_size])
                buffer = buffer[window_size:]

        # 取出已检测到的语音段并送识别(每轮都执行,含 EOF 轮)
        streams: list = []
        segs: list[Segment] = []
        while not vad.empty():
            front = vad.front
            segs.append(Segment(
                start=front.start / SAMPLE_RATE,
                duration=len(front.samples) / SAMPLE_RATE,
            ))
            stream = recognizer.create_stream()
            stream.accept_waveform(SAMPLE_RATE, front.samples)
            streams.append(stream)
            vad.pop()
        for seg, stream in zip(segs, streams):
            try:
                recognizer.decode_stream(stream)
                text = stream.result.text.strip()
            except Exception:
                # 个别过短或纯噪声的片段可能触发解码异常,跳过该条不影响整体字幕
                continue
            if text in ("", ".", "The."):
                continue
            seg.text = text
            segments.append(seg)

        if progress is not None and not is_eof:
            if total_duration:
                ratio = min(0.99, num_processed / (SAMPLE_RATE * total_duration))
                progress(ratio, f"识别中… 已完成 {ratio * 100:.0f}%")
            else:
                progress(0.5, "识别中…")

    try:
        proc.stdout.close()
    except Exception:
        pass
    proc.wait()

    if progress is not None:
        progress(1.0, "识别完成")

    return segments
