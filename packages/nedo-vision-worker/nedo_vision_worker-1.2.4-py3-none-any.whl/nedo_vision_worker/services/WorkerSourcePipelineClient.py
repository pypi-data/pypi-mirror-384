import logging
import os
import time
import subprocess
from urllib.parse import urlparse
from pathlib import Path

from ..database.DatabaseManager import _get_storage_paths
from ..repositories.WorkerSourcePipelineDebugRepository import WorkerSourcePipelineDebugRepository
from ..repositories.WorkerSourcePipelineDetectionRepository import WorkerSourcePipelineDetectionRepository
from ..util.FFmpegUtil import (
    get_rtsp_ffmpeg_options,
    get_stream_timeout_duration,
    get_ffmpeg_version,
)
from .GrpcClientBase import GrpcClientBase
from .SharedDirectDeviceClient import SharedDirectDeviceClient
from ..protos.WorkerSourcePipelineService_pb2_grpc import WorkerSourcePipelineServiceStub
from ..protos.WorkerSourcePipelineService_pb2 import (
    GetListByWorkerIdRequest,
    SendPipelineImageRequest,
    UpdatePipelineStatusRequest,
    SendPipelineDebugRequest,
    SendPipelineDetectionDataRequest,
)
from ..repositories.WorkerSourcePipelineRepository import WorkerSourcePipelineRepository


class WorkerSourcePipelineClient(GrpcClientBase):
    def __init__(self, server_host: str, server_port: int = 50051):
        super().__init__(server_host, server_port)
        self.repo = WorkerSourcePipelineRepository()
        self.debug_repo = WorkerSourcePipelineDebugRepository()
        self.detection_repo = WorkerSourcePipelineDetectionRepository()
        storage_paths = _get_storage_paths()
        self.source_file_path: Path = storage_paths["files"] / "source_files"
        self.shared_device_client = SharedDirectDeviceClient()

        self.video_positions = {}
        self.last_fetch_times = {}

        try:
            self.connect(WorkerSourcePipelineServiceStub)
        except Exception as e:
            logging.error(f"Failed to connect to gRPC server: {e}")
            self.stub = None


    # ---------- small helpers ----------

    @staticmethod
    def _opts_dict_to_cli(opts: dict) -> list:
        out = []
        for k, v in opts.items():
            out += [f"-{k}", str(v)]
        return out

    @staticmethod
    def _strip_timeout_keys(d: dict) -> dict:
        o = dict(d)
        o.pop("rw_timeout", None)
        o.pop("stimeout", None)
        o.pop("timeout", None)
        return o

    @staticmethod
    def _rtsp_timeout_flag_by_version() -> str:
        major, minor, patch = get_ffmpeg_version()
        return "-timeout" if major >= 5 else "-stimeout"


    # ---------- stream detection & video position ----------

    def _detect_stream_type(self, url):
        if isinstance(url, str) and url.isdigit():
            return "direct"

        parsed_url = urlparse(url)
        if parsed_url.scheme == "rtsp":
            return "rtsp"
        if parsed_url.scheme in ["http", "https"] and url.endswith(".m3u8"):
            return "hls"
        if url.startswith("worker-source/"):
            file_path = self.source_file_path / os.path.basename(url)
            if file_path.exists():
                if file_path.suffix.lower() in (".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm", ".m4v"):
                    return "video_file"
            return "image_file"
        return "unknown"

    def _get_video_duration(self, file_path):
        try:
            file_path_str = str(file_path)
            if not os.path.exists(file_path_str):
                logging.error(f"Video file does not exist: {file_path_str}")
                return None

            import json
            cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", file_path_str]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                logging.error(f"FFprobe failed for {file_path_str}: {result.stderr}")
                return None

            try:
                probe_data = json.loads(result.stdout)
            except json.JSONDecodeError as e:
                logging.error(f"Failed to parse ffprobe output for {file_path_str}: {e}")
                return None

            if "format" not in probe_data or "duration" not in probe_data["format"]:
                logging.error(f"No duration found in probe result for {file_path_str}")
                return None

            try:
                duration_val = float(probe_data["format"]["duration"])
            except Exception as e:
                logging.error(f"Duration value not convertible to float: {e}", exc_info=True)
                return None

            if isinstance(duration_val, bool):
                logging.error("Duration value is boolean, which is invalid")
                return None

            return duration_val

        except Exception as e:
            logging.error(f"Error getting video duration for {file_path}: {e}", exc_info=True)
            return None

    def _get_current_video_position(self, video_path):
        now = time.time()

        if video_path not in self.video_positions:
            self.video_positions[video_path] = 0.0
            self.last_fetch_times[video_path] = now
            return 0.0

        current_pos = self.video_positions[video_path]
        last_fetch_time = self.last_fetch_times[video_path]
        current_pos += (now - last_fetch_time)

        duration = self._get_video_duration(video_path)
        if duration is not None and isinstance(duration, (int, float)):
            if current_pos >= duration:
                current_pos = 0.0
        else:
            if current_pos >= 120.0:
                current_pos = 0.0

        self.video_positions[video_path] = current_pos
        self.last_fetch_times[video_path] = now
        return current_pos

    def get_video_positions_status(self):
        status = {}
        for video_path, position in self.video_positions.items():
            duration = self._get_video_duration(video_path)
            last_fetch_time = self.last_fetch_times.get(video_path, None)
            time_since_last_fetch = time.time() - last_fetch_time if last_fetch_time else None

            if duration:
                status[video_path] = {
                    "current_position": position,
                    "duration": duration,
                    "progress_percent": (position / duration) * 100,
                    "last_fetch_time": last_fetch_time,
                    "time_since_last_fetch": time_since_last_fetch,
                }
            else:
                status[video_path] = {
                    "current_position": position,
                    "duration": None,
                    "progress_percent": None,
                    "last_fetch_time": last_fetch_time,
                    "time_since_last_fetch": time_since_last_fetch,
                }
        return status


    # ---------- ffmpeg cmd builders ----------

    def _build_ffmpeg_cmd_rtsp(self, url: str) -> list:
        base_opts = self._strip_timeout_keys(get_rtsp_ffmpeg_options())
        timeout_flag = self._rtsp_timeout_flag_by_version()
        in_args = self._opts_dict_to_cli(base_opts) + ["-rtsp_transport", "tcp", timeout_flag, "5000000", "-i", url]
        return ["ffmpeg", "-hide_banner", "-loglevel", "error"] + in_args + [
            "-vframes", "1", "-q:v", "2", "-f", "mjpeg", "pipe:1"
        ]

    def _build_ffmpeg_cmd_hls(self, url: str) -> list:
        in_args = ["-f", "hls", "-analyzeduration", "10000000", "-probesize", "10000000", "-i", url]
        return ["ffmpeg", "-hide_banner", "-loglevel", "error"] + in_args + [
            "-vframes", "1", "-q:v", "2", "-f", "mjpeg", "pipe:1"
        ]

    def _build_ffmpeg_cmd_video_file(self, file_path: str, pos: float) -> list:
        in_args = ["-ss", f"{pos:.3f}", "-i", file_path]
        return ["ffmpeg", "-hide_banner", "-loglevel", "error"] + in_args + [
            "-vframes", "1", "-q:v", "2", "-f", "mjpeg", "pipe:1"
        ]

    def _build_ffmpeg_cmd_image_file(self, file_path: str) -> list:
        in_args = ["-i", file_path]
        return ["ffmpeg", "-hide_banner", "-loglevel", "error"] + in_args + [
            "-vframes", "1", "-q:v", "2", "-f", "mjpeg", "pipe:1"
        ]


    # ---------- frame capture ----------

    def _get_single_frame_bytes(self, url):
        stream_type = self._detect_stream_type(url)
        proc = None

        try:
            if stream_type == "direct":
                device_index = int(url)
                logging.info(f"📹 [APP] Capturing frame from direct device: {device_index}")

                width, height, fps, pixel_format = self.shared_device_client.get_video_properties(url)
                if not width or not height:
                    logging.error(f"Failed to get properties for device {device_index}")
                    return None

                cmd = self.shared_device_client.create_ffmpeg_cli(url, width, height, fps)
                cmd += ["-vframes", "1", "-q:v", "2", "-f", "mjpeg", "pipe:1"]

            elif stream_type == "rtsp":
                cmd = self._build_ffmpeg_cmd_rtsp(url)

            elif stream_type == "hls":
                cmd = self._build_ffmpeg_cmd_hls(url)

            elif stream_type == "video_file":
                file_path = self.source_file_path / os.path.basename(url)
                if not file_path.exists():
                    logging.error(f"Video file does not exist: {file_path}")
                    return None
                pos = self._get_current_video_position(str(file_path))
                logging.info(f"🎬 [APP] Capturing video frame at {pos:.2f}s from {file_path}")
                cmd = self._build_ffmpeg_cmd_video_file(str(file_path), pos)

            elif stream_type == "image_file":
                file_path = self.source_file_path / os.path.basename(url)
                logging.info(f"🖼️ [APP] Capturing image frame from {file_path}")
                cmd = self._build_ffmpeg_cmd_image_file(str(file_path))

            else:
                logging.error(f"Unsupported stream type: {url}")
                return None

            timeout_s = get_stream_timeout_duration(stream_type)
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            try:
                stdout, stderr = proc.communicate(timeout=timeout_s)
            except subprocess.TimeoutExpired:
                proc.kill()
                stdout, stderr = proc.communicate()
                logging.error(f"FFmpeg timed out after {timeout_s}s for {stream_type} stream")
                return None

            if proc.returncode != 0:
                logging.error(f"FFmpeg error for {stream_type} stream: {(stderr or b'').decode('utf-8', 'ignore')}")
                return None

            if not stdout:
                logging.error("No data received from FFmpeg")
                return None

            return stdout

        except Exception as e:
            logging.error(f"Error capturing frame: {e}", exc_info=True)
            return None

        finally:
            if stream_type == "direct":
                try:
                    self.shared_device_client.release_device_access(url)
                except Exception:
                    pass
            if proc and proc.poll() is None:
                try:
                    proc.terminate()
                    proc.wait(timeout=2)
                except Exception:
                    try:
                        proc.kill()
                    except Exception:
                        pass


    # ---------- RPCs ----------

    def update_pipeline_status(self, pipeline_id: str, status_code: str, token: str):
        if not self.stub:
            return {"success": False, "message": "gRPC connection is not established."}

        try:
            timestamp = int(time.time() * 1000)

            request = UpdatePipelineStatusRequest(
                pipeline_id=pipeline_id,
                status_code=status_code,
                timestamp=timestamp,
                token=token,
            )
            response = self.handle_rpc(self.stub.UpdateStatus, request)

            if response and response.success:
                return {"success": True, "message": response.message}
            return {"success": False, "message": response.message if response else "Unknown error"}

        except Exception as e:
            logging.error(f"Error updating pipeline status: {e}")
            return {"success": False, "message": f"Error occurred: {e}"}

    def get_worker_source_pipeline_list(self, worker_id: str, token: str) -> dict:
        if not self.stub:
            return {"success": False, "message": "gRPC connection is not established."}

        try:
            request = GetListByWorkerIdRequest(worker_id=worker_id, token=token)
            response = self.handle_rpc(self.stub.GetListByWorkerId, request)

            if response and response.success:
                def update_status_callback(pipeline_id: str, status_code: str):
                    return self.update_pipeline_status(pipeline_id, status_code, token)

                self.repo.sync_worker_source_pipelines(response, update_status_callback)
                return {"success": True, "message": response.message, "data": response.data}

            return {"success": False, "message": response.message if response else "Unknown error"}

        except Exception as e:
            logging.error(f"Error fetching worker source pipeline list: {e}")
            return {"success": False, "message": f"Error occurred: {e}"}

    def send_pipeline_image(self, worker_source_pipeline_id: str, uuid: str, url: str, token: str):
        if not self.stub:
            return {"success": False, "message": "gRPC connection is not established."}

        try:
            frame_bytes = self._get_single_frame_bytes(url)

            if not frame_bytes:
                return {"success": False, "message": "Failed to retrieve frame from source"}

            request = SendPipelineImageRequest(
                worker_source_pipeline_id=worker_source_pipeline_id,
                uuid=uuid,
                image=frame_bytes,
                token=token,
            )
            response = self.handle_rpc(self.stub.SendPipelineImage, request)

            if response and response.success:
                return {"success": True, "message": response.message}
            return {"success": False, "message": response.message if response else "Unknown error"}

        except Exception as e:
            logging.error(f"Error sending pipeline image: {e}")
            return {"success": False, "message": f"Error occurred: {e}"}

    @staticmethod
    def read_image_as_binary(image_path: str) -> bytes:
        with open(image_path, "rb") as f:
            return f.read()

    def sync_pipeline_debug(self, token: str):
        if not self.stub:
            return {"success": False, "message": "gRPC connection is not established."}

        try:
            debug_entries = self.debug_repo.get_debug_entries_with_data()

            for debug_entry in debug_entries:
                image_binary = self.read_image_as_binary(debug_entry.image_path)

                request = SendPipelineDebugRequest(
                    worker_source_pipeline_id=debug_entry.worker_source_pipeline_id,
                    uuid=debug_entry.uuid,
                    data=debug_entry.data,
                    image=image_binary,
                    token=token,
                )
                response = self.handle_rpc(self.stub.SendPipelineDebug, request)

                if response and response.success:
                    self.debug_repo.delete_entry_by_id(debug_entry.id)
                else:
                    return {"success": False, "message": response.message if response else "Unknown error"}

            return {"success": True, "message": "Successfully synced debug entries"}

        except Exception as e:
            logging.error(f"Error syncing pipeline debug: {e}")

    def sync_pipeline_detection(self, token: str):
        if not self.stub:
            return {"success": False, "message": "gRPC connection is not established."}

        try:
            entries = self.detection_repo.get_entries()

            for entry in entries:
                image_binary = self.read_image_as_binary(entry.image_path)

                request = SendPipelineDetectionDataRequest(
                    worker_source_pipeline_id=entry.worker_source_pipeline_id,
                    data=entry.data,
                    image=image_binary,
                    timestamp=int(entry.created_at.timestamp() * 1000),
                    token=token,
                )
                response = self.handle_rpc(self.stub.SendPipelineDetectionData, request)

                if response and response.success:
                    self.detection_repo.delete_entry_by_id(entry.id)
                else:
                    return {"success": False, "message": response.message if response else "Unknown error"}

            return {"success": True, "message": "Successfully synced debug entries"}

        except Exception as e:
            logging.error(f"Error syncing pipeline debug: {e}")
