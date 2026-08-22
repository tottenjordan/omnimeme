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
