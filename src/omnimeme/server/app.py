"""FastAPI Backend Server for OmniMeme Video Directing Agent."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from omnimeme.agent import create_omni_director_agent
from omnimeme.ui.freeform_widget import FreeformInput, process_freeform_request
from omnimeme.ui.guided_experience import GuidedPromptInput, MediaAttachment, process_guided_request

app = FastAPI(title="OmniMeme Video Directing Agent API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MediaAttachmentModel(BaseModel):
    uri: str
    mime_type: str
    description: str = ""


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


class FreeformApiRequest(BaseModel):
    raw_prompt: str
    director_style_preference: str = ""
    reference_images: list[MediaAttachmentModel] = []
    reference_videos: list[MediaAttachmentModel] = []


def _parse_media_attachments(models: list[MediaAttachmentModel]) -> list[MediaAttachment]:
    return [
        MediaAttachment(uri=m.uri, mime_type=m.mime_type, description=m.description) for m in models
    ]


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "OmniMeme Agent API"}


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
    res = process_guided_request(inp, agent)
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
    res = process_freeform_request(inp, agent)
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
    from fastapi.responses import StreamingResponse

    generator = agent.stream_run(
        user_prompt=raw_directive,
        director_notes=f"Aspect: {req.aspect_ratio}, Duration: {req.duration_sec}s",
        duration_sec=req.duration_sec,
        aspect_ratio=req.aspect_ratio,
        reference_assets=reference_assets,
    )
    return StreamingResponse(generator, media_type="text/event-stream")


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
    from fastapi.responses import StreamingResponse

    generator = agent.stream_run(
        user_prompt=req.raw_prompt,
        director_notes=req.director_style_preference,
        reference_assets=reference_assets,
    )
    return StreamingResponse(generator, media_type="text/event-stream")
