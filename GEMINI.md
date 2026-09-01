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

## 🛡️ Mandatory Workflow Rules & Deployment Conventions
1. **Pull Request Isolation**: ALL code changes must strictly be committed to a feature branch, pushed to GitHub, and submitted as a Pull Request (`gh pr create`).
2. **Explicit PR Review**: NEVER merge a Pull Request into `main` until the user explicitly confirms GitHub review approval.
3. **Deployment Verification**: Always verify deployment status dynamically using `gcloud run services describe omnimeme` or `agents-cli deploy --status` rather than relying on legacy metadata fields.
4. **Media Teardown**: Temporary rendered test artifacts (`static/rendered/*.mp4`, `*.wav`) must never be committed to Git and must be cleaned up automatically.

