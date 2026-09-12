"""Tests for Character Vault domain models and persistence manager."""

from omnimeme.vault import CharacterRole, CharacterVault


def test_character_role_creation():
    char = CharacterRole(
        role_id="char_samurai_01",
        name="Cyber Samurai",
        description="Cyberpunk samurai in dark obsidian armor with glowing neon visor",
        aesthetic_tags=["cyberpunk", "photorealistic", "35mm"],
        voice_style="Deep gravelly baritone",
        image_role="Character Reference",
    )
    assert char.role_id == "char_samurai_01"
    assert char.image_tag == "@Image1: Character Reference - Cyber Samurai"


def test_character_vault_crud():
    vault = CharacterVault()
    char = CharacterRole(
        role_id="char_wizard_01",
        name="Potion Master",
        description="Elderly wizard in indigo robes",
    )
    vault.add_character(char)
    assert vault.get_character("char_wizard_01") == char
    assert len(vault.list_characters()) == 1

    vault.delete_character("char_wizard_01")
    assert vault.get_character("char_wizard_01") is None
    assert len(vault.list_characters()) == 0


def test_character_vault_file_persistence(tmp_path):
    storage_file = str(tmp_path / "test_vault.json")
    vault1 = CharacterVault(storage_file=storage_file)
    char = CharacterRole(
        role_id="char_persisted_01",
        name="Persisted Warrior",
        description="A warrior that survives restarts",
        aesthetic_tags=["persisted"],
    )
    vault1.add_character(char)

    # Instantiate new vault pointing to same storage file
    vault2 = CharacterVault(storage_file=storage_file)
    loaded_char = vault2.get_character("char_persisted_01")
    assert loaded_char is not None
    assert loaded_char.name == "Persisted Warrior"
    assert loaded_char.aesthetic_tags == ["persisted"]

    # Test delete persists
    vault2.delete_character("char_persisted_01")
    vault3 = CharacterVault(storage_file=storage_file)
    assert vault3.get_character("char_persisted_01") is None
