# Project Guidelines - OmniMeme Gemini Omni Flash Video Directing Agent

> **IMPORTANT**: Always refer to [`CODE_STANDARDS.md`](file:///usr/local/google/home/jordantotten/omnimeme/CODE_STANDARDS.md) before writing code, creating dependencies, or making environment changes.

## Overview
This repository contains an ADK-based agentic workflow in Python using `google-agents-cli` for generating videos with Gemini Omni Flash preview.
It uses Gemini Enterprise Agent Platform to source the model API and deploy and scale the agent.

## User Interfaces
1. **Guided Experience**: Structured prompt generator for directing camera, subject, motion, lighting, mood, audio.
2. **Free-form Text Widget**: Natural language text input enhanced by the Video Directing ADK agent.

## Development Workflow
- **Package & Dependency Management**: `uv`
- **Lint & Format**: `ruff`
- **Type Check**: `ty`
- **Unit/Contract Testing**: `pytest`
- **Agent Development, Smoke Testing & Eval**: `agents-cli` (`agents-cli run`, `agents-cli eval run`)
- **Documentation & Notes**: Saved in [`docs/notes/`](file:///usr/local/google/home/jordantotten/omnimeme/docs/notes/README.md)
