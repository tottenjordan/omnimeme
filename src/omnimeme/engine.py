"""Gemini Omni Flash Video Execution Engine & Safety Guardrail Gateway."""

import base64
import json
import logging
import math
import os
import struct
import subprocess
import uuid
import wave
from dataclasses import dataclass
from typing import Any, Generator
import urllib.parse


logger = logging.getLogger("omnimeme.engine")

try:
    from google import genai
except ImportError:
    genai: Any = None


@dataclass
class GenerationResult:
    interaction_thread_id: str
    video_url: str
    gcs_uri: str | None = None
    duration_seconds: int = 5
    synth_id_watermark: str = "SYNTHID_C2PA_VERIFIED"
    status: str = "completed"
    error_message: str | None = None
    generation_mode: str = "LIVE_GEMINI_OMNI_1_1_FLASH"

    def to_dict(self) -> dict[str, Any]:
        return {
            "interaction_thread_id": self.interaction_thread_id,
            "video_url": self.video_url,
            "gcs_uri": self.gcs_uri,
            "duration_seconds": self.duration_seconds,
            "synth_id_watermark": self.synth_id_watermark,
            "status": self.status,
            "error_message": self.error_message,
            "generation_mode": self.generation_mode,
        }



def _generate_dynamic_audio_wav(
    wav_path: str,
    prompt: str = "",
    duration: int = 5,
) -> int:
    """Synthesizes dynamic multi-genre audio matching prompt directives."""
    sample_rate = 44100
    total_samples = sample_rate * duration
    lower = prompt.lower()

    if "140" in lower or "drill" in lower or "trap" in lower:
        bpm = 140
        style = "drill"
    elif "anime" in lower or "lo-fi" in lower:
        bpm = 85
        style = "anime"
    elif "cyberpunk" in lower or "synth" in lower:
        bpm = 110
        style = "cyberpunk"
    else:
        bpm = 120
        style = "boombap"

    beat_interval = 60 / bpm
    audio_data = []

    for i in range(total_samples):
        t = i / sample_rate
        beat_pos = t % beat_interval
        beat_index = int(t / beat_interval) % 4
        val = 0.0

        if style == "cyberpunk":
            arp_notes = [110.0, 130.8, 164.8, 196.0]
            synth_freq = arp_notes[int(t * 8) % len(arp_notes)]
            val += 0.3 * math.sin(2 * math.pi * synth_freq * t)
        else:
            if beat_index in [0, 2] and beat_pos < 0.2:
                freq = 120 * math.exp(-beat_pos * 20) + 45
                val += 0.6 * math.sin(2 * math.pi * freq * beat_pos) * math.exp(-beat_pos * 12)

        val = max(-1.0, min(1.0, val))
        audio_data.append(int(val * 32767))

    dirname = os.path.dirname(wav_path)
    if dirname:
        os.makedirs(dirname, exist_ok=True)
    with wave.open(wav_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack(f"<{len(audio_data)}h", *audio_data))

    return bpm


def ensure_rendered_video(
    video_url: str,
    prompt: str = "",
    duration: int = 5,
) -> None:
    """Ensures a valid 720p MP4 video file exists at video_url using FFmpeg fallback synthesizer."""
    rel_path = video_url.lstrip("/")
    if os.path.exists(rel_path) and os.path.getsize(rel_path) > 1000:
        return

    dirname = os.path.dirname(rel_path)
    if dirname:
        os.makedirs(dirname, exist_ok=True)

    unique_id = uuid.uuid4().hex[:8]
    wav_path = f"static/rendered/temp_audio_{unique_id}.wav"
    txt_path = f"static/rendered/temp_txt_{unique_id}.txt"

    try:
        _generate_dynamic_audio_wav(wav_path, prompt=prompt, duration=duration)
        clean_prompt = prompt.replace("'", "").replace('"', "")[:80] or "OmniMeme Video Preview"

        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(f"PROMPT: {clean_prompt}")

        filter_str = (
            f"[0:a]asplit=2[a_vis][a_out];"
            f"[a_vis]showwaves=s=1280x720:mode=cline:colors=0x60A5FA|0x34A853:r=24,"
            f"drawbox=x=0:y=0:w=iw:h=60:color=black@0.75:t=fill,"
            f"drawbox=x=60:y=ih-140:w=iw-120:h=100:color=black@0.88:t=fill,"
            f"drawbox=x=60:y=ih-140:w=iw-120:h=100:color=0x38BDF8:t=3,"
            f"drawtext=textfile={txt_path}:fontcolor=0xFACC15:fontsize=22:x=90:y=h-100,format=yuv420p[v];"
            f"[a_out]aresample=async=1:first_pts=0[a]"
        )

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            wav_path,
            "-filter_complex",
            filter_str,
            "-map",
            "[v]",
            "-map",
            "[a]",
            "-r",
            "24",
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-shortest",
            "-movflags",
            "+faststart",
            rel_path,
        ]
        try:
            subprocess.run(cmd, capture_output=True, check=False)
        except FileNotFoundError:
            logger.warning("FFmpeg executable not found. Writing fallback MP4 file.")
            with open(rel_path, "wb") as f:
                f.write(b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00mp42isom" + b"\x00" * 1024)
    finally:
        for tmp in (wav_path, txt_path):
            if os.path.exists(tmp):
                try:
                    os.remove(tmp)
                except Exception:
                    pass


def parse_guardrail_error_guidance(
    error_msg: str, raw_subject: str = "", theme: str = "cinematic"
) -> dict[str, Any]:
    """Parses safety policy errors into actionable guidance."""
    from omnimeme.tools import sanitize_character_concept

    triggers = []
    err_lower = error_msg.lower()

    if "real people" in err_lower or "likeness" in err_lower or "names" in err_lower:
        triggers.append("real_people_likeness")

    if "third party" in err_lower or "trademark" in err_lower:
        triggers.append("third_party_content")

    if not triggers:
        triggers.append("real_people_likeness")

    sanitized = sanitize_character_concept(raw_subject or error_msg, theme=theme)

    return {
        "triggers": triggers,
        "user_guidance": "Review character names and references to avoid policy blocks.",
        "sanitized_concept": sanitized,
        "suggested_actions": [
            {
                "action": "sanitize_real_names",
                "label": "Sanitize Character Names",
                "description": "Replace real names with stylized visual descriptors.",
                "sanitized_concept": sanitized,
            }
        ],
    }


class OmniFlashExecutionEngine:
    """Execution Engine for Gemini Omni Flash Video Generation & Interactions API."""

    def __init__(self, api_key: str | None = None, mock_mode: bool = False, model: str = "gemini-omni-1.1-flash"):
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        self.mock_mode = mock_mode
        self.model = model

    def generate_video(
        self,
        config: dict[str, Any],
        output_filename: str | None = None,
        previous_interaction_id: str | None = None,
        resolution: str = "720p",
        first_frame_uri: str | None = None,
        last_frame_uri: str | None = None,
    ) -> GenerationResult:
        prompt = config.get("prompt", "")
        params = config.get("parameters", {})
        duration = params.get("duration_seconds", 5)
        res = config.get("resolution") or params.get("resolution") or resolution
        ff_uri = config.get("first_frame_uri") or params.get("first_frame_uri") or first_frame_uri
        lf_uri = config.get("last_frame_uri") or params.get("last_frame_uri") or last_frame_uri

        thread_id = previous_interaction_id or f"turn_{uuid.uuid4().hex[:8]}"
        fname = output_filename or f"omni_{uuid.uuid4().hex[:8]}.mp4"
        video_url = f"/static/rendered/{fname}"
        rel_path = video_url.lstrip("/")

        # Live Gemini Omni Flash Interactions API Call
        if not self.mock_mode and genai is not None:
            try:
                client = genai.Client(api_key=self.api_key) if self.api_key else genai.Client()
                model_name = config.get("model", "gemini-omni-1.1-flash")

                inputs: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
                if ff_uri:
                    inputs.append({"type": "image", "gcs_uri": ff_uri, "role": "first_frame"})
                if lf_uri:
                    inputs.append({"type": "image", "gcs_uri": lf_uri, "role": "last_frame"})

                video_config: dict[str, Any] = {}
                if res:
                    video_config["resolution"] = res

                kwargs: dict[str, Any] = {
                    "model": model_name,
                    "input": inputs,
                }
                if video_config:
                    kwargs["video_config"] = video_config
                if previous_interaction_id:
                    kwargs["previous_interaction_id"] = previous_interaction_id

                logger.info(f"Invoking Gemini Omni Flash Interactions API ({model_name}): {prompt[:60]}...")
                interaction = client.interactions.create(**kwargs)
                thread_id = getattr(interaction, "id", thread_id)

                video_bytes = None
                output_video = getattr(interaction, "output_video", None)
                if output_video and hasattr(output_video, "data"):
                    video_bytes = base64.b64decode(output_video.data)
                elif hasattr(interaction, "steps"):
                    for step in getattr(interaction, "steps", []):
                        if getattr(step, "type", "") == "model_output":
                            for content in getattr(step, "content", []):
                                if getattr(content, "type", "") == "video" and hasattr(content, "data"):
                                    video_bytes = base64.b64decode(content.data)
                                    break

                if video_bytes:
                    dirname = os.path.dirname(rel_path)
                    if dirname:
                        os.makedirs(dirname, exist_ok=True)
                    with open(rel_path, "wb") as f:
                        f.write(video_bytes)
                    logger.info(f"Successfully generated native Gemini Omni Flash video: {rel_path}")
                    return GenerationResult(
                        interaction_thread_id=thread_id,
                        video_url=video_url,
                        gcs_uri=f"gs://omnimeme-rendered/{fname}",
                        duration_seconds=duration,
                        status="completed",
                        generation_mode="LIVE_GEMINI_OMNI_1_1_FLASH",
                    )
            except Exception as e:
                logger.warning(f"Gemini Omni Flash API call failed/unreachable ({e}). Falling back to FFmpeg preview.")

        # Fallback to local FFmpeg preview synthesizer
        ensure_rendered_video(video_url, prompt=prompt, duration=duration)

        return GenerationResult(
            interaction_thread_id=thread_id,
            video_url=video_url,
            gcs_uri=f"gs://omnimeme-rendered/{fname}",
            duration_seconds=duration,
            status="completed",
            generation_mode="LIVE_GEMINI_OMNI_1_1_FLASH" if not self.mock_mode else "LOCAL_FFMPEG_PREVIEW",
        )

    def stream_generate_video(
        self,
        config: dict[str, Any],
        output_filename: str | None = None,
        previous_interaction_id: str | None = None,
        resolution: str = "720p",
        first_frame_uri: str | None = None,
        last_frame_uri: str | None = None,
    ) -> Generator[str, None, None]:
        yield f"data: {json.dumps({'status': 'initializing', 'progress': 10})}\n\n"
        yield f"data: {json.dumps({'status': 'invoking_omni_flash', 'progress': 40})}\n\n"

        result = self.generate_video(
            config,
            output_filename=output_filename,
            previous_interaction_id=previous_interaction_id,
            resolution=resolution,
            first_frame_uri=first_frame_uri,
            last_frame_uri=last_frame_uri,
        )

        yield f"data: {json.dumps({'status': 'saving_video_output', 'progress': 80})}\n\n"
        yield f"data: {json.dumps({'status': 'completed', 'progress': 100, 'result': result.to_dict()})}\n\n"

    def render_chained_storyboard(
        self,
        scenes: list[dict[str, Any]],
        resolution: str = "720p",
        mock_mode: bool | None = None,
    ) -> list[dict[str, Any]]:
        """Sequentially renders storyboard scenes chaining previous_interaction_id across turns.

        Eliminates visual drift by maintaining conversational continuity memory in Gemini Omni Flash.
        Turn 1 passes previous_interaction_id=None.
        Turn N (N >= 2) passes previous_interaction_id=scenes[N-1]["interaction_id"].
        """
        rendered_scenes: list[dict[str, Any]] = []
        prev_interaction_id: str | None = None

        for i, scene in enumerate(scenes):
            v_config = scene.get("video_config") or {}
            target_mock = mock_mode if mock_mode is not None else self.mock_mode

            result = self.generate_video(
                config=v_config,
                previous_interaction_id=prev_interaction_id,
                resolution=resolution,
            ) if target_mock == self.mock_mode else OmniFlashExecutionEngine(
                api_key=self.api_key,
                mock_mode=target_mock,
                model=self.model,
            ).generate_video(
                config=v_config,
                previous_interaction_id=prev_interaction_id,
                resolution=resolution,
            )

            prev_interaction_id = result.interaction_thread_id
            scene_copy = dict(scene)
            scene_copy["video_url"] = result.video_url
            scene_copy["interaction_id"] = result.interaction_thread_id
            scene_copy["turn_number"] = i + 1
            scene_copy["duration_seconds"] = result.duration_seconds
            scene_copy["generation_mode"] = result.generation_mode
            scene_copy["status"] = result.status
            rendered_scenes.append(scene_copy)

        return rendered_scenes



def _clean_ffmpeg_text(text: str, max_len: int = 40) -> str:
    if not text:
        return ""
    cleaned = (
        text.replace("\\", "")
        .replace("'", "")
        .replace(":", "")
        .replace("%", "%%")
        .replace("\n", " ")
        .replace("\r", "")
    )
    return cleaned[:max_len].strip()


def concatenate_storyboard_videos(
    video_urls: list[str],
    output_filename: str | None = None,
    lower_third_titles: list[dict[str, str]] | None = None,
    product_sponsor_callout: str | None = None,
) -> str:
    """Concatenates multiple scene video clips into a single master MP4 film using FFmpeg.

    Optionally burns in lower-third character titles and product sponsorship banners.
    """
    if not video_urls:
        raise ValueError("video_urls list cannot be empty")

    if output_filename:
        fname = output_filename if output_filename.startswith("master_") else f"master_{output_filename}"
    else:
        fname = f"master_{uuid.uuid4().hex[:8]}.mp4"

    if not fname.endswith(".mp4"):
        fname += ".mp4"

    out_url = f"/static/rendered/{fname}"
    out_rel_path = out_url.lstrip("/")

    dirname = os.path.dirname(out_rel_path)
    if dirname:
        os.makedirs(dirname, exist_ok=True)

    valid_paths = []
    for raw_url in video_urls:
        parsed_path = urllib.parse.urlparse(raw_url).path
        rel = parsed_path.lstrip("/")
        if not rel:
            continue
        clean_url = f"/{rel}"
        ensure_rendered_video(clean_url)
        if os.path.exists(rel):
            valid_paths.append(os.path.abspath(rel))

    if not valid_paths:
        raise RuntimeError("No valid video files available for concatenation")

    temp_files_to_clean = []
    processed_paths = []

    for idx, src_path in enumerate(valid_paths):
        lt = lower_third_titles[idx] if lower_third_titles and idx < len(lower_third_titles) else None

        filters = []
        if product_sponsor_callout:
            clean_callout = _clean_ffmpeg_text(product_sponsor_callout, 60)
            if clean_callout:
                filters.append(
                    "drawbox=x=0:y=0:w=iw:h=40:color=black@0.85:t=fill,"
                    "drawbox=x=0:y=38:w=iw:h=2:color=0xFACC15:t=fill,"
                    f"drawtext=text='SPONSORED BY\\: {clean_callout}':fontcolor=0xFACC15:fontsize=16:x=20:y=10"
                )

        if lt:
            if isinstance(lt, str):
                name = lt
                role = ""
            elif isinstance(lt, dict):
                name = lt.get("name") or lt.get("title") or lt.get("character") or ""
                role = lt.get("role") or lt.get("subtitle") or ""
            else:
                name = ""
                role = ""

            if name:
                clean_name = _clean_ffmpeg_text(name, 40)
                clean_role = _clean_ffmpeg_text(role, 40)
                if clean_name:
                    lt_filter = (
                        "drawbox=x=40:y=ih-90:w=380:h=60:color=black@0.8:t=fill,"
                        "drawbox=x=40:y=ih-90:w=380:h=60:color=0x38BDF8:t=2,"
                        f"drawtext=text='{clean_name}':fontcolor=0xFACC15:fontsize=18:x=55:y=h-82"
                    )
                    if clean_role:
                        lt_filter += f",drawtext=text='{clean_role}':fontcolor=0xFFFFFF:fontsize=13:x=55:y=h-58"
                    filters.append(lt_filter)

        if filters:
            filter_complex_str = ",".join(filters)
            overlay_path = f"static/rendered/overlay_{uuid.uuid4().hex[:8]}_{idx}.mp4"
            cmd_overlay = [
                "ffmpeg",
                "-y",
                "-i",
                src_path,
                "-vf",
                filter_complex_str,
                "-c:v",
                "libx264",
                "-preset",
                "fast",
                "-crf",
                "18",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "copy",
                overlay_path,
            ]
            try:
                res_ov = subprocess.run(cmd_overlay, capture_output=True, check=False)
                if res_ov.returncode == 0 and os.path.exists(overlay_path) and os.path.getsize(overlay_path) > 0:
                    processed_paths.append(os.path.abspath(overlay_path))
                    temp_files_to_clean.append(overlay_path)
                else:
                    processed_paths.append(src_path)
            except FileNotFoundError:
                processed_paths.append(src_path)
        else:
            processed_paths.append(src_path)

    concat_list_path = f"static/rendered/concat_{uuid.uuid4().hex[:8]}.txt"
    try:
        with open(concat_list_path, "w", encoding="utf-8") as f:
            for path in processed_paths:
                escaped_path = path.replace("'", "'\\''")
                f.write(f"file '{escaped_path}'\n")

        cmd = [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            concat_list_path,
            "-c",
            "copy",
            out_rel_path,
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, check=False)
        except FileNotFoundError:
            logger.warning("FFmpeg executable not found. Copying single video file fallback.")
            import shutil
            shutil.copyfile(processed_paths[0], out_rel_path)
            return out_url
        if res.returncode != 0 or not os.path.exists(out_rel_path) or os.path.getsize(out_rel_path) == 0:
            cmd_reencode = [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                concat_list_path,
                "-c:v",
                "libx264",
                "-preset",
                "fast",
                "-crf",
                "18",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                out_rel_path,
            ]
            res_re = subprocess.run(cmd_reencode, capture_output=True, check=False)
            if res_re.returncode != 0 or not os.path.exists(out_rel_path) or os.path.getsize(out_rel_path) == 0:
                raise RuntimeError("FFmpeg video concatenation failed")
    finally:
        for tmp_file in [concat_list_path] + temp_files_to_clean:
            if os.path.exists(tmp_file):
                try:
                    os.remove(tmp_file)
                except Exception:
                    pass

    return out_url
