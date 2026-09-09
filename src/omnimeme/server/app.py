from contextlib import asynccontextmanager
import json
import logging
import os
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.agents.llm_agent import Agent
from pydantic import BaseModel

from omnimeme.agent import create_omni_director_agent
from omnimeme.engine import OmniFlashExecutionEngine, concatenate_storyboard_videos
from omnimeme.prompts import OMNI_FLASH_DIRECTING_INSTR
from omnimeme.scriptwriter import create_scriptwriter_agent
from omnimeme.tools import enhance_video_prompt, generate_video_config
from omnimeme.turnaround import generate_turnaround_sheet_config
from omnimeme.ui.freeform_widget import FreeformInput, process_freeform_request
from omnimeme.ui.guided_experience import GuidedPromptInput, MediaAttachment, process_guided_request
from omnimeme.vault import CHARACTER_ARCHETYPE_PRESETS, CharacterRole, CharacterVault


logger = logging.getLogger("omnimeme.server")

omni_director_adk_agent = Agent(
    name="omni_director",
    model="gemini-omni-1.1-flash",
    instruction=OMNI_FLASH_DIRECTING_INSTR,
    tools=[enhance_video_prompt, generate_video_config],
)

a2a_director_app = to_a2a(omni_director_adk_agent)


@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    async with a2a_director_app.router.lifespan_context(a2a_director_app):
        yield


app = FastAPI(title="OmniMeme Video Directing Agent API", version="0.1.0", lifespan=lifespan)
app.mount("/a2a/app", a2a_director_app)

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
    resolution: str = "720p"
    first_frame_uri: str | None = None
    last_frame_uri: str | None = None


class ProductInfoModel(BaseModel):
    name: str
    description: str = ""
    image_url: str | None = None
    tagline: str = ""


class GuidedApiRequest(BaseModel):
    subject: str
    action: str = ""
    camera: str = ""
    lighting: str = ""
    style: str = ""
    audio: str = ""
    dialogue_text: str = ""
    sound_effects: str = ""
    music_score: str = ""
    mute_dialogue: bool = False
    no_music: bool = False
    duration_sec: int = 5
    aspect_ratio: str = "16:9"
    resolution: str = "720p"
    first_frame_uri: str | None = None
    last_frame_uri: str | None = None
    reference_images: list[MediaAttachmentModel] = []
    reference_videos: list[MediaAttachmentModel] = []
    character_role_id: str | None = None
    character_b_role_id: str | None = None
    product: ProductInfoModel | None = None
    motion_preset: str | None = None


class FreeformApiRequest(BaseModel):
    raw_prompt: str
    director_style_preference: str = ""
    resolution: str = "720p"
    first_frame_uri: str | None = None
    last_frame_uri: str | None = None
    reference_images: list[MediaAttachmentModel] = []
    reference_videos: list[MediaAttachmentModel] = []
    character_role_id: str | None = None
    character_b_role_id: str | None = None
    product: ProductInfoModel | None = None
    motion_preset: str | None = None


class ScriptwritingRequest(BaseModel):
    concept: str
    scene_count: int = 3
    style_preference: str = ""
    character_role_id: str | None = None


class MashupRequest(BaseModel):
    character_a_id: str
    character_b_id: str
    mashup_genre: str = "Parody Crossover"
    parody_tone: str = "Absurdist Satire"
    product: ProductInfoModel | None = None
    scene_count: int = 4


class ConcatenateRequest(BaseModel):
    video_urls: list[str]
    output_filename: str | None = None
    lower_third_titles: list[dict[str, str]] | None = None
    product_sponsor_callout: str | None = None


class ChainedRenderRequest(BaseModel):
    scenes: list[dict[str, Any]]
    resolution: str = "720p"
    mock_mode: bool | None = None



def _parse_media_attachments(models: list[MediaAttachmentModel]) -> list[MediaAttachment]:
    return [
        MediaAttachment(uri=m.uri, mime_type=m.mime_type, description=m.description) for m in models
    ]



@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "OmniMeme Agent API"}


@app.get("/api/vault/archetypes")
def get_vault_archetypes():
    return CHARACTER_ARCHETYPE_PRESETS



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
    ref_images = _parse_media_attachments(req.reference_images)
    if req.character_b_role_id:
        char_b = global_vault.get_character(req.character_b_role_id)
        if char_b and char_b.turnaround_sheet_url:
            ref_images.append(MediaAttachment(uri=char_b.turnaround_sheet_url, mime_type="image/png", description=f"{char_b.name} Turnaround Sheet (@Image2)"))
    if req.product and req.product.image_url:
        ref_images.append(MediaAttachment(uri=req.product.image_url, mime_type="image/png", description=f"Product Reference: {req.product.name}"))

    inp = GuidedPromptInput(
        subject=req.subject,
        action=req.action,
        camera=req.camera,
        lighting=req.lighting,
        style=req.style,
        audio=req.audio,
        dialogue_text=req.dialogue_text,
        sound_effects=req.sound_effects,
        music_score=req.music_score,
        mute_dialogue=req.mute_dialogue,
        no_music=req.no_music,
        duration_sec=req.duration_sec,
        aspect_ratio=req.aspect_ratio,
        resolution=req.resolution,
        first_frame_uri=req.first_frame_uri,
        last_frame_uri=req.last_frame_uri,
        reference_images=ref_images,
        reference_videos=_parse_media_attachments(req.reference_videos),
        motion_preset=req.motion_preset,
    )
    char_role = global_vault.get_character(req.character_role_id) if req.character_role_id else None
    res = process_guided_request(inp, agent, character_role=char_role)
    if res["status"] == "error":
        raise HTTPException(status_code=400, detail=res["error_message"])
    return res


@app.post("/api/freeform/enhance")
def enhance_freeform(req: FreeformApiRequest):
    agent = create_omni_director_agent()
    ref_images = _parse_media_attachments(req.reference_images)
    if req.character_b_role_id:
        char_b = global_vault.get_character(req.character_b_role_id)
        if char_b and char_b.turnaround_sheet_url:
            ref_images.append(MediaAttachment(uri=char_b.turnaround_sheet_url, mime_type="image/png", description=f"{char_b.name} Turnaround Sheet (@Image2)"))
    if req.product and req.product.image_url:
        ref_images.append(MediaAttachment(uri=req.product.image_url, mime_type="image/png", description=f"Product Reference: {req.product.name}"))

    inp = FreeformInput(
        raw_prompt=req.raw_prompt,
        director_style_preference=req.director_style_preference,
        resolution=req.resolution,
        first_frame_uri=req.first_frame_uri,
        last_frame_uri=req.last_frame_uri,
        reference_images=ref_images,
        reference_videos=_parse_media_attachments(req.reference_videos),
        motion_preset=req.motion_preset,
    )
    char_role = global_vault.get_character(req.character_role_id) if req.character_role_id else None
    res = process_freeform_request(inp, agent, character_role=char_role)
    if res["status"] == "error":
        raise HTTPException(status_code=400, detail=res["error_message"])
    return res


@app.get("/api/vault/mashup-bundles")
def get_vault_mashup_bundles():
    from omnimeme.vault import MASHUP_PRESET_BUNDLES
    return MASHUP_PRESET_BUNDLES


@app.post("/api/scriptwriting/generate")
def generate_scriptwriting(req: ScriptwritingRequest):
    if not req.concept or not req.concept.strip():
        raise HTTPException(status_code=400, detail="Concept cannot be empty.")

    scriptwriter = create_scriptwriter_agent()
    result = scriptwriter.generate_storyboard(
        concept=req.concept,
        scene_count=req.scene_count,
        style_preference=req.style_preference,
        character_role_id=req.character_role_id,
        character_vault=global_vault,
    )
    return {"status": "success", "storyboard": result}


@app.post("/api/scriptwriting/mashup")
def generate_mashup_scriptwriting(req: MashupRequest):
    if not req.character_a_id or not req.character_b_id or not req.character_a_id.strip() or not req.character_b_id.strip():
        raise HTTPException(status_code=400, detail="character_a_id and character_b_id are required.")

    scriptwriter = create_scriptwriter_agent()
    p_name = req.product.name if req.product else None
    p_desc = req.product.description if req.product else None
    p_img = req.product.image_url if req.product else None
    p_tag = req.product.tagline if req.product else None

    result = scriptwriter.generate_mashup_storyboard(
        character_a_id=req.character_a_id,
        character_b_id=req.character_b_id,
        mashup_genre=req.mashup_genre,
        parody_tone=req.parody_tone,
        product_name=p_name,
        product_description=p_desc,
        product_image_url=p_img,
        product_tagline=p_tag,
        scene_count=req.scene_count,
        character_vault=global_vault,
    )
    return {"status": "success", "storyboard": result}


@app.post("/api/scriptwriting/concatenate")
def concatenate_scriptwriting(req: ConcatenateRequest):
    if not req.video_urls:
        raise HTTPException(status_code=400, detail="video_urls list cannot be empty.")
    try:
        master_url = concatenate_storyboard_videos(
            req.video_urls,
            output_filename=req.output_filename,
            lower_third_titles=req.lower_third_titles,
            product_sponsor_callout=req.product_sponsor_callout,
        )
        return {"status": "success", "master_video_url": master_url}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/scriptwriting/render-chained")
def render_chained_storyboard_endpoint(req: ChainedRenderRequest):
    if not req.scenes:
        raise HTTPException(status_code=400, detail="scenes list cannot be empty.")
    try:
        is_mock = req.mock_mode if req.mock_mode is not None else False
        engine = OmniFlashExecutionEngine(mock_mode=is_mock)
        rendered_scenes = engine.render_chained_storyboard(
            scenes=req.scenes,
            resolution=req.resolution,
            mock_mode=req.mock_mode,
        )
        return {
            "status": "success",
            "scenes": rendered_scenes,
            "total_scenes": len(rendered_scenes),
            "cumulative_duration_seconds": sum(s.get("duration_seconds", 5) for s in rendered_scenes),
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Chained rendering failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


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
        dialogue_text=req.dialogue_text,
        sound_effects=req.sound_effects,
        music_score=req.music_score,
        mute_dialogue=req.mute_dialogue,
        no_music=req.no_music,
        duration_sec=req.duration_sec,
        aspect_ratio=req.aspect_ratio,
        resolution=req.resolution,
        first_frame_uri=req.first_frame_uri,
        last_frame_uri=req.last_frame_uri,
        reference_images=_parse_media_attachments(req.reference_images),
        reference_videos=_parse_media_attachments(req.reference_videos),
        motion_preset=req.motion_preset,
    )
    raw_directive = inp.to_raw_directive()
    reference_assets = inp.get_all_reference_assets()
    char_role = global_vault.get_character(req.character_role_id) if req.character_role_id else None

    generator = agent.stream_run(
        user_prompt=raw_directive,
        director_notes=f"Aspect: {req.aspect_ratio}, Duration: {req.duration_sec}s",
        duration_sec=req.duration_sec,
        aspect_ratio=req.aspect_ratio,
        resolution=req.resolution,
        first_frame_uri=req.first_frame_uri,
        last_frame_uri=req.last_frame_uri,
        reference_assets=reference_assets,
        character_role=char_role,
        motion_preset=req.motion_preset,
        dialogue_text=req.dialogue_text,
        sound_effects=req.sound_effects,
        music_score=req.music_score,
        mute_dialogue=req.mute_dialogue,
        no_music=req.no_music,
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
        resolution=req.resolution,
        first_frame_uri=req.first_frame_uri,
        last_frame_uri=req.last_frame_uri,
        reference_images=_parse_media_attachments(req.reference_images),
        reference_videos=_parse_media_attachments(req.reference_videos),
        motion_preset=req.motion_preset,
    )
    reference_assets = inp.get_all_reference_assets()
    char_role = global_vault.get_character(req.character_role_id) if req.character_role_id else None

    generator = agent.stream_run(
        user_prompt=req.raw_prompt,
        director_notes=req.director_style_preference,
        resolution=req.resolution,
        first_frame_uri=req.first_frame_uri,
        last_frame_uri=req.last_frame_uri,
        reference_assets=reference_assets,
        character_role=char_role,
        motion_preset=req.motion_preset,
    )
    return StreamingResponse(generator, media_type="text/event-stream", headers=SSE_HEADERS)


class VideoExecutionRequest(BaseModel):
    video_config: dict[str, Any]
    session_name: str = ""
    previous_interaction_id: str | None = None
    mock_mode: bool | None = None
    resolution: str = "720p"
    first_frame_uri: str | None = None
    last_frame_uri: str | None = None


@app.post("/api/generate-video")
def generate_video(req: VideoExecutionRequest):
    is_mock = req.mock_mode if req.mock_mode is not None else False
    engine = OmniFlashExecutionEngine(mock_mode=is_mock)
    result = engine.generate_video(
        req.video_config,
        previous_interaction_id=req.previous_interaction_id,
        resolution=req.resolution,
        first_frame_uri=req.first_frame_uri,
        last_frame_uri=req.last_frame_uri,
    )
    return result.to_dict()


@app.post("/api/generate-video/stream")
def stream_generate_video(req: VideoExecutionRequest):
    is_mock = req.mock_mode if req.mock_mode is not None else False
    engine = OmniFlashExecutionEngine(mock_mode=is_mock)
    generator = engine.stream_generate_video(
        req.video_config,
        previous_interaction_id=req.previous_interaction_id,
        resolution=req.resolution,
        first_frame_uri=req.first_frame_uri,
        last_frame_uri=req.last_frame_uri,
    )
    return StreamingResponse(generator, media_type="text/event-stream", headers=SSE_HEADERS)


class UserFeedbackRequest(BaseModel):
    interaction_thread_id: str
    rating: int  # 1 to 5 stars
    feedback_type: str = "general"
    comment: str | None = None
    prompt: str | None = None


@app.post("/api/feedback")
def submit_feedback(req: UserFeedbackRequest):
    if req.rating < 1 or req.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5.")

    logger.info(
        f"User Feedback received: thread={req.interaction_thread_id} rating={req.rating}/5 "
        f"type={req.feedback_type} comment={json.dumps(req.comment or '')} prompt={json.dumps(req.prompt or '')}"
    )
    return {"status": "success", "message": "Feedback recorded successfully."}
