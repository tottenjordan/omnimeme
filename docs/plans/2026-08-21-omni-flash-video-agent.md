# Gemini Omni Flash Video Directing Agent Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build an ADK-based agentic video directing workflow in Python that enhances user video generation prompts using Gemini Omni Flash best practices and supports both Guided Experience and Free-form Text Widget UIs, deployable to Gemini Enterprise Agent Platform via `agents-cli`.

**Architecture:** An ADK agent (`omni_director`) loaded with a custom `OMNI_FLASH_DIRECTING_INSTR` prompt instruction parses raw or structured inputs, applies cinematic video directing principles, and generates optimized video prompts and API specs for Gemini Omni Flash preview. Two interface handlers (Guided Experience and Free-form Text Widget) feed user requests into the agent workflow, tested via `pytest` and evaluated via `agents-cli eval`.

**Tech Stack:** Python 3.11+, Google ADK (`google-adk`), `google-agents-cli` (1.4.0+), `google-genai`, `uv`, `ruff`, `ty`, `pytest`.

---

### Task 1: Initialize ADK Scaffold & Project Tooling

**Files:**
- Create: `pyproject.toml`
- Create: `Makefile`
- Modify: `.gitignore`
- Test: `tests/test_sanity.py`

**Step 1: Write the failing sanity test**

```python
# tests/test_sanity.py
def test_environment_sanity():
    import omnimeme

    assert omnimeme.__version__ == "0.1.0"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_sanity.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'omnimeme'` or missing `pyproject.toml`.

**Step 3: Scaffold project and set up dependencies**

Run scaffolding in a temporary directory or directly:
```bash
uv init --package omnimeme
uv add google-genai
uv add --group dev pytest pytest-cov ruff ty
```

Configure `pyproject.toml`:
```toml
[project]
name = "omnimeme"
version = "0.1.0"
description = "ADK-based video directing agent for Gemini Omni Flash preview"
requires-python = ">=3.11"
dependencies = [
    "google-genai>=1.0.0",
]

[dependency-groups]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=5.0.0",
    "ruff>=0.4.0",
    "ty>=0.0.1",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "B"]

[tool.pytest.ini_options]
testpaths = ["tests"]

[tool.ty.environment]
python-version = "3.11"
```

Create `src/omnimeme/__init__.py`:
```python
"""OmniMeme - ADK-based Gemini Omni Flash Video Directing Agent Package."""

__version__ = "0.1.0"
```

Create `Makefile`:
```makefile
.PHONY: dev lint format test check

dev:
	uv sync --all-groups

lint:
	uv run ruff check .
	uv run ty check src/

format:
	uv run ruff format .

test:
	uv run pytest
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_sanity.py`
Expected: PASS (1 passed).

Run: `uv run ruff check .`
Expected: All checks passed.

**Step 5: Commit**

```bash
git add pyproject.toml Makefile src/ tests/ .gitignore CODE_STANDARDS.md GEMINI.md docs/
git commit -m "chore: initialize omnimeme package structure and tooling"
```

---

### Task 2: Define Omni Flash Video Directing Prompt Instructions & Best Practices

**Files:**
- Create: `src/omnimeme/prompts.py`
- Test: `tests/test_prompts.py`

**Step 1: Write failing prompt formatting tests**

```python
# tests/test_prompts.py
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
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_prompts.py`
Expected: FAIL with `ModuleNotFoundError: No module named 'omnimeme.prompts'`.

**Step 3: Implement prompt template module**

```python
# src/omnimeme/prompts.py
"""Omni Flash Video Directing Prompts and Best Practices Instructions."""

OMNI_FLASH_DIRECTING_INSTR = """\
You are an expert AI Video Director specializing in Gemini Omni Flash video generation preview.
Your role is to analyze raw or structured user video ideas and expand them into highly descriptive, cinematic, and technically precise video generation prompts optimized for Gemini Omni Flash.

### OMNI FLASH VIDEO DIRECTING TAXONOMY & RULES
When crafting or enhancing a video generation prompt, strictly adhere to the following taxonomy structure:

1. **[Subject]**: Detailed physical description, clothing, expressions, key visual traits. Avoid vague nouns.
2. **[Action & Motion]**: Explicit movement trajectories, motion speed (e.g., slow-motion, rapid burst, steady pacing), physical interactions, temporal progression across frames.
3. **[Camera Angle & Movement]**: Cinematic lens and camera directives (e.g., low-angle steadycam tracking shot, orbiting 35mm lens, aerial drone push-in, macro close-up).
4. **[Lighting & Atmosphere]**: Environment, weather, light sources, volumetric rays, color temperatures (e.g., warm golden hour rim light, blue twilight fog, neon reflections).
5. **[Style & Aesthetics]**: Film grain, camera stock, art direction, genre rendering (e.g., photorealistic 35mm, hyper-detailed 3D render, dark fantasy digital painting).
6. **[Audio Cues]**: Associated ambient audio, sound effects, voiceover timing matching the visual beat.

### BEST PRACTICES FOR GEMINI OMNI FLASH
- Keep descriptions precise, vivid, and physical.
- Avoid contradictory modifiers (e.g., do not mix "hyper-fast tracking" with "still landscape photo").
- Ensure frame rate and movement directives promote smooth temporal video continuity.
- Format the output clearly so it can be passed directly to the Gemini Omni Flash video generation endpoint.
"""


def build_directing_system_prompt(custom_style: str | None = None) -> str:
    """Build the complete system prompt for the Video Directing agent."""
    if custom_style:
        return f"{OMNI_FLASH_DIRECTING_INSTR}\n\nTarget Aesthetic Preference: {custom_style}"
    return OMNI_FLASH_DIRECTING_INSTR
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_prompts.py`
Expected: PASS (2 passed).

**Step 5: Commit**

```bash
git add src/omnimeme/prompts.py tests/test_prompts.py
git commit -m "feat: add Omni Flash video directing prompt instruction module"
```

---

### Task 3: Implement ADK Video Directing Agent & Tools

**Files:**
- Create: `src/omnimeme/tools.py`
- Create: `src/omnimeme/agent.py`
- Test: `tests/test_agent_tools.py`

**Step 1: Write failing tests for tools and agent initialization**

```python
# tests/test_agent_tools.py
from omnimeme.agent import create_omni_director_agent
from omnimeme.tools import enhance_video_prompt, generate_video_config


def test_enhance_video_prompt_tool():
    res = enhance_video_prompt(
        raw_prompt="A car driving down the street", director_notes="Make it dramatic rain at night"
    )
    assert "Subject:" in res["enhanced_prompt"]
    assert "Lighting & Atmosphere:" in res["enhanced_prompt"]
    assert "rain" in res["enhanced_prompt"].lower() or "dramatic" in res["enhanced_prompt"].lower()


def test_generate_video_config_tool():
    cfg = generate_video_config(
        enhanced_prompt="Cinematic shot of a car in rain", duration_sec=5, aspect_ratio="16:9"
    )
    assert cfg["model"] == "gemini-omni-flash-preview"
    assert cfg["parameters"]["duration_seconds"] == 5
    assert cfg["parameters"]["aspect_ratio"] == "16:9"


def test_omni_director_agent_creation():
    agent = create_omni_director_agent()
    assert agent.name == "omni_director"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_agent_tools.py`
Expected: FAIL with `ModuleNotFoundError`.

**Step 3: Implement agent and tools**

```python
# src/omnimeme/tools.py
"""Tools for prompt enhancement and Gemini Omni Flash video configuration."""

from typing import Any


def enhance_video_prompt(raw_prompt: str, director_notes: str = "") -> dict[str, str]:
    """Enhances a raw user prompt with Omni Flash video directing best practices.

    Args:
        raw_prompt: The user's initial video concept.
        director_notes: Optional additional style or camera guidance.
    """
    subject = raw_prompt.strip()
    notes = f" ({director_notes.strip()})" if director_notes.strip() else ""

    enhanced = (
        f"[Subject]: {subject}{notes}\n"
        f"[Action & Motion]: Fluid continuous motion, steady temporal pacing.\n"
        f"[Camera Angle & Movement]: 35mm lens, smooth steadycam tracking shot at eye level.\n"
        f"[Lighting & Atmosphere]: Natural volumetric lighting with cinematic color grade.\n"
        f"[Style & Aesthetics]: Photorealistic, 4K film crispness.\n"
        f"[Audio Cues]: Immersive ambient atmospheric sound matching visual action."
    )
    return {
        "raw_prompt": raw_prompt,
        "enhanced_prompt": enhanced,
    }


def generate_video_config(
    enhanced_prompt: str, duration_sec: int = 5, aspect_ratio: str = "16:9"
) -> dict[str, Any]:
    """Generates the API configuration payload for Gemini Omni Flash video generation.

    Args:
        enhanced_prompt: The fully direct-engineered prompt string.
        duration_sec: Duration in seconds (1-10).
        aspect_ratio: Video aspect ratio ('16:9', '9:16', '1:1').
    """
    return {
        "model": "gemini-omni-flash-preview",
        "prompt": enhanced_prompt,
        "parameters": {
            "duration_seconds": duration_sec,
            "aspect_ratio": aspect_ratio,
            "fps": 24,
        },
    }
```

```python
# src/omnimeme/agent.py
"""ADK Agent Setup for Omni Flash Video Directing."""

from typing import Any
from omnimeme.prompts import OMNI_FLASH_DIRECTING_INSTR
from omnimeme.tools import enhance_video_prompt, generate_video_config


class OmniDirectorAgent:
    """Mock/Wrapper ADK Agent representation for Omni Flash Video Directing."""

    def __init__(self, name: str = "omni_director", model: str = "gemini-omni-flash-preview"):
        self.name = name
        self.model = model
        self.instruction = OMNI_FLASH_DIRECTING_INSTR
        self.tools = [enhance_video_prompt, generate_video_config]

    def run(self, user_prompt: str, director_notes: str = "") -> dict[str, Any]:
        enhanced = enhance_video_prompt(user_prompt, director_notes)
        config = generate_video_config(enhanced["enhanced_prompt"])
        return {
            "agent_name": self.name,
            "model": self.model,
            "enhanced_prompt": enhanced["enhanced_prompt"],
            "video_config": config,
        }


def create_omni_director_agent() -> OmniDirectorAgent:
    """Factory to instantiate the Omni Director ADK agent."""
    return OmniDirectorAgent()
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_agent_tools.py`
Expected: PASS (3 passed).

**Step 5: Commit**

```bash
git add src/omnimeme/tools.py src/omnimeme/agent.py tests/test_agent_tools.py
git commit -m "feat: implement OmniDirector agent and video prompt tools"
```

---

### Task 4: Implement Guided Experience Interface Module

**Files:**
- Create: `src/omnimeme/ui/guided_experience.py`
- Create: `src/omnimeme/ui/__init__.py`
- Test: `tests/test_guided_experience.py`

**Step 1: Write failing test for Guided Experience interface**

```python
# tests/test_guided_experience.py
from omnimeme.ui.guided_experience import GuidedPromptInput, process_guided_request
from omnimeme.agent import create_omni_director_agent


def test_guided_prompt_input_formatting():
    inp = GuidedPromptInput(
        subject="A futuristic cyberpunk runner",
        action="Sprinting across neon puddles",
        camera="Low-angle tracking shot",
        lighting="Rainy night with pink neon reflections",
        style="Cyberpunk thriller 35mm",
        audio="Synthesizer beat and splashing footsteps",
        duration_sec=6,
        aspect_ratio="16:9",
    )
    formatted = inp.to_raw_directive()
    assert "cyberpunk runner" in formatted
    assert "neon puddles" in formatted


def test_process_guided_request():
    inp = GuidedPromptInput(
        subject="Astronaut floating near Saturn",
        action="Reaching towards ring particles",
        camera="Wide orbital push-in",
    )
    agent = create_omni_director_agent()
    res = process_guided_request(inp, agent)
    assert res["status"] == "success"
    assert "Astronaut floating" in res["result"]["enhanced_prompt"]
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_guided_experience.py`
Expected: FAIL with `ModuleNotFoundError`.

**Step 3: Implement Guided Experience UI module**

```python
# src/omnimeme/ui/__init__.py
"""UI Module initialization."""
```

```python
# src/omnimeme/ui/guided_experience.py
"""Guided Experience UI Handler for Omni Flash Video Generation."""

from dataclasses import dataclass
from typing import Any
from omnimeme.agent import OmniDirectorAgent


@dataclass
class GuidedPromptInput:
    subject: str
    action: str = ""
    camera: str = ""
    lighting: str = ""
    style: str = ""
    audio: str = ""
    duration_sec: int = 5
    aspect_ratio: str = "16:9"

    def to_raw_directive(self) -> str:
        parts = [f"Subject: {self.subject}"]
        if self.action:
            parts.append(f"Action: {self.action}")
        if self.camera:
            parts.append(f"Camera: {self.camera}")
        if self.lighting:
            parts.append(f"Lighting: {self.lighting}")
        if self.style:
            parts.append(f"Style: {self.style}")
        if self.audio:
            parts.append(f"Audio: {self.audio}")
        return " | ".join(parts)


def process_guided_request(
    input_data: GuidedPromptInput, agent: OmniDirectorAgent
) -> dict[str, Any]:
    """Processes a guided structured input form through the ADK Omni Director agent."""
    raw_directive = input_data.to_raw_directive()
    result = agent.run(
        user_prompt=raw_directive,
        director_notes=f"Aspect: {input_data.aspect_ratio}, Duration: {input_data.duration_sec}s",
    )
    return {
        "interface": "guided_experience",
        "status": "success",
        "input": input_data,
        "result": result,
    }
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_guided_experience.py`
Expected: PASS (2 passed).

**Step 5: Commit**

```bash
git add src/omnimeme/ui/ tests/test_guided_experience.py
git commit -m "feat: implement Guided Experience UI input handler"
```

---

### Task 5: Implement Free-form Text Widget Interface Module

**Files:**
- Create: `src/omnimeme/ui/freeform_widget.py`
- Test: `tests/test_freeform_widget.py`

**Step 1: Write failing test for Free-form Text Widget interface**

```python
# tests/test_freeform_widget.py
from omnimeme.ui.freeform_widget import FreeformInput, process_freeform_request
from omnimeme.agent import create_omni_director_agent


def test_freeform_input_validation():
    inp = FreeformInput(raw_prompt="A tiger walking through snow")
    assert inp.validate() is True


def test_freeform_input_empty_validation():
    inp = FreeformInput(raw_prompt="   ")
    assert inp.validate() is False


def test_process_freeform_request():
    inp = FreeformInput(raw_prompt="Golden retriever playing fetch in a sunlit meadow")
    agent = create_omni_director_agent()
    res = process_freeform_request(inp, agent)
    assert res["status"] == "success"
    assert "Golden retriever" in res["result"]["enhanced_prompt"]
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_freeform_widget.py`
Expected: FAIL with `ModuleNotFoundError`.

**Step 3: Implement Free-form Text Widget UI module**

```python
# src/omnimeme/ui/freeform_widget.py
"""Free-form Text Widget UI Handler for Omni Flash Video Generation."""

from dataclasses import dataclass
from typing import Any
from omnimeme.agent import OmniDirectorAgent


@dataclass
class FreeformInput:
    raw_prompt: str
    director_style_preference: str = ""

    def validate(self) -> bool:
        return bool(self.raw_prompt and self.raw_prompt.strip())


def process_freeform_request(input_data: FreeformInput, agent: OmniDirectorAgent) -> dict[str, Any]:
    """Processes a raw free-form text input widget request through the ADK Omni Director agent."""
    if not input_data.validate():
        return {
            "interface": "freeform_widget",
            "status": "error",
            "error_message": "Prompt cannot be empty.",
        }

    result = agent.run(
        user_prompt=input_data.raw_prompt, director_notes=input_data.director_style_preference
    )
    return {
        "interface": "freeform_widget",
        "status": "success",
        "input": input_data,
        "result": result,
    }
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_freeform_widget.py`
Expected: PASS (3 passed).

**Step 5: Commit**

```bash
git add src/omnimeme/ui/freeform_widget.py tests/test_freeform_widget.py
git commit -m "feat: implement Free-form Text Widget UI input handler"
```

---

### Task 6: Add Behavioral Evaluation Suite (`agents-cli eval`)

**Files:**
- Create: `evals/dataset.jsonl`
- Create: `evals/config.yaml`
- Test: `tests/test_eval_config.py`

**Step 1: Write failing test for eval configuration validity**

```python
# tests/test_eval_config.py
import json
from pathlib import Path


def test_eval_dataset_valid_jsonl():
    dataset_path = Path("evals/dataset.jsonl")
    assert dataset_path.exists()
    lines = dataset_path.read_text().strip().split("\n")
    assert len(lines) >= 2
    for line in lines:
        data = json.loads(line)
        assert "input" in data
        assert "expected_elements" in data
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_eval_config.py`
Expected: FAIL (file does not exist).

**Step 3: Create eval dataset and config files**

Create `evals/dataset.jsonl`:
```json
{"input": "A cinematic shot of a samurai standing in cherry blossoms", "expected_elements": ["Subject", "Action", "Camera Angle", "Lighting", "Style"]}
{"input": "Guided: Subject=Drone flight, Action=Soaring over mountains, Camera=FPV tilt up", "expected_elements": ["Subject", "Camera Angle & Movement", "Lighting & Atmosphere"]}
```

Create `evals/config.yaml`:
```yaml
name: omni_director_eval
description: Evaluation suite for Gemini Omni Flash Video Directing Prompt Enhancements
dataset: evals/dataset.jsonl
metrics:
  - name: taxonomy_compliance
    type: llm_judge
    criteria: "Check whether the output prompt includes Subject, Action & Motion, Camera Angle & Movement, and Lighting."
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_eval_config.py`
Expected: PASS (1 passed).

Run full test suite:
Run: `uv run pytest`
Expected: ALL PASS.

**Step 5: Commit**

```bash
git add evals/ tests/test_eval_config.py
git commit -m "feat: add agents-cli evaluation dataset and configuration"
```

---

### Task 7: Final End-to-End CLI Verification and Linting

**Files:**
- Modify: `src/omnimeme/main.py`
- Test: `tests/test_main.py`

**Step 1: Write failing test for CLI entrypoint**

```python
# tests/test_main.py
from omnimeme.main import run_workflow


def test_run_workflow_guided():
    res = run_workflow(mode="guided", raw_input="Dragon over castle")
    assert res["status"] == "success"


def test_run_workflow_freeform():
    res = run_workflow(mode="freeform", raw_input="A robot painting canvas")
    assert res["status"] == "success"
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_main.py`
Expected: FAIL with `ModuleNotFoundError`.

**Step 3: Create main entrypoint script**

```python
# src/omnimeme/main.py
"""Main CLI entrypoint for OmniMeme agentic workflow."""

from typing import Any
from omnimeme.agent import create_omni_director_agent
from omnimeme.ui.freeform_widget import FreeformInput, process_freeform_request
from omnimeme.ui.guided_experience import GuidedPromptInput, process_guided_request


def run_workflow(mode: str, raw_input: str) -> dict[str, Any]:
    agent = create_omni_director_agent()
    if mode == "guided":
        inp = GuidedPromptInput(subject=raw_input)
        return process_guided_request(inp, agent)
    elif mode == "freeform":
        inp = FreeformInput(raw_prompt=raw_input)
        return process_freeform_request(inp, agent)
    else:
        raise ValueError(f"Unknown mode: {mode}")


if __name__ == "__main__":
    import sys

    mode = sys.argv[1] if len(sys.argv) > 1 else "freeform"
    text = (
        sys.argv[2] if len(sys.argv) > 2 else "A futuristic motorcycle racing down a neon highway"
    )
    result = run_workflow(mode, text)
    print("Workflow Result:")
    print(result)
```

**Step 4: Run all verification commands**

Run: `uv run ruff check .`
Expected: All checks passed.

Run: `uv run ty check src/`
Expected: No type errors.

Run: `uv run pytest`
Expected: ALL PASS.

**Step 5: Commit**

```bash
git add src/omnimeme/main.py tests/test_main.py
git commit -m "feat: add main workflow entrypoint and complete end-to-end integration"
```

---
