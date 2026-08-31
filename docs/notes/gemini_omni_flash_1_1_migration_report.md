# Technical Research & Migration Report: Gemini Omni Flash 1.1 (`gemini-omni-1.1-flash-preview` / `gemini-omni-1.1-flash`)

---

## EXECUTIVE SUMMARY

This report evaluates **Gemini Omni Flash 1.1** (`gemini-omni-1.1-flash-preview` / `gemini-omni-1.1-flash`) against legacy **Gemini Omni Flash Preview** (`gemini-omni-flash-preview`) and details architectural implications for the **OmniMeme Video Directing Studio** (`/usr/local/google/home/jordantotten/omnimeme`).

> [!IMPORTANT]
> **Deprecation Notice**: Legacy `gemini-omni-flash-preview` will be deprecated on **September 30, 2026**. Upgrading model strings across `omnimeme` to `gemini-omni-1.1-flash` is required for production longevity.

---

## SECTION 1: NEW FEATURES & COMPARATIVE TECHNICAL MATRIX

| Feature / Capability | Previous Model (`gemini-omni-flash-preview`) | Upgraded Model (`gemini-omni-1.1-flash-preview`) | Repository Implications for `omnimeme` |
| :--- | :--- | :--- | :--- |
| **Scene Extension Context Window** | Referenced only the **final 1 second** of prior video, causing visual drift across edit turns. | Analyzes up to **10 seconds of prior context memory** via `previous_interaction_id`; extends scenes in 10s increments up to **40s cumulative length**. | Fixes visual drift in [Screening Room Conversational Edits](file:///usr/local/google/home/jordantotten/omnimeme/frontend/src/App.tsx#L489-L524). Enables multi-turn scene extension controls. |
| **Keyframe Interpolation (First & Last Frame)** | Single keyframe input only (Prompt-to-Video or start-frame Image-to-Video). | **First and Last Frame Keyframing**: Generates continuous video transitioning between starting (`first_frame`) and ending (`last_frame`) images (whip-pans, dolly zooms, orbital rotations, seamless loops). | Enables keyframe transition workflows in [Guided Experience](file:///usr/local/google/home/jordantotten/omnimeme/src/omnimeme/ui/guided_experience.py#L26-L74) and UI form controls. |
| **Resolution Controls & Draft Mode** | Fixed 720p output resolution. Latency bottleneck for rapid iterations. | **360p Fast Draft Mode** (up to 60% faster throughput, 1/3 API cost) alongside **720p**, **1080p**, and **4K High-Res** upscaling options. | Requires adding `resolution` select control in [Video Config Generator](file:///usr/local/google/home/jordantotten/omnimeme/src/omnimeme/tools.py#L59-L84) and React UI state in [App.tsx](file:///usr/local/google/home/jordantotten/omnimeme/frontend/src/App.tsx#L119-L130). |
| **Multimodal Input References** | Text prompts and static images (`.png`/`.jpeg`) only. | **Video Reference Input**: Reference up to **3 seconds of video clips** in multimodal input array for motion matching, pose alignment, and character choreography. | Extends [MediaAttachment](file:///usr/local/google/home/jordantotten/omnimeme/src/omnimeme/ui/guided_experience.py#L10-L22) and [Character Vault](file:///usr/local/google/home/jordantotten/omnimeme/src/omnimeme/vault.py#L8-L33) to pass GCS `.mp4` URIs as reference assets. |
| **Native Sound & Audio Generation** | Basic audio generation; required procedural waveform fallback engine. | **Native Multimodal Audio Generation** (Speech, ambient sound effects, and synchronized music score directly in `output_video`). | Allows replacing local procedural audio synthesis ([`_generate_dynamic_audio_wav`](file:///usr/local/google/home/jordantotten/omnimeme/src/omnimeme/engine.py#L48-L101)) with model-native synced audio. |
| **Context Window & Capabilities Boundaries** | 32k legacy tokens. | **131,072 Input Tokens**, **57,920 Output Tokens** (Enterprise Agent Platform) / 1M tokens (Developer API). Native Thinking Mode supported. System instructions & function calling **not supported**. | Prompts and directives must be passed as input text blocks to `client.interactions.create()`, as native tool calling is unsupported on Omni Flash. |

---

## SECTION 2: APPLICATION & USER JOURNEY HIGHLIGHTS

Upgrading `omnimeme` to `gemini-omni-1.1-flash-preview` impacts four primary user journey touchpoints.

### Highlight 1: Guided Experience Prompt Generator & Parameter Controls
- **Affected Repository Files**:
  - [`src/omnimeme/tools.py`](file:///usr/local/google/home/jordantotten/omnimeme/src/omnimeme/tools.py#L59-L84) (`generate_video_config`)
  - [`src/omnimeme/agent.py`](file:///usr/local/google/home/jordantotten/omnimeme/src/omnimeme/agent.py#L16) (`OmniDirectorAgent.__init__`)
  - [`src/omnimeme/ui/guided_experience.py`](file:///usr/local/google/home/jordantotten/omnimeme/src/omnimeme/ui/guided_experience.py#L26-L74) (`GuidedPromptInput`)
  - [`frontend/src/App.tsx`](file:///usr/local/google/home/jordantotten/omnimeme/frontend/src/App.tsx#L119-L130) (`guidedInput` state)
- **Current Functionality**:
  - Guided Experience collects `subject`, `action`, `camera`, `lighting`, `style`, `audio`, `duration_sec` (1-10s), and `aspect_ratio` (`16:9`, `9:16`).
  - [`generate_video_config`](file:///usr/local/google/home/jordantotten/omnimeme/src/omnimeme/tools.py#L74) hardcodes `"model": "gemini-omni-flash-preview"`, with no resolution or draft selector.
- **1.1 Model Feature**:
  - Adds `"resolution"` (`360p`, `720p`, `1080p`, `4k`) and support for keyframe specification in `response_format`.
- **User Journey Impact**:
  - Directors can rapidly prototype scene concepts in **360p Draft Mode** (60% faster, 66% lower cost) before committing to a final **4K production render**.
- **Recommendations**:
  1. Update `model` string in [`agent.py`](file:///usr/local/google/home/jordantotten/omnimeme/src/omnimeme/agent.py#L16) and [`tools.py`](file:///usr/local/google/home/jordantotten/omnimeme/src/omnimeme/tools.py#L74) from `gemini-omni-flash-preview` to `gemini-omni-1.1-flash`.
  2. Add `resolution` property to [`GuidedPromptInput`](file:///usr/local/google/home/jordantotten/omnimeme/src/omnimeme/ui/guided_experience.py#L26-L37) and UI dropdown in [`App.tsx`](file:///usr/local/google/home/jordantotten/omnimeme/frontend/src/App.tsx#L753-L774).
  3. Add input fields for `first_frame_uri` and `last_frame_uri` keyframes to trigger smooth camera transition interpolation.

---

### Highlight 2: Project Character Vault & Multimodal Reference Attachments
- **Affected Repository Files**:
  - [`src/omnimeme/vault.py`](file:///usr/local/google/home/jordantotten/omnimeme/src/omnimeme/vault.py#L8-L33) (`CharacterRole`)
  - [`src/omnimeme/turnaround.py`](file:///usr/local/google/home/jordantotten/omnimeme/src/omnimeme/turnaround.py#L38-L68) (`generate_turnaround_sheet_config`)
  - [`frontend/src/App.tsx`](file:///usr/local/google/home/jordantotten/omnimeme/frontend/src/App.tsx#L574-L644) (Character Vault Studio Toolbar)
- **Current Functionality**:
  - Character Vault attaches 4-panel turnaround sheets (`@Image1: Character Reference`) via image GCS URIs.
  - Media attachments in [`guided_experience.py`](file:///usr/local/google/home/jordantotten/omnimeme/src/omnimeme/ui/guided_experience.py#L10-L22) support video MIME types in dataclass, but payload generation in `tools.py` defaulted to image references.
- **1.1 Model Feature**:
  - **Multimodal Video References**: Accepts up to 3-second reference videos in `reference_assets` for motion transfer, pose matching, and choreography.
- **User Journey Impact**:
  - Creators can attach performance reference clips (e.g., dance routines, action choreography) alongside character turnaround images.
- **Recommendations**:
  1. Enhance [`generate_video_config`](file:///usr/local/google/home/jordantotten/omnimeme/src/omnimeme/tools.py#L82-L84) to accept video MIME types (`video/mp4`, `video/webm`) in `reference_assets`.
  2. Add a "Motion Reference Clip" uploader to Character Vault cards in [`App.tsx`](file:///usr/local/google/home/jordantotten/omnimeme/frontend/src/App.tsx#L590-L640).

---

### Highlight 3: The Screening Room & Stateful Conversational Video Editing
- **Affected Repository Files**:
  - [`src/omnimeme/engine.py`](file:///usr/local/google/home/jordantotten/omnimeme/src/omnimeme/engine.py#L204-L281) (`OmniFlashExecutionEngine.generate_video`)
  - [`src/omnimeme/server/app.py`](file:///usr/local/google/home/jordantotten/omnimeme/src/omnimeme/server/app.py#L280-L299) (`/api/generate-video`)
  - [`frontend/src/App.tsx`](file:///usr/local/google/home/jordantotten/omnimeme/frontend/src/App.tsx#L489-L524) (`handleConversationalEdit`)
  - [`frontend/src/api/client.ts`](file:///usr/local/google/home/jordantotten/omnimeme/frontend/src/api/client.ts#L83-L99) (`executeVideoGeneration`)
- **Current Functionality**:
  - Users perform iterative video edits in "The Screening Room". Conversational edits pass `previous_interaction_id`.
  - In the previous model, context memory was limited to 1 second, causing subject morphing and visual drift over multi-turn edits.
- **1.1 Model Feature**:
  - **10-Second Context Analysis & 40s Cumulative Extension**: Maintains narrative and visual continuity across 10-second history buffers up to a 40-second total clip duration.
- **User Journey Impact**:
  - Directors can incrementally extend scenes (e.g. "Continue the shot for 10 more seconds and pan camera left") with smooth character and environmental continuity.
- **Recommendations**:
  1. Add an "Extend Scene (+10s)" action button in The Screening Room React UI in [`App.tsx`](file:///usr/local/google/home/jordantotten/omnimeme/frontend/src/App.tsx#L489-L524).
  2. Display cumulative clip timeline indicators (10s → 20s → 30s → 40s max).

---

### Highlight 4: Video Execution Engine & Audio Synthesis Pipeline
- **Affected Repository Files**:
  - [`src/omnimeme/engine.py`](file:///usr/local/google/home/jordantotten/omnimeme/src/omnimeme/engine.py#L48-L176) (`_generate_dynamic_audio_wav` & `ensure_rendered_video`)
- **Current Functionality**:
  - Engine uses procedural wave synthesizer `_generate_dynamic_audio_wav` and FFmpeg filter complex in `ensure_rendered_video` to generate preview audio waveforms.
- **1.1 Model Feature**:
  - **Native Multimodal Audio Generation**: Model outputs synchronized speech, sound effects, and music score natively inside the returned MP4 container.
- **User Journey Impact**:
  - Production API generations provide realistic audio without relying on synthetic waveform fallbacks.
- **Recommendations**:
  1. Preserve FFmpeg pipeline for `mock_mode=True` local execution.
  2. For live API executions (`mock_mode=False`), decode native video and audio channels directly from `interaction.output_video`.

---

## SECTION 3: RECOMMENDED INTERNAL AND EXTERNAL RESOURCES

### Internal Google Resources & Documentation
1. **Internal Architecture & Best Practice Guide**:
   - Path: `//depot/company/teams/cloud-fde/L2_Architectural_Patterns/Models/Prompt_Engineering/Gemini_Omni_Flash.md`
   - *Description*: Technical patterns for stateful Interactions API sessions, editing prompt discipline ("Keep everything else the same"), single-scene enforcement, and parameter constraints.
2. **Vertex AI SRE Model Playbook**:
   - Path: `playbooks/cloud-ml/llm/gemini-omni-1.1-flash-preview.md`
   - *Description*: Internal architecture breakdown of backend stations (`368p`, `720p`, `1080p` upsampler, `4K` upsampler, SynthID watermarking endpoints, and Cardolan/GRoot infrastructure).
3. **Internal Release Announcements**:
   - Link: `go/tools-weekly-report` (May 25, 2026 Gemini Omni Flash release summary).
   - *Description*: Launch highlights detailing multimodal capabilities and ADK integration.
4. **Internal Pricing & Model Directory**:
   - Link: `go/prices` & `go/gemini-model-variants/gemini-omni-flash`
   - *Description*: Official model endpoints, context limits, and pricing tiers across Google AI Studio and Enterprise Agent Platform.

### External Public Documentation
1. **Google Cloud Gemini Omni 1.1 Documentation**:
   - Link: [`https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/omni-1-1-flash`](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/omni-1-1-flash)
   - *Description*: Official feature table, token limits (131k input / 57k output), and Agent Studio links.
2. **Google Developers Launch Blog**:
   - Link: [`https://blog.google/innovation-and-ai/technology/developers-tools/build-with-gemini-omni-1-1-flash/`](https://blog.google/innovation-and-ai/technology/developers-tools/build-with-gemini-omni-1-1-flash/)
   - *Description*: Code examples for Python SDK `client.interactions.create()`, video extension snippets, keyframing demonstrations, and 360p draft benchmark data.
3. **Gemini API Technical Guide & Video Understanding**:
   - Link: [`https://ai.google.dev/gemini-api/docs/omni`](https://ai.google.dev/gemini-api/docs/omni) & [`https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/capabilities/video-understanding`](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/capabilities/video-understanding)
   - *Description*: Supported video MIME types, aspect ratios (`16:9`, `9:16`), and REST/Python/JS SDK code patterns.
