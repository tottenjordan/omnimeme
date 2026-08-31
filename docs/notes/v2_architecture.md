# OmniMeme v2 Architecture & Feature Overview

## 🎬 Core Features
1. **A2A Creative Scriptwriter Agent (`ScriptwriterAgent`)**: Accepts high-level creative concepts and structures multi-scene storyboards delegating scene configs to `OmniDirectorAgent` via Google A2A protocol.
2. **Master Film Concatenation Engine (`concatenate_storyboard_videos`)**: Merges sequential scene clips into a single master MP4 movie with FFmpeg fallbacks.
3. **Character Archetype Gallery**: Offers 1-click character archetype presets (*Cyberpunk Ronin*, *Sci-Fi Fleet Captain*, *Anime Mech Pilot*, *Fantasy Sorcerer*, *Film Noir Detective*).
4. **Automated CI/CD Workflows**: Multi-stage GitHub Actions workflows with FFmpeg binary installation and Cloud Run deployment checks.
