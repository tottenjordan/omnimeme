"""Scriptwriter & Storyboarder Agent for OmniMeme Multi-Scene Video Directing."""

import json
import logging
import os
from typing import Any

from google import genai
from google.genai import types
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from omnimeme.agent import OmniDirectorAgent, create_omni_director_agent
from omnimeme.client import get_platform_client
from omnimeme.tools import generate_video_config
from omnimeme.vault import CharacterVault

logger = logging.getLogger("omnimeme.scriptwriter")


class ScriptwriterAgent:
    """Agent using gemini-2.5-flash to transform high-level creative concepts into structured multi-scene storyboards."""

    def __init__(
        self,
        name: str = "scriptwriter_agent",
        model: str = "gemini-2.5-flash",
        director_agent: Any | None = None,
        remote_director_card_url: str | None = None,
        project_id: str | None = None,
        location: str | None = "us-central1",
    ):
        self.name = name
        self.model = model
        self.client = get_platform_client(project_id, location)

        if remote_director_card_url:
            self.director_agent = RemoteA2aAgent(
                name="remote_omni_director",
                agent_card=remote_director_card_url,
            )
        elif director_agent is not None:
            self.director_agent = director_agent
        else:
            self.director_agent = create_omni_director_agent()

    def generate_storyboard(
        self,
        concept: str,
        scene_count: int = 3,
        style_preference: str = "",
        character_role_id: str | None = None,
        character_vault: CharacterVault | None = None,
    ) -> dict[str, Any]:
        """Generates a structured multi-scene storyboard from a creative concept.

        Each scene includes scene_number, title, visual_description, camera_instruction,
        audio_cue, character_role_id, and video_config (generated via OmniDirectorAgent or A2A delegation).
        """
        if not concept or not concept.strip():
            raise ValueError("Concept cannot be empty.")

        count = max(1, min(scene_count, 10))
        char_role = None
        if character_role_id and character_vault:
            char_role = character_vault.get_character(character_role_id)

        scene_definitions = self._generate_scene_breakdown_with_gemini(
            concept=concept.strip(),
            scene_count=count,
            style_preference=style_preference.strip(),
        )

        scenes = []
        for i, scene_info in enumerate(scene_definitions, start=1):
            visual_desc = scene_info.get("visual_description", "")
            camera_inst = scene_info.get("camera_instruction", "")
            title = scene_info.get("title", f"Scene {i}")
            audio = scene_info.get("audio_cue", "")

            # Generate video_config via director_agent (OmniDirectorAgent or RemoteA2aAgent)
            video_config = self._create_scene_video_config(
                visual_description=visual_desc,
                camera_instruction=camera_inst,
                style_preference=style_preference,
                char_role=char_role,
            )

            scenes.append(
                {
                    "scene_number": i,
                    "title": title,
                    "visual_description": visual_desc,
                    "camera_instruction": camera_inst,
                    "audio_cue": audio,
                    "character_role_id": character_role_id,
                    "video_config": video_config,
                }
            )

        return {
            "concept": concept.strip(),
            "scene_count": count,
            "style_preference": style_preference.strip(),
            "character_role_id": character_role_id,
            "scenes": scenes,
        }

    def _generate_scene_breakdown_with_gemini(
        self, concept: str, scene_count: int, style_preference: str
    ) -> list[dict[str, str]]:
        """Uses gemini-2.5-flash to break down a creative concept into structured scene objects."""
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if api_key:
            try:
                genai_client = genai.Client(api_key=api_key)
                prompt = (
                    f"You are an expert Hollywood scriptwriter and video storyboard director.\n"
                    f"Transform the following high-level creative concept into a structured multi-scene storyboard breakdown of exactly {scene_count} scenes.\n"
                    f"Style Preference: {style_preference if style_preference else 'Cinematic 4K'}\n\n"
                    f"Concept:\n\"{concept}\"\n\n"
                    f"Return ONLY a raw JSON array containing exactly {scene_count} objects with keys: "
                    f"\"scene_number\", \"title\", \"visual_description\", \"camera_instruction\", \"audio_cue\"."
                )
                response = genai_client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                    ),
                )
                if response and response.text:
                    parsed = json.loads(response.text.strip())
                    if isinstance(parsed, list) and len(parsed) == scene_count:
                        return parsed
            except Exception as e:
                logger.warning(f"Gemini API call ({self.model}) failed or unavailable: {e}. Falling back to dynamic generator.")

        return [
            self._generate_fallback_scene_definition(
                concept=concept,
                scene_number=i,
                total_scenes=scene_count,
                style_preference=style_preference,
            )
            for i in range(1, scene_count + 1)
        ]

    def _generate_fallback_scene_definition(
        self, concept: str, scene_number: int, total_scenes: int, style_preference: str
    ) -> dict[str, str]:
        """Creates dynamic scene breakdown titles, visual descriptions, camera instructions, and audio cues."""
        short_concept = concept[:35] + ("..." if len(concept) > 35 else "")
        style_suffix = f" Style: {style_preference}." if style_preference else ""

        if scene_number == 1:
            title = f"Scene 1: Opening - {short_concept}"
            visual = f"Establishing shot introducing {concept}.{style_suffix} Atmosphere setting and initial character entrance."
            camera = "Wide opening tracking shot, 35mm cinematic lens at eye level."
            audio = "Ambient background atmosphere hum with gentle melodic crescendo."
        elif scene_number == total_scenes and total_scenes > 1:
            title = f"Scene {scene_number}: Climax - {short_concept}"
            visual = f"Climactic peak sequence of {concept}.{style_suffix} Dynamic high-stakes kinetic motion."
            camera = "Dynamic low-angle orbital tracking shot with fast-paced motion."
            audio = "Dramatic orchestral score climax fading into echoing ambient reverb."
        else:
            title = f"Scene {scene_number}: Narrative Progression - {short_concept}"
            visual = f"Mid-sequence narrative development focusing on {concept}.{style_suffix} Fluid character interaction."
            camera = "Medium tracking pan with steadycam push-in framing."
            audio = "Tense bassline drone with synchronized thematic sound effects."

        return {
            "scene_number": str(scene_number),
            "title": title,
            "visual_description": visual,
            "camera_instruction": camera,
            "audio_cue": audio,
        }

    def _create_scene_video_config(
        self,
        visual_description: str,
        camera_instruction: str,
        style_preference: str,
        char_role: Any | None,
    ) -> dict[str, Any]:
        """Generates video_config by delegating to director_agent or generating directly."""
        notes = f"{style_preference}. Camera: {camera_instruction}".strip()

        if self.director_agent is not None:
            if hasattr(self.director_agent, "run") and callable(getattr(self.director_agent, "run")):
                try:
                    res = self.director_agent.run(
                        user_prompt=visual_description,
                        director_notes=notes,
                        character_role=char_role,
                        theme=style_preference or "cinematic",
                    )
                    if isinstance(res, dict) and "video_config" in res:
                        return res["video_config"]
                    elif isinstance(res, dict):
                        return res
                except Exception as e:
                    logger.warning(f"Delegation to director_agent failed: {e}. Using direct generator.")

        # Fallback or direct video_config generation helper
        ref_assets = None
        if char_role and getattr(char_role, "turnaround_sheet_url", None):
            ref_assets = [
                {
                    "uri": char_role.turnaround_sheet_url,
                    "mime_type": "image/png",
                    "description": f"{char_role.name} Turnaround Sheet (@Image1)",
                }
            ]

        enhanced_prompt = f"[Subject]: {visual_description}\n[Camera]: {camera_instruction}\n[Style]: {style_preference or 'Cinematic 4K'}"
        return generate_video_config(
            enhanced_prompt=enhanced_prompt,
            duration_sec=5,
            aspect_ratio="16:9",
            reference_assets=ref_assets,
        )


def create_scriptwriter_agent(
    director_agent: Any | None = None,
    remote_director_card_url: str | None = None,
) -> ScriptwriterAgent:
    """Factory to instantiate the Scriptwriter & Storyboarder Agent."""
    return ScriptwriterAgent(
        director_agent=director_agent,
        remote_director_card_url=remote_director_card_url,
    )

