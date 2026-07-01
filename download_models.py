#!/usr/bin/env python3
"""首次运行下载 SenseVoice 与 silero-vad 模型到 ./models/。

主源为 k2-fsa GitHub releases(官方示例同源)。国内若下载缓慢/失败,可设置
环境变量 SUB_MODELS_BASE 指向任意托管了相同文件名的镜像,例如:

    # Windows PowerShell
    $env:SUB_MODELS_BASE = "https://your-mirror.example/asr-models"
    python download_models.py

模型不会被打包进 git(体积大),由本脚本在运行时下载。
直接运行 `python download_models.py` 即可。
"""
from __future__ import annotations

import os
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

# Windows 中文控制台默认 GBK 编码,打印 emoji 等字符会抛 UnicodeEncodeError。
# 这里把标准输出/错误流强制为 UTF-8,保证在任意 Windows 控制台都不崩。
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def _models_root() -> Path:
    """返回模型存放目录。

    默认放在项目根目录下的 ``models/``。但 **ONNX Runtime 在 Windows 上对含非
    ASCII 字符(如中文)的模型路径会加载损坏**,导致解码时抛
    ``invalid unordered_map key``。因此若默认路径含非 ASCII 字符,自动改用纯 ASCII
    的用户缓存目录。可用环境变量 ``SUB_MODELS_DIR`` 显式指定任意目录。
    """
    env = os.environ.get("SUB_MODELS_DIR")
    if env:
        root = Path(env)
    else:
        root = Path(__file__).resolve().parent / "models"
        if not str(root).isascii():
            if os.name == "nt":
                base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
            else:
                base = str(Path.home() / ".cache")
            root = Path(base) / "subtitle-generator" / "models"
            if not str(root).isascii():
                root = Path(tempfile.gettempdir()) / "subtitle-generator" / "models"
    root.mkdir(parents=True, exist_ok=True)
    return root


# 模型存放目录(可能位于项目下,也可能位于用户缓存,取决于路径是否为纯 ASCII)
MODEL_DIR = _models_root()

# SenseVoice(zh/en/ja/ko/yue 多语种)官方 ONNX 导出
SENSE_NAME = "sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17"
SENSE_TARBALL = f"{SENSE_NAME}.tar.bz2"
VAD_NAME = "silero_vad.onnx"

# 官方发布源(可被环境变量 SUB_MODELS_BASE 覆盖)
DEFAULT_BASE = "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models"


def model_paths() -> dict[str, Path]:
    """返回各模型文件的期望路径(可能尚不存在)。"""
    sense_dir = MODEL_DIR / SENSE_NAME
    return {
        "sense_dir": sense_dir,
        "tokens": sense_dir / "tokens.txt",
        "model_int8": sense_dir / "model.int8.onnx",
        "model_full": sense_dir / "model.onnx",
        "vad": MODEL_DIR / VAD_NAME,
    }


def _download(url: str, dest: Path) -> None:
    """下载 url 到 dest,带简单进度打印。"""
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    print(f"下载 {url}")
    print(f"  → {dest}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as resp, open(tmp, "wb") as f:
        total = int(resp.headers.get("Content-Length") or 0)
        done = 0
        chunk = 1 << 20  # 1 MiB
        while True:
            buf = resp.read(chunk)
            if not buf:
                break
            f.write(buf)
            done += len(buf)
            if total:
                pct = done * 100 / total
                print(f"\r  {done / 1e6:7.1f} / {total / 1e6:.1f} MB  ({pct:5.1f}%)", end="", flush=True)
            else:
                print(f"\r  {done / 1e6:.1f} MB", end="", flush=True)
    print()
    tmp.replace(dest)


def _extract(tarball: Path) -> None:
    """解压 tar.bz2 到 MODEL_DIR(Python 3.12+ 使用安全的 data 过滤器)。"""
    print("解压模型…")
    with tarfile.open(tarball, "r:bz2") as t:
        try:
            t.extractall(MODEL_DIR, filter="data")  # 3.12+
        except TypeError:
            t.extractall(MODEL_DIR)                 # 3.10 / 3.11


def ensure_models() -> dict[str, Path]:
    """确保模型就绪(缺失则下载),返回 model_paths()。"""
    paths = model_paths()
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    base = os.environ.get("SUB_MODELS_BASE", DEFAULT_BASE).rstrip("/")

    # 1) SenseVoice:两个 onnx 都缺失才需要下载
    if not paths["model_full"].is_file() and not paths["model_int8"].is_file():
        tarball = MODEL_DIR / SENSE_TARBALL
        if not tarball.is_file():
            _download(f"{base}/{SENSE_TARBALL}", tarball)
        _extract(tarball)
        tarball.unlink(missing_ok=True)  # 解压后删除压缩包,省空间

    # 2) silero-vad
    if not paths["vad"].is_file():
        _download(f"{base}/{VAD_NAME}", paths["vad"])

    return paths


def status() -> None:
    """打印模型就绪状态。"""
    paths = model_paths()
    print("\n模型状态:")
    for k, v in paths.items():
        ok = "OK " if v.is_file() else "缺失"
        print(f"  [{ok}] {k:12s} {v}")


if __name__ == "__main__":
    try:
        ensure_models()
    except Exception as e:  # noqa: BLE001
        print(f"\n❌ 下载失败:{e}", file=sys.stderr)
        print("可尝试设置环境变量 SUB_MODELS_BASE 指向镜像后重试。", file=sys.stderr)
        sys.exit(1)
    status()
    print("\n✅ 模型就绪,可以运行 `python app.py` 了。")
