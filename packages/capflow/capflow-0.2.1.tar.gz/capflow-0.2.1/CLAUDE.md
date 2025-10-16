# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**captionflow** is an image captioning library that combines three AI models in a verification pipeline:
- **Florence2**: Microsoft's vision-language model for detailed captions
- **WD14**: Danbooru-style tagging model (anime/illustration focus)
- **VLM**: Vision Language Model for verification and reconciliation

The key innovation is the **VLM verification layer** that resolves contradictions between Florence2 and WD14 by directly examining the image and converting tags to natural language.

## Python Environment

- **Python Version**: 3.12+ (specified in `pyproject.toml`)
- **Package Manager**: `uv` (recommended) or pip
- **Build System**: hatchling

## Development Commands

### Environment Setup
```bash
# Development environment with all dependencies
uv sync

# Or using pip
pip install -e "."
```

### Running Tests
```bash
# Run all tests (requires OPENAI_API_KEY in .env)
uv run python -m pytest

# Run a specific test file
uv run python -m pytest tests/test_florence2.py

# Run a specific test
uv run python -m pytest tests/test_florence2.py::TestFlorence2::test_generate_caption_basic

# Run with coverage
uv run python -m pytest --cov=captionflow --cov-report=html

# Run tests without VLM (no API key needed)
uv run python -m pytest tests/test_florence2.py tests/test_wd14.py

# Alternative: activate venv first
source .venv/bin/activate
pytest
```

**Note**: Tests use `python-dotenv` to load `.env` from the repository root. VLM tests require `OPENAI_API_KEY` to be set.

### Building and Publishing to PyPI
```bash
# Install build tools
uv sync

# Build distribution packages
uv run python -m build

# Check the built packages
uv run twine check dist/*

# Upload to TestPyPI (optional, for testing)
uv run twine upload --repository testpypi dist/*

# Upload to PyPI
uv run twine upload dist/*
```

**Authentication**: Configure PyPI credentials using one of these methods:
- API token (recommended): Set `TWINE_USERNAME=__token__` and `TWINE_PASSWORD=<your-token>`
- `.pypirc` file in home directory with credentials
- Interactive prompt during upload

**Version management**: Update version in `pyproject.toml` before building.

### API Keys

**Important**: The core library does NOT load `.env` files. API keys must be passed explicitly:

```python
import os
import captionflow as cf

# Pass API key from environment
vlm = cf.VLM(api_key=os.getenv("OPENAI_API_KEY"))
```

Tests use `python-dotenv` to load `.env` files from the repository root.

## Architecture

### Three-Stage Pipeline

The pipeline is designed to **reduce hallucinations** through cross-validation:

1. **WD14 Tags** (`src/captionflow/models/wd14.py`)
   - Generates high-confidence Danbooru-style tags
   - Tags like `1girl`, `solo` indicate subject count (high confidence = reliable)
   - Output: List of tags with confidence scores

2. **Florence2 Captions** (`src/captionflow/models/florence2.py`)
   - Generates natural language descriptions
   - Configured with conservative parameters to reduce hallucinations:
     - `num_beams=5` (more conservative beam search)
     - `repetition_penalty=1.2` (penalize repetition)
   - Output: Detailed text caption

3. **VLM Verification** (`src/captionflow/models/vlm.py`)
   - **Critical role**: Acts as a verification and reconciliation layer
   - Examines the image directly (not just text inputs)
   - Resolves contradictions:
     - If Florence2 says "a few people" but WD14 says `solo` (>0.9 confidence), VLM verifies by looking at the image
     - Converts WD14 tags to natural English (e.g., `1girl, solo` → "a single woman")
   - Output: Verified, natural language description optimized for image generation

### Key Design Decisions

1. **Conservative Florence2 parameters**: Reduces hallucinations at the caption generation stage
2. **High-confidence WD14 tags as ground truth**: Tags with >0.9 confidence are treated as reliable facts
3. **VLM as arbiter**: Makes final decisions based on direct visual observation
4. **Prompt optimization**: Output is formatted for AI image generators (Stable Diffusion, Midjourney, FLUX)

### Device Support

Cross-platform GPU support with automatic detection:
- **CUDA** (Linux/Windows): NVIDIA GPU, float16 precision
- **MPS** (macOS): Apple Silicon GPU, float32 precision (flash_attn not supported)
- **CPU**: Fallback mode

Device selection: `utils.device.get_optimal_device()`

## Model Details

### Florence2 (`src/captionflow/models/florence2.py`)
- Models: `base` (230M params, ~1GB VRAM) or `large` (770M params, ~3GB VRAM)
- Tasks: `caption`, `detailed_caption`, `more_detailed_caption`
- Uses lazy loading (model loaded on first inference)

### WD14 (`src/captionflow/models/wd14.py`)
- Models: `wd-eva02-large-tagger-v3` (default), `wd-vit-large-tagger-v3`
- Loaded via `timm` with HuggingFace Hub integration
- Tags CSV includes ratings, general tags, and character tags

### VLM (`src/capflow/models/vlm.py`)
- Default: OpenAI `gpt-5-mini`
- Supports OpenRouter for alternative models (Gemini, Claude, etc.)
- System prompt emphasizes factual accuracy and contradiction resolution
- **Async-first API**: Primary methods are async, with `_sync` variants available
- Sync methods work correctly even when called from async context (no "event loop already running" errors)

### EXIF Utilities (`src/capflow/utils/exif.py`)
- `extract_exif()`: Extract all EXIF metadata from image files
- `get_camera_info()`: Parse camera make, model, and lens information
- `get_capture_settings()`: Extract ISO, aperture, shutter speed, focal length
- `get_datetime()`: Get capture date/time in ISO 8601 format
- Handles various EXIF formats and edge cases gracefully

## Usage Examples

### Async (Recommended)

```python
import os
import capflow as cf

# Initialize (VLM requires API key)
florence2 = cf.Florence2()
wd14 = cf.WD14()
vlm = cf.VLM(api_key=os.getenv("OPENAI_API_KEY"))

# Generate
image_path = "image.jpg"
caption = florence2.generate_caption(image_path, task="more_detailed_caption")
tags = wd14.generate_tags(image_path)

# VLM is async
description = await vlm.generate_caption(
    image_path,
    context=f"Florence2: {caption}\nWD14 Tags: {', '.join(tags)}"
)

# Extract EXIF metadata
exif_data = cf.extract_exif(image_path)
camera_info = cf.get_camera_info(exif_data)  # {'make': 'Canon', 'model': '...', 'lens': '...'}
settings = cf.get_capture_settings(exif_data)  # {'iso': 800, 'aperture': 2.8, ...}
datetime = cf.get_datetime(exif_data)  # '2024-03-15T14:30:22'
```

### Synchronous

```python
import os
import capflow as cf

# Initialize
florence2 = cf.Florence2()
wd14 = cf.WD14()
vlm = cf.VLM(api_key=os.getenv("OPENAI_API_KEY"))

# All synchronous
image_path = "image.jpg"
caption = florence2.generate_caption(image_path, task="more_detailed_caption")
tags = wd14.generate_tags(image_path)

# Use _sync methods for VLM
description = vlm.generate_caption_sync(
    image_path,
    context=f"Florence2: {caption}\nWD14 Tags: {', '.join(tags)}"
)
```

## Important Notes

### VLM Async/Sync API

VLM provides both async and sync methods:

**Async methods (primary):**
- `await vlm.generate_caption(image, context=None, user_prompt=None)`
- `await vlm.generate_caption_with_tags(image, tags, user_prompt=None)`
- `await vlm.generate_tags(image)`
- `await vlm.refine_caption(image, draft_caption, refinement_prompt=None)`

**Sync methods (with `_sync` suffix):**
- `vlm.generate_caption_sync(image, context=None, user_prompt=None)`
- `vlm.generate_caption_with_tags_sync(image, tags, user_prompt=None)`
- `vlm.generate_tags_sync(image)`
- `vlm.refine_caption_sync(image, draft_caption, refinement_prompt=None)`

The `_sync` methods automatically detect if they're running in an async event loop and handle it correctly by running the async code in a new thread. This prevents "event loop already running" errors.

**Windows Ctrl+C Support:**

For proper KeyboardInterrupt handling on Windows, use the `run_async()` helper:

```python
import capflow as cf

async def main():
    vlm = cf.VLM(api_key="...")
    caption = await vlm.generate_caption("image.jpg")
    return caption

# Properly handles Ctrl+C on Windows
result = cf.run_async(main())
```

The helper sets `WindowsSelectorEventLoopPolicy` on Windows to ensure signals are handled correctly.

### Dependency Management
- Core library has minimal dependencies (torch, transformers, pillow, timm, pydantic-ai-slim)
- Development dependencies (`[dependency-groups.dev]`): pytest, pytest-asyncio, pytest-cov, python-dotenv, pyyaml, build, twine
- Use `uv sync` to install all dependencies including dev group
- Package manager: `uv` is recommended for lockfile support and faster installs

### API Key Management
- **Core library does NOT load `.env` files**
- API keys must be passed explicitly from application code
- Tests use `python-dotenv` to load `.env` from repository root
- VLM models accept API keys via constructor parameter: `cf.VLM(api_key="...")`
- This design keeps the library clean and lets applications control configuration

### Model Naming Convention
All models follow a simple naming pattern:
- `Florence2` (not Florence2Model, Florence2Tagger, etc.)
- `WD14` (not Wd14Tagger, WD14Model, etc.)
- `VLM` (not VisionLanguageModel, VLMTagger, etc.)
- `BaseModel` (abstract base class)

This reflects the package name **capflow** (caption generation, not tagging).

### Import Style
All code examples and tests use the pattern:
```python
import capflow as cf
# Then use cf.Florence2(), cf.WD14(), cf.VLM()
```

Models are exported in `src/capflow/__init__.py` via `from .models import VLM, WD14, Florence2`.

### Test Structure
Tests are in `tests/` directory with fixtures defined in `conftest.py`:
- `sample_image`: Path to test image (located in `tests/images/` directory)
- `openai_api_key`: Loaded from environment, skips test if not available
- Tests use `pytest.skip()` to gracefully handle missing dependencies
- Async tests use `@pytest.mark.asyncio` decorator

Test files follow naming convention:
- `test_<model>.py` for unit tests
- `test_<model>_sync.py` for sync method tests
- `test_integration.py` for pipeline tests

VLM tests require `OPENAI_API_KEY` environment variable. Run `uv run python -m pytest` to execute all tests.

### Git Workflow
- `.gitignore` excludes: generated outputs (`*.yaml`), model caches, API keys (`.env`), `__pycache__`, `.pytest_cache`
- Tests directory is NOT ignored (contrary to previous `.gitignore`)
- Commit messages include Claude Code attribution
