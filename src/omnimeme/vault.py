"""Project-Level Character Vault for OmniMeme."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CharacterRole:
    role_id: str
    name: str
    description: str
    turnaround_sheet_url: str | None = None
    aesthetic_tags: list[str] = field(default_factory=list)
    voice_style: str = ""
    wardrobe: str = ""
    image_role: str = "Character Reference"

    @property
    def image_tag(self) -> str:
        return f"@Image1: {self.image_role} - {self.name}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "role_id": self.role_id,
            "name": self.name,
            "description": self.description,
            "turnaround_sheet_url": self.turnaround_sheet_url,
            "aesthetic_tags": self.aesthetic_tags,
            "voice_style": self.voice_style,
            "wardrobe": self.wardrobe,
            "image_role": self.image_role,
            "image_tag": self.image_tag,
        }


class CharacterVault:
    """In-memory and file-persisted vault for managing project characters."""

    def __init__(self):
        self._characters: dict[str, CharacterRole] = {}

    def add_character(self, character: CharacterRole) -> CharacterRole:
        self._characters[character.role_id] = character
        return character

    def get_character(self, role_id: str) -> CharacterRole | None:
        return self._characters.get(role_id)

    def list_characters(self) -> list[CharacterRole]:
        return list(self._characters.values())

    def delete_character(self, role_id: str) -> bool:
        if role_id in self._characters:
            del self._characters[role_id]
            return True
        return False


CHARACTER_ARCHETYPE_PRESETS: list[dict[str, Any]] = [
    {
        "role_id": "cyberpunk_ronin",
        "name": "Cyberpunk Ronin",
        "description": "Lone cybernetic samurai with glowing plasma katana in neon rain.",
        "aesthetic_tags": ["Cyberpunk", "Neon Noir", "Futuristic"],
        "voice_style": "Low gravelly synth bass",
        "wardrobe": "Dark high-collar trenchcoat over carbon-fiber body armor",
        "image_role": "Primary Protagonist",
    },
    {
        "role_id": "scifi_captain",
        "name": "Sci-Fi Captain",
        "description": "Commanding starship captain with tactical visor and dress uniform.",
        "aesthetic_tags": ["Sci-Fi", "Space Opera", "Commanding"],
        "voice_style": "Authoritative, calm, clear",
        "wardrobe": "Deep navy naval tunic with gold rank pins and shoulder pauldrons",
        "image_role": "Fleet Commander",
    },
    {
        "role_id": "anime_mech_pilot",
        "name": "Anime Mech Pilot",
        "description": "Ace starfighter pilot in sleek combat suit.",
        "aesthetic_tags": ["Anime", "Mecha", "Cinematic"],
        "voice_style": "Enthusiastic, sharp, intense",
        "wardrobe": "White and crimson plugsuit with holographic HUD elements",
        "image_role": "Hero Pilot",
    },
    {
        "role_id": "fantasy_sorcerer",
        "name": "Fantasy Sorcerer",
        "description": "Mystical arch-mage channeling glowing arcane runes.",
        "aesthetic_tags": ["Fantasy", "Arcane", "High Magic"],
        "voice_style": "Resonant, echoing, ancient",
        "wardrobe": "Midnight blue embroidered velvet robes with crystal staff",
        "image_role": "Arcane Spellcaster",
    },
    {
        "role_id": "film_noir_detective",
        "name": "Film Noir Detective",
        "description": "Hard-boiled investigator in rain-slicked city streets.",
        "aesthetic_tags": ["Noir", "Monochrome", "Vintage"],
        "voice_style": "Smooth voiceover monologue, raspy",
        "wardrobe": "Classic brown fedora, classic trench coat, smoking cigarette",
        "image_role": "Lead Investigator",
    },
]

