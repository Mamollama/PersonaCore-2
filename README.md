# PersonaCore 2

> Ollama-powered AI video generation suite with a cinematic GUI

PersonaCore 2 is a local-first creative tool that combines the power of locally running Ollama language models with open-source video generation pipelines. Describe a concept in plain English, let an AI director expand it into a rich visual prompt, then generate and export a video — all without sending data to the cloud.

---

## Screenshot

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ ◈ PersonaCore 2   AI VIDEO SUITE                          ✕  −  ⤢          │
├──────────┬──────────────────────────────────────────────┬──────────────────┤
│ PROJECTS │  Prompt Studio                               │ Generate         │
│ ─────────│  ┌─────────────────────────────────────────┐│ STYLE PRESET     │
│ + New    │  │ Your Concept                            ││ Cinematic ▾      │
│          │  │ A lone astronaut walks across Mars...   ││ BACKEND          │
│ OLLAMA   │  └─────────────────────────────────────────┘│ Demo ▾           │
│ MODEL    │  [ ✦ Enrich with AI ]  [ Clear ]            │ RESOLUTION       │
│ llama3.2 │  ┌─────────────────────────────────────────┐│ 512×512 ▾        │
│ ─────────│  │ Director's Vision (streaming...)        ││ ──────────────── │
│ PERSONA  │  │ **SCENE DESCRIPTION**: The desolate...  ││ CONSOLE          │
│ Director │  └─────────────────────────────────────────┘│ [INF] Ready      │
│ ─────────│  [ ▶ Generate Video ]                       │ [INF] Enriching  │
│ HISTORY  ├──────────────────────────────────────────────┤                  │
│          │ ● Enriching → ● Generating → ○ Rendering    │                  │
│          │ ┌────────────────────────────────────────────┤                  │
│          │ │  [  Video Preview — animated placeholder ] │                  │
│          │ └────────────────────────────────────────────┘                  │
├──────────┴──────────────────────────────────────────────┴──────────────────┤
│ Ready — enrich a prompt to get started        GPU: 42%  CPU: 12%  RAM: 8GB │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Requirements

- **Python 3.11+**
- **[Ollama](https://ollama.ai)** — running locally at `http://localhost:11434`
- **FFmpeg** — for video compositing and export (optional but recommended)
- **GPU** — NVIDIA CUDA or AMD ROCm recommended for diffusion backends
- **PyQt6** — the GUI framework

---

## Quick Start

### Linux / macOS
```bash
git clone <repo>
cd PersonaCore-2
chmod +x setup.sh
./setup.sh
source .venv/bin/activate
python main.py
```

### Windows
```powershell
git clone <repo>
cd PersonaCore-2
.\setup.ps1
.\.venv\Scripts\Activate.ps1
python main.py
```

---

## Architecture

### Module Map

```
personacore/
├── main.py                  # Entry point
├── ai/
│   ├── ollama_client.py     # Raw Ollama REST API wrapper (streaming)
│   ├── model_manager.py     # Model list + selection management
│   ├── prompt_enricher.py   # Prompt expansion via Ollama
│   └── personas.py          # Director personas (system prompts + presets)
├── video/
│   ├── base_generator.py    # Abstract generator interface
│   ├── registry.py          # Backend registry (pluggable)
│   ├── demo_generator.py    # OpenCV+NumPy demo (no model needed)
│   ├── zeroscope_generator.py   # Zeroscope v2 via diffusers
│   ├── animatediff_generator.py # AnimateDiff via diffusers
│   └── ffmpeg_pipeline.py   # FFmpeg compositing + export
├── gui/
│   ├── main_window.py       # Main window orchestrator
│   ├── theme.py             # Dark cinematic theme + stylesheet
│   ├── animations.py        # QPropertyAnimation helpers
│   ├── widgets/
│   │   ├── title_bar.py     # Custom frameless title bar
│   │   ├── sidebar.py       # Left panel (projects, models, history)
│   │   ├── prompt_studio.py # Center (raw input + enriched output)
│   │   ├── step_tracker.py  # Pipeline progress tracker
│   │   ├── settings_panel.py # Right panel (params, export)
│   │   ├── video_preview.py # Embedded video player
│   │   └── log_console.py   # Color-coded live console
│   └── components/
│       ├── glass_panel.py   # Frosted-glass panel widget
│       ├── animated_button.py # GlowButton with hover animations
│       ├── gradient_border.py # Animated rotating gradient border
│       └── stat_badge.py    # Status bar stat chips
├── workers/
│   ├── enrichment_worker.py # QThread for Ollama streaming
│   ├── generation_worker.py # QThread for video generation
│   └── model_refresh_worker.py # QThread for model list refresh
├── config/
│   └── settings.py          # Persistent JSON settings (~/.personacore2/)
├── project/
│   └── project_manager.py   # Project save/load/history
├── export/
│   └── exporter.py          # Format conversion (MP4, GIF, WebM)
└── logging_module/
    └── logger.py            # Structured logger → Qt signals → UI console
```

### Design Principles

**Pluggable video backend**: Every generator implements `BaseVideoGenerator` from `video/base_generator.py`. New backends register in `video/registry.py` and are immediately available in the UI without any GUI changes.

**Thread safety**: All Ollama calls and video generation run in `QThread` workers. The main thread is never blocked. Workers communicate via Qt signals.

**Director personas**: Each persona bundles a system prompt (the AI's voice) with style preset parameters. Switching persona changes both the LLM behavior and the video generation defaults.

**Persistent projects**: Projects store the full pipeline state — raw prompt, enriched prompt, settings snapshot, and output paths. They survive restarts and can be exported as zip bundles.

---

## Video Backends

| Backend | Requirements | Notes |
|---------|-------------|-------|
| **Demo** | OpenCV, NumPy | No model — generates animated test visuals |
| **Zeroscope v2** | `pip install -e ".[diffusers]"` + GPU | `cerspense/zeroscope_v2_576w` |
| **AnimateDiff** | `pip install -e ".[diffusers]"` + GPU | `guoyww/animatediff-motion-adapter-v1-5-2` |

To add a custom backend:
```python
# my_backend.py
from personacore.video.base_generator import BaseVideoGenerator, GenerationParams, GenerationResult

class MyGenerator(BaseVideoGenerator):
    name = "My Custom Backend"
    
    def is_available(self) -> bool: ...
    def generate(self, params, output_dir, on_progress=None, is_cancelled=None) -> GenerationResult: ...

# Register it:
from personacore.video.registry import get_registry
get_registry().register("my_backend", MyGenerator)
```

---

## Director Personas

Built-in personas:

| ID | Name | Style |
|----|------|-------|
| `director` | Cinematic Director | Epic, photorealistic cinema |
| `anime` | Anime Auteur | Japanese animation style |
| `documentary` | Documentary Filmmaker | Raw, authentic vérité |
| `neon_noir` | Neon Noir Visionary | Cyberpunk, rain, neon |
| `abstract` | Abstract Artist | Generative, non-representational |

Custom personas are stored in `~/.personacore2/personas/` as JSON.

---

## Configuration

Settings persist in `~/.personacore2/settings.json` (Windows: `%LOCALAPPDATA%\PersonaCore\PersonaCore2\settings.json`).

Key settings:
```json
{
  "ollama": {
    "base_url": "http://localhost:11434",
    "default_model": "llama3.2"
  },
  "video": {
    "backend": "demo",
    "resolution": "512x512",
    "fps": 8,
    "duration_seconds": 3
  }
}
```

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Escape` | Cancel current operation |
| `Ctrl+N` | New project (planned) |
| `Ctrl+S` | Save project (planned) |

---

## License

MIT
