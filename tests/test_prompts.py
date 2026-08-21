from omnimeme.prompts import OMNI_FLASH_DIRECTING_INSTR, build_directing_system_prompt


def test_omni_flash_instruction_contains_taxonomy():
    assert "Subject" in OMNI_FLASH_DIRECTING_INSTR
    assert "Action & Motion" in OMNI_FLASH_DIRECTING_INSTR
    assert "Camera Angle & Movement" in OMNI_FLASH_DIRECTING_INSTR
    assert "Lighting & Atmosphere" in OMNI_FLASH_DIRECTING_INSTR
    assert "Style & Aesthetics" in OMNI_FLASH_DIRECTING_INSTR
    assert "Audio Cues" in OMNI_FLASH_DIRECTING_INSTR


def test_build_directing_system_prompt_custom_context():
    prompt = build_directing_system_prompt(custom_style="Anime")
    assert "Anime" in prompt
    assert "Omni Flash" in prompt
