# Note: Agent Architecture & Gemini Enterprise Agent Platform

## Overview
This architecture uses Google's Agent Development Kit (ADK) and `agents-cli` to construct a video generation directing workflow.

## Platform Integration
- **Model API Source**: Gemini Enterprise Agent Platform (Vertex AI generative model endpoints for Gemini Omni Flash).
- **Deployment & Scaling**: Vertex AI Agent Runtime (`agent_runtime` target via `agents-cli`).
- **CLI Workflow**: Developed, evaluated, and deployed using `google-agents-cli`.

## ADK Agent Design
- **Video Directing Agent (`omni_director`)**: ADK agent loaded with `OMNI_FLASH_DIRECTING_INSTR` prompt template. It receives raw or structured inputs, applies video directing principles, and returns enhanced prompts + execution metadata for video generation API calls.
- **Workflow / Tools**:
  - `enhance_prompt`: Transforms user input into an optimized Omni Flash video generation prompt.
  - `generate_video_spec`: Prepares structured parameter payload for Gemini Enterprise Agent Platform video generation call.
