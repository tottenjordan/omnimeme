"""FastAPI Backend Server for OmniMeme Video Directing Agent."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from omnimeme.agent import create_omni_director_agent
from omnimeme.ui.freeform_widget import FreeformInput, process_freeform_request
from omnimeme.ui.guided_experience import GuidedPromptInput, process_guided_request

app = FastAPI(title="OmniMeme Video Directing Agent API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GuidedApiRequest(BaseModel):
    subject: str
    action: str = ""
    camera: str = ""
    lighting: str = ""
    style: str = ""
    audio: str = ""
    duration_sec: int = 5
    aspect_ratio: str = "16:9"


class FreeformApiRequest(BaseModel):
    raw_prompt: str
    director_style_preference: str = ""


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
    )
    raw_directive = inp.to_raw_directive()
    from fastapi.responses import StreamingResponse

    generator = agent.stream_run(
        user_prompt=raw_directive,
        director_notes=f"Aspect: {req.aspect_ratio}, Duration: {req.duration_sec}s",
        duration_sec=req.duration_sec,
        aspect_ratio=req.aspect_ratio,
    )
    return StreamingResponse(generator, media_type="text/event-stream")


@app.post("/api/freeform/stream")
def stream_freeform(req: FreeformApiRequest):
    if not req.raw_prompt or not req.raw_prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")

    agent = create_omni_director_agent()
    from fastapi.responses import StreamingResponse

    generator = agent.stream_run(
        user_prompt=req.raw_prompt,
        director_notes=req.director_style_preference,
    )
    return StreamingResponse(generator, media_type="text/event-stream")
