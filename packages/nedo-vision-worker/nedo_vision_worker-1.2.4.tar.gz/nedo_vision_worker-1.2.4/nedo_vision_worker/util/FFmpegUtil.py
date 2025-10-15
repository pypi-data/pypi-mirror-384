import logging
import subprocess
import re
from typing import Dict, Any, Tuple, List


def get_ffmpeg_version() -> Tuple[int, int, int]:
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if result.returncode == 0:
            m = re.search(r"ffmpeg version n?(\d+)\.(\d+)(?:\.(\d+))?", result.stdout)
            if m:
                major = int(m.group(1))
                minor = int(m.group(2))
                patch = int(m.group(3)) if m.group(3) else 0
                return major, minor, patch
    except Exception as e:
        logging.warning(f"Could not determine FFmpeg version: {e}")
    return 4, 4, 1


def _supports_rw_timeout(v: Tuple[int, int, int]) -> bool:
    major, minor, _ = v
    return major >= 5 or (major == 4 and minor >= 3)


def get_rtsp_ffmpeg_options() -> Dict[str, Any]:
    v = get_ffmpeg_version()

    opts = {
        "rtsp_transport": "tcp",
        "probesize": "256k",
        "analyzeduration": "1000000",
        "buffer_size": "1024000",
        "max_delay": "700000",
        "fflags": "nobuffer+genpts",
    }

    if _supports_rw_timeout(v):
        opts["rw_timeout"] = "5000000"
    else:
        opts["stimeout"] = "5000000"

    return opts


def get_rtsp_probe_options() -> List[str]:
    v = get_ffmpeg_version()

    opts = [
        "-v", "error",
        "-rtsp_transport", "tcp",
        "-probesize", "256k",
        "-analyzeduration", "1000000",
    ]

    opts += ["-rw_timeout" if _supports_rw_timeout(v) else "-stimeout", "5000000"]
    return opts


def get_stream_timeout_duration(t: str) -> int:
    return {
        "rtsp": 30,
        "hls": 20,
        "direct": 10,
        "video_file": 5,
    }.get(t, 15)
