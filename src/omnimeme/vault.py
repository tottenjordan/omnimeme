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


MASHUP_PRESET_BUNDLES: list[dict[str, Any]] = [
    {
        "id": "space_lord_vs_chef",
        "title": "Space Lord vs. Galactic Chef",
        "description": "Dark Lord of the Galaxy battles a master chef in a reality TV kitchen showdown.",
        "character_a": {
            "role_id": "space_lord",
            "name": "Space Lord",
            "description": "Dark armored galactic tyrant with heavy breathing mask and plasma saber.",
            "aesthetic_tags": ["Sci-Fi", "Villain", "Space Opera"],
            "voice_style": "Deep menacing mechanical voice",
            "wardrobe": "Obsidian armor with flowing black cape",
            "image_role": "Galactic Villain",
        },
        "character_b": {
            "role_id": "chef_supreme",
            "name": "Chef Supreme",
            "description": "Fiery celebrity chef wielding high-tech culinary utensils.",
            "aesthetic_tags": ["Comedy", "Culinary", "Reality TV"],
            "voice_style": "Loud energetic passionate shouting",
            "wardrobe": "Pristine white chef coat with gold embroidery and chef hat",
            "image_role": "Master Chef",
        },
        "mashup_genre": "Sci-Fi Reality Cooking Show",
        "parody_tone": "Absurdist Satire",
        "product": {
            "name": "Lightsaber Blender 9000",
            "description": "Plasma-powered countertop blender that purees ingredients at lightspeed.",
            "image_url": "gs://omnimeme-assets/products/lightsaber_blender.png",
            "tagline": "Puree with the Force!",
        },
    },
    {
        "id": "cyber_ronin_vs_noir_detective",
        "title": "Cyber Ronin vs. Noir Detective",
        "description": "A neon cyber samurai gets interviewed by a 1940s hard-boiled detective in rainy Neo-Chicago.",
        "character_a": {
            "role_id": "cyberpunk_ronin",
            "name": "Cyberpunk Ronin",
            "description": "Lone cybernetic samurai with glowing plasma katana in neon rain.",
            "aesthetic_tags": ["Cyberpunk", "Neon Noir", "Futuristic"],
            "voice_style": "Low gravelly synth bass",
            "wardrobe": "Dark high-collar trenchcoat over carbon-fiber body armor",
            "image_role": "Primary Protagonist",
        },
        "character_b": {
            "role_id": "film_noir_detective",
            "name": "Film Noir Detective",
            "description": "Hard-boiled investigator in rain-slicked city streets.",
            "aesthetic_tags": ["Noir", "Monochrome", "Vintage"],
            "voice_style": "Smooth voiceover monologue, raspy",
            "wardrobe": "Classic brown fedora, classic trench coat, smoking cigarette",
            "image_role": "Lead Investigator",
        },
        "mashup_genre": "Neon Cyber-Noir Detective Thriller",
        "parody_tone": "Hard-Boiled Parody",
        "product": {
            "name": "Cyber-Fedora Neural HUD",
            "description": "Classic felt fedora upgraded with 8K holographic crime-scene scanner.",
            "image_url": "gs://omnimeme-assets/products/cyber_fedora.png",
            "tagline": "Solve crimes in timeless style.",
        },
    },
    {
        "id": "sorcerer_vs_mech_pilot",
        "title": "Fantasy Sorcerer vs. Anime Mech Pilot",
        "description": "Ancient arch-mage challenges futuristic giant robot pilot to an infomercial duel.",
        "character_a": {
            "role_id": "fantasy_sorcerer",
            "name": "Fantasy Sorcerer",
            "description": "Mystical arch-mage channeling glowing arcane runes.",
            "aesthetic_tags": ["Fantasy", "Arcane", "High Magic"],
            "voice_style": "Resonant, echoing, ancient",
            "wardrobe": "Midnight blue embroidered velvet robes with crystal staff",
            "image_role": "Arcane Spellcaster",
        },
        "character_b": {
            "role_id": "anime_mech_pilot",
            "name": "Anime Mech Pilot",
            "description": "Ace starfighter pilot in sleek combat suit.",
            "aesthetic_tags": ["Anime", "Mecha", "Cinematic"],
            "voice_style": "Enthusiastic, sharp, intense",
            "wardrobe": "White and crimson plugsuit with holographic HUD elements",
            "image_role": "Hero Pilot",
        },
        "mashup_genre": "Mecha Fantasy Crossover",
        "parody_tone": "Over-The-Top Anime Parody",
        "product": {
            "name": "Mana-Shield Energy Drink",
            "description": "Arcane-infused sports drink providing instant spell slots and mech battery charges.",
            "image_url": "gs://omnimeme-assets/products/mana_shield_drink.png",
            "tagline": "Power your magic. Charge your mech.",
        },
    },
]


