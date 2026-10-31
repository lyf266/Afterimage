# AGENTS.md - Afterimage Autonomous Agent Guidelines

## 1. Project Mission & Identity
**Afterimage (残影)** is a native Linux KDE Plasma 6 (Wayland) desktop cognitive telemetry and autonomous AI retrospective synthesis engine.
It extends `desktop-timetracker` by adding local-first AI analysis, attention/flow modeling, context-switching cognitive loss calculation, and multi-format structured retrospective outputs (Markdown, Obsidian, natural language CLI).

## 2. Architecture & Design Principles
1. **Zero-disruption Wayland event backbone**:
   - Must use native KWin scripts and D-Bus interfaces. Never use X11 tools (`xdotool`, `xprop`) or periodic full-screen screenshots.
   - Resource budget: resident memory < 20 MB, idle CPU < 0.1%.
2. **Local Privacy & Strict Redaction**:
   - All raw telemetry is stored in local SQLite (`~/.local/share/afterimage/afterimage.db`).
   - Prioritize backward compatibility with existing `desktop-timetracker` databases (`~/.local/share/timetracker/timetracker.db`).
   - Before passing any activity data or window titles to an LLM, run through `src/ai/sanitizer.py` to scrub tokens, passwords, and file paths.
3. **Pluggable AI Backends**:
   - Support offline inference via local Ollama (`http://localhost:11434`).
   - Support cloud models (Gemini API, DeepSeek, OpenAI compatible) via user-provided environment variables or configuration.
4. **Hardware Input Privacy**:
   - `evdev` counters must remain purely aggregated metrics (KPM typing speed, travel distance in meters, click count). Never capture keycodes or screen coordinates.

## 3. Testing & Verification Gates
- Unit Tests:
  ```bash
  python3 -m unittest discover tests/
  ```
- Linter & Formatting:
  ```bash
  python3 -m py_compile src/afterimage
  ```

## 4. Quality & Commit Rules
- Follow conventional commits: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`.
- All documentation and code changes must adhere to the global typography rules (Source Han Sans SC for Chinese/multilingual presentation).
- Never claim a feature is complete without running verification commands.
