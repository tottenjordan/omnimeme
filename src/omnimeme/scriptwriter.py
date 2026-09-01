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

    def generate_mashup_storyboard(
        self,
        character_a_id: str,
        character_b_id: str,
        mashup_genre: str = "Parody Crossover",
        parody_tone: str = "Absurdist Satire",
        product_name: str | None = None,
        product_description: str | None = None,
        product_image_url: str | None = None,
        product_tagline: str | None = None,
        scene_count: int = 4,
        character_vault: CharacterVault | None = None,
    ) -> dict[str, Any]:
        """Generates a structured 4-scene parody mashup storyboard alternating character beats and commercial callouts."""
        if not character_a_id or not character_b_id or not character_a_id.strip() or not character_b_id.strip():
            raise ValueError("character_a_id and character_b_id are required.")

        character_a_id = character_a_id.strip()
        character_b_id = character_b_id.strip()

        count = max(1, min(scene_count, 10))

        char_a = character_vault.get_character(character_a_id) if character_vault else None
        char_b = character_vault.get_character(character_b_id) if character_vault else None

        if not char_a or not char_b:
            from omnimeme.vault import MASHUP_PRESET_BUNDLES, CHARACTER_ARCHETYPE_PRESETS, CharacterRole
            for bundle in MASHUP_PRESET_BUNDLES:
                ca = bundle.get("character_a", {})
                cb = bundle.get("character_b", {})
                if not char_a and ca.get("role_id") == character_a_id:
                    char_a = CharacterRole(**ca)
                if not char_a and cb.get("role_id") == character_a_id:
                    char_a = CharacterRole(**cb)
                if not char_b and ca.get("role_id") == character_b_id:
                    char_b = CharacterRole(**ca)
                if not char_b and cb.get("role_id") == character_b_id:
                    char_b = CharacterRole(**cb)

            for arch in CHARACTER_ARCHETYPE_PRESETS:
                if not char_a and arch.get("role_id") == character_a_id:
                    char_a = CharacterRole(**arch)
                if not char_b and arch.get("role_id") == character_b_id:
                    char_b = CharacterRole(**arch)

        if not char_a:
            from omnimeme.vault import CharacterRole
            char_a = CharacterRole(
                role_id=character_a_id,
                name=character_a_id.replace("_", " ").title(),
                description=f"Parody protagonist {character_a_id}",
            )
        if not char_b:
            from omnimeme.vault import CharacterRole
            char_b = CharacterRole(
                role_id=character_b_id,
                name=character_b_id.replace("_", " ").title(),
                description=f"Parody antagonist {character_b_id}",
            )

        scene_definitions = self._generate_mashup_scene_breakdown_with_gemini(
            char_a=char_a,
            char_b=char_b,
            mashup_genre=mashup_genre,
            parody_tone=parody_tone,
            product_name=product_name,
            product_description=product_description,
            product_tagline=product_tagline,
            scene_count=count,
        )

        scenes = []
        for i, s_info in enumerate(scene_definitions, start=1):
            char_id = s_info.get("character_role_id", char_a.role_id if i % 2 == 1 else char_b.role_id)
            scene_char = char_a if char_id == char_a.role_id else char_b

            v_desc = s_info.get("visual_description", "")
            c_inst = s_info.get("camera_instruction", "")
            title = s_info.get("title", f"Scene {i}")
            audio = s_info.get("audio_cue", "")

            style_pref = f"{mashup_genre}, {parody_tone} parody style"
            video_config = self._create_scene_video_config(
                visual_description=v_desc,
                camera_instruction=c_inst,
                style_preference=style_pref,
                char_role=scene_char,
            )

            if product_image_url and (i == 3 or "commercial" in title.lower() or "sponsor" in title.lower()):
                ref_assets = video_config.get("reference_assets") or []
                ref_assets.append(
                    {
                        "uri": product_image_url,
                        "mime_type": "image/png",
                        "description": f"Product Reference: {product_name or 'Sponsor Product'}",
                    }
                )
                video_config["reference_assets"] = ref_assets

            lower_third = s_info.get("lower_third_title") or {
                "name": scene_char.name,
                "role": getattr(scene_char, "image_role", None) or mashup_genre,
            }
            if isinstance(lower_third, str):
                lower_third = {"name": lower_third, "role": mashup_genre}

            scenes.append(
                {
                    "scene_number": i,
                    "title": title,
                    "visual_description": v_desc,
                    "camera_instruction": c_inst,
                    "audio_cue": audio,
                    "character_role_id": char_id,
                    "lower_third_title": lower_third,
                    "video_config": video_config,
                }
            )

        product_dict = None
        if product_name:
            product_dict = {
                "name": product_name,
                "description": product_description or "",
                "image_url": product_image_url or "",
                "tagline": product_tagline or "",
            }

        return {
            "concept": f"Mashup: {char_a.name} vs {char_b.name} ({mashup_genre})",
            "mashup_genre": mashup_genre,
            "parody_tone": parody_tone,
            "character_a_id": character_a_id,
            "character_b_id": character_b_id,
            "product": product_dict,
            "scene_count": count,
            "scenes": scenes,
        }

    def _generate_mashup_scene_breakdown_with_gemini(
        self,
        char_a: Any,
        char_b: Any,
        mashup_genre: str,
        parody_tone: str,
        product_name: str | None,
        product_description: str | None,
        product_tagline: str | None,
        scene_count: int,
    ) -> list[dict[str, Any]]:
        """Uses gemini-2.5-flash to break down a parody mashup concept into 4 alternating beats."""
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if api_key:
            try:
                genai_client = genai.Client(api_key=api_key)
                product_info = f"Sponsor Product: {product_name} ({product_tagline})" if product_name else "No product tie-in"
                prompt = (
                    f"You are an expert comedy video director and parody scriptwriter.\n"
                    f"Create a 4-scene alternating character beat video storyboard for a parody mashup.\n"
                    f"Character A: {char_a.name} ({char_a.description})\n"
                    f"Character B: {char_b.name} ({char_b.description})\n"
                    f"Mashup Genre: {mashup_genre}\n"
                    f"Parody Tone: {parody_tone}\n"
                    f"{product_info}\n\n"
                    f"Structure exact {scene_count} scenes alternating character beats and a commercial parody beat.\n"
                    f"Return ONLY a raw JSON array containing exactly {scene_count} objects with keys:\n"
                    f"\"scene_number\", \"title\", \"visual_description\", \"camera_instruction\", \"audio_cue\", \"character_role_id\", \"lower_third_title\"."
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
                logger.warning(f"Gemini API call ({self.model}) failed for mashup: {e}. Using fallback generator.")

        return self._generate_fallback_mashup_scene_breakdown(
            char_a=char_a,
            char_b=char_b,
            mashup_genre=mashup_genre,
            parody_tone=parody_tone,
            product_name=product_name,
            product_description=product_description,
            product_tagline=product_tagline,
            scene_count=scene_count,
        )

    def _generate_fallback_mashup_scene_breakdown(
        self,
        char_a: Any,
        char_b: Any,
        mashup_genre: str,
        parody_tone: str,
        product_name: str | None,
        product_description: str | None,
        product_tagline: str | None,
        scene_count: int,
    ) -> list[dict[str, Any]]:
        """Generates dynamic 4-scene fallback breakdown alternating character beats & commercial parody."""
        scenes = []
        p_title = product_name or "Commercial Parody"
        p_tag = product_tagline or "As seen on TV!"

        for i in range(1, scene_count + 1):
            if i == 1:
                scenes.append(
                    {
                        "scene_number": 1,
                        "title": f"Scene 1: {char_a.name} Entrance ({mashup_genre})",
                        "visual_description": f"{char_a.name} ({char_a.description}) makes a dramatic entrance in a {mashup_genre} scene with a {parody_tone} parody style.",
                        "camera_instruction": "Wide tracking hero entrance shot with dynamic cinematic lighting.",
                        "audio_cue": f"Signature entrance theme music for {char_a.name} with ambient reverb.",
                        "character_role_id": char_a.role_id,
                        "lower_third_title": {"name": char_a.name, "role": getattr(char_a, "image_role", "Protagonist") or "Protagonist"},
                    }
                )
            elif i == 2:
                scenes.append(
                    {
                        "scene_number": 2,
                        "title": f"Scene 2: {char_b.name} Confrontation",
                        "visual_description": f"{char_b.name} ({char_b.description}) interrupts {char_a.name}, sparking a comical standoff in {mashup_genre} style.",
                        "camera_instruction": "Over-the-shoulder medium shot cutting rapidly between characters.",
                        "audio_cue": "Tense standoff string music suddenly interrupted by a comical needle scratch.",
                        "character_role_id": char_b.role_id,
                        "lower_third_title": {"name": char_b.name, "role": getattr(char_b, "image_role", "Rival") or "Rival"},
                    }
                )
            elif i == 3:
                scenes.append(
                    {
                        "scene_number": 3,
                        "title": f"Scene 3: Commercial Parody - {p_title}",
                        "visual_description": f"The dramatic scene breaks for an absurd commercial parody pitching '{p_title}' ('{p_tag}') with high energy infomercial graphics.",
                        "camera_instruction": "Vibrant studio lighting with snappy zoom-in on product display.",
                        "audio_cue": f"Upbeat high-energy infomercial jingle with enthusiastic narrator pitching {p_title}.",
                        "character_role_id": char_a.role_id,
                        "lower_third_title": {"name": f"SPONSOR: {p_title}", "role": p_tag},
                    }
                )
            elif i == 4:
                scenes.append(
                    {
                        "scene_number": 4,
                        "title": f"Scene 4: Mashup Climax - {char_a.name} & {char_b.name}",
                        "visual_description": f"{char_a.name} and {char_b.name} combine forces using {product_name or 'their ultimate parody powers'} for an explosive climactic finale in {mashup_genre} style.",
                        "camera_instruction": "360-degree orbital camera pan with slow-motion visual effects.",
                        "audio_cue": "Epic orchestral mashup soundtrack ending with victorious fanfare and audience applause.",
                        "character_role_id": char_a.role_id,
                        "lower_third_title": {"name": f"{char_a.name} x {char_b.name}", "role": "Epic Mashup Finale"},
                    }
                )
            else:
                char = char_a if i % 2 == 1 else char_b
                scenes.append(
                    {
                        "scene_number": i,
                        "title": f"Scene {i}: Mashup Beat {i} - {char.name}",
                        "visual_description": f"Action beat starring {char.name} continuing the {mashup_genre} parody duel.",
                        "camera_instruction": "Dynamic tracking shot with kinetic motion.",
                        "audio_cue": "Fast-paced action music.",
                        "character_role_id": char.role_id,
                        "lower_third_title": {"name": char.name, "role": mashup_genre},
                    }
                )

        return scenes

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

