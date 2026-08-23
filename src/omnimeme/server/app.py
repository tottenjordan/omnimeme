import os
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from omnimeme.agent import create_omni_director_agent
from omnimeme.engine import OmniFlashExecutionEngine
from omnimeme.turnaround import generate_turnaround_sheet_config
from omnimeme.ui.freeform_widget import FreeformInput, process_freeform_request
from omnimeme.ui.guided_experience import GuidedPromptInput, MediaAttachment, process_guided_request
from omnimeme.vault import CharacterRole, CharacterVault

app = FastAPI(title="OmniMeme Video Directing Agent API", version="0.1.0")

os.makedirs("static/rendered", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

global_vault = CharacterVault()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "Content-Type": "text/event-stream",
    "X-Accel-Buffering": "no",
}


class MediaAttachmentModel(BaseModel):
    uri: str
    mime_type: str
    description: str = ""


class CharacterRoleModel(BaseModel):
    role_id: str
    name: str
    description: str
    turnaround_sheet_url: str | None = None
    aesthetic_tags: list[str] = []
    voice_style: str = ""
    wardrobe: str = ""
    image_role: str = "Character Reference"


class TurnaroundApiRequest(BaseModel):
    reference_image_url: str | None = None
    style_preference: str = ""


class GuidedApiRequest(BaseModel):
    subject: str
    action: str = ""
    camera: str = ""
    lighting: str = ""
    style: str = ""
    audio: str = ""
    duration_sec: int = 5
    aspect_ratio: str = "16:9"
    reference_images: list[MediaAttachmentModel] = []
    reference_videos: list[MediaAttachmentModel] = []
    character_role_id: str | None = None


class FreeformApiRequest(BaseModel):
    raw_prompt: str
    director_style_preference: str = ""
    reference_images: list[MediaAttachmentModel] = []
    reference_videos: list[MediaAttachmentModel] = []
    character_role_id: str | None = None


def _parse_media_attachments(models: list[MediaAttachmentModel]) -> list[MediaAttachment]:
    return [
        MediaAttachment(uri=m.uri, mime_type=m.mime_type, description=m.description) for m in models
    ]


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "OmniMeme Agent API"}


@app.get("/api/vault/characters")
def list_vault_characters():
    return [c.to_dict() for c in global_vault.list_characters()]


@app.post("/api/vault/characters")
def add_vault_character(req: CharacterRoleModel):
    char = CharacterRole(
        role_id=req.role_id,
        name=req.name,
        description=req.description,
        turnaround_sheet_url=req.turnaround_sheet_url,
        aesthetic_tags=req.aesthetic_tags,
        voice_style=req.voice_style,
        wardrobe=req.wardrobe,
        image_role=req.image_role,
    )
    global_vault.add_character(char)
    return char.to_dict()


@app.delete("/api/vault/characters/{role_id}")
def delete_vault_character(role_id: str):
    success = global_vault.delete_character(role_id)
    if not success:
        raise HTTPException(status_code=404, detail="Character not found")
    return {"status": "success", "deleted_role_id": role_id}


@app.get("/api/gcs/proxy")
def proxy_gcs_image(uri: str):
    """Proxies gs:// or http:// image URIs into visual SVG/PNG thumbnails for UI hot-loading."""
    if not uri:
        raise HTTPException(status_code=400, detail="URI is required")

    if uri.startswith("http://") or uri.startswith("https://"):
        return RedirectResponse(url=uri)

    clean_name = uri.split("/")[-1]
    svg_thumbnail = f"""<svg xmlns="http://www.w3.org/2000/svg" width="300" height="200" viewBox="0 0 300 200">
      <rect width="300" height="200" fill="#1e293b"/>
      <rect x="10" y="10" width="280" height="180" rx="8" fill="#0f172a" stroke="#3b82f6" stroke-width="2"/>
      <circle cx="150" cy="80" r="30" fill="#3b82f6" opacity="0.8"/>
      <path d="M120 140 Q150 110 180 140" stroke="#60a5fa" stroke-width="4" fill="none"/>
      <text x="150" y="170" fill="#94a3b8" font-family="sans-serif" font-size="12" text-anchor="middle">{clean_name}</text>
    </svg>"""
    return Response(content=svg_thumbnail, media_type="image/svg+xml")


@app.post("/api/vault/characters/{role_id}/turnaround")
def generate_character_turnaround(role_id: str, req: TurnaroundApiRequest | None = None):
    char = global_vault.get_character(role_id)
    if not char:
        raise HTTPException(status_code=404, detail="Character not found in vault")

    ref_url = req.reference_image_url if req else None
    style_pref = req.style_preference if req else ""

    config = generate_turnaround_sheet_config(
        char, style_preference=style_pref, reference_image_url=ref_url
    )
    sheet_url = (
        ref_url
        or char.turnaround_sheet_url
        or f"gs://omnimeme-assets/turnarounds/{char.role_id}_sheet.png"
    )
    char.turnaround_sheet_url = sheet_url

    return {
        "status": "success",
        "character": char.to_dict(),
        "turnaround_config": config,
        "generated_sheet_url": sheet_url,
    }


@app.post("/api/guided/enhance")
def enhance_guided(req: GuidedApiRequest):
    agent = create_omni_director_agent()
    inp = GuidedPromptInput(
        subject=req.subject,
        action=req.action,
        camera=req.camera,
        lighting=req.lighting,
        style=req.style,
        audio=req.audio,
        duration_sec=req.duration_sec,
        aspect_ratio=req.aspect_ratio,
        reference_images=_parse_media_attachments(req.reference_images),
        reference_videos=_parse_media_attachments(req.reference_videos),
    )
    char_role = global_vault.get_character(req.character_role_id) if req.character_role_id else None
    res = process_guided_request(inp, agent, character_role=char_role)
    if res["status"] == "error":
        raise HTTPException(status_code=400, detail=res["error_message"])
    return res


@app.post("/api/freeform/enhance")
def enhance_freeform(req: FreeformApiRequest):
    agent = create_omni_director_agent()
    inp = FreeformInput(
        raw_prompt=req.raw_prompt,
        director_style_preference=req.director_style_preference,
        reference_images=_parse_media_attachments(req.reference_images),
        reference_videos=_parse_media_attachments(req.reference_videos),
    )
    char_role = global_vault.get_character(req.character_role_id) if req.character_role_id else None
    res = process_freeform_request(inp, agent, character_role=char_role)
    if res["status"] == "error":
        raise HTTPException(status_code=400, detail=res["error_message"])
    return res


@app.post("/api/guided/stream")
def stream_guided(req: GuidedApiRequest):
    if not req.subject or not req.subject.strip():
        raise HTTPException(status_code=400, detail="Subject cannot be empty.")

    agent = create_omni_director_agent()
    inp = GuidedPromptInput(
        subject=req.subject,
        action=req.action,
        camera=req.camera,
        lighting=req.lighting,
        style=req.style,
        audio=req.audio,
        duration_sec=req.duration_sec,
        aspect_ratio=req.aspect_ratio,
        reference_images=_parse_media_attachments(req.reference_images),
        reference_videos=_parse_media_attachments(req.reference_videos),
    )
    raw_directive = inp.to_raw_directive()
    reference_assets = inp.get_all_reference_assets()
    char_role = global_vault.get_character(req.character_role_id) if req.character_role_id else None

    generator = agent.stream_run(
        user_prompt=raw_directive,
        director_notes=f"Aspect: {req.aspect_ratio}, Duration: {req.duration_sec}s",
        duration_sec=req.duration_sec,
        aspect_ratio=req.aspect_ratio,
        reference_assets=reference_assets,
        character_role=char_role,
    )
    return StreamingResponse(generator, media_type="text/event-stream", headers=SSE_HEADERS)


@app.post("/api/freeform/stream")
def stream_freeform(req: FreeformApiRequest):
    if not req.raw_prompt or not req.raw_prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")

    agent = create_omni_director_agent()
    inp = FreeformInput(
        raw_prompt=req.raw_prompt,
        director_style_preference=req.director_style_preference,
        reference_images=_parse_media_attachments(req.reference_images),
        reference_videos=_parse_media_attachments(req.reference_videos),
    )
    reference_assets = inp.get_all_reference_assets()
    char_role = global_vault.get_character(req.character_role_id) if req.character_role_id else None

    generator = agent.stream_run(
        user_prompt=req.raw_prompt,
        director_notes=req.director_style_preference,
        reference_assets=reference_assets,
        character_role=char_role,
    )
    return StreamingResponse(generator, media_type="text/event-stream", headers=SSE_HEADERS)


class VideoExecutionRequest(BaseModel):
    video_config: dict[str, Any]
    session_name: str = ""
    previous_interaction_id: str | None = None
    mock_mode: bool | None = None


@app.post("/api/generate-video")
def generate_video(req: VideoExecutionRequest):
    is_mock = req.mock_mode if req.mock_mode is not None else False
    engine = OmniFlashExecutionEngine(mock_mode=is_mock)
    result = engine.generate_video(
        req.video_config,
        previous_interaction_id=req.previous_interaction_id,
    )
    return result.to_dict()


@app.post("/api/generate-video/stream")
def stream_generate_video(req: VideoExecutionRequest):
    is_mock = req.mock_mode if req.mock_mode is not None else False
    engine = OmniFlashExecutionEngine(mock_mode=is_mock)
    generator = engine.stream_generate_video(
        req.video_config,
        previous_interaction_id=req.previous_interaction_id,
    )
    return StreamingResponse(generator, media_type="text/event-stream", headers=SSE_HEADERS)

