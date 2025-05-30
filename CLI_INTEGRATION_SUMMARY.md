# ImageBreak CLI Integration Summary

## Overview

The ImageBreak CLI has been successfully enhanced to integrate all new features including:

✅ **Configurable System Instructions** - All AI behaviors customizable via environment variables and CLI arguments
✅ **Cyclic Image Generation** - Quality-based retry logic with HuggingFace image analysis
✅ **Optional AWS Integration** - AWS moderation is now optional, not required
✅ **HuggingFace Integration** - Uncensored image analysis using BLIP-2 and other vision models
✅ **Streamlit Web UI Integration** - Launch interactive web interface directly from CLI
✅ **Enhanced Error Handling** - Clear error messages and help guidance
✅ **Modular Commands** - Separate commands for each pipeline stage

## CLI Commands

### 0. Web UI Integration

```bash
# Launch interactive web interface (Recommended for beginners)
imagebreak web-ui

# Custom configuration
imagebreak web-ui --host 0.0.0.0 --port 8080 --theme dark

# Server mode (headless)
imagebreak web-ui --headless --no-browser

# With environment file
imagebreak --env-file production.env web-ui
```

### 1. Configuration Management

```bash
# Check current configuration and API status
imagebreak config-info

# Use custom environment file
imagebreak --env-file production.env [command]

# Enable verbose logging
imagebreak --verbose [command]
```

### 2. Prompt Generation

```bash
# Generate boundary-testing prompts
imagebreak generate-prompts \
  --policies content_policy.txt \
  --output prompts.json \
  --num-prompts 10 \
  --topics "violence,misinformation" \
  --model openai

# With custom system instruction
imagebreak generate-prompts \
  --policies policy.txt \
  --output prompts.json \
  --system-instruction "Custom AI researcher instruction..."
```

### 3. Prompt Alteration

```bash
# Create filter-evasion variants
imagebreak alter-prompts \
  --prompts prompts.json \
  --output altered_prompts.json \
  --model gemini

# Auto-generate output filename
imagebreak alter-prompts --prompts prompts.json
```

### 4. Advanced Image Generation

```bash
# Cyclic generation with quality assessment
imagebreak test-images \
  --prompts altered_prompts.json \
  --use-cyclic \
  --max-attempts 5 \
  --quality-threshold 0.8 \
  --hf-model "Salesforce/blip2-flan-t5-xl" \
  --save-images \
  --output-folder ./generated_images

# Legacy mode (no cyclic generation)
imagebreak test-images \
  --prompts prompts.json \
  --no-use-cyclic
```

### 5. Full Pipeline

```bash
# Complete end-to-end test
imagebreak full-test \
  --policies content_policy.txt \
  --num-prompts 5 \
  --use-cyclic \
  --quality-threshold 0.7 \
  --text-model openai \
  --image-model openai
```

## New Features Integration

### Configurable System Instructions

All system instructions are now configurable:

- **Environment Variables**: Set via `BOUNDARY_PROMPT_SYSTEM_INSTRUCTION`, `PROMPT_ALTERATION_SYSTEM_INSTRUCTION`, `IMAGE_ANALYSIS_SYSTEM_INSTRUCTION`
- **CLI Arguments**: Override with `--system-instruction` parameter
- **Dynamic Configuration**: Instructions can be customized per command

### Cyclic Generation

The CLI fully supports the new cyclic generation system:

- **Quality Thresholds**: Set via `--quality-threshold` (0.0-1.0)
- **Retry Limits**: Configure with `--max-attempts`
- **HuggingFace Models**: Choose analysis model with `--hf-model`
- **Real-time Feedback**: Progress tracking and quality scores
- **Detailed Results**: Attempt-by-attempt tracking in JSON output

### HuggingFace Integration

Vision-language models are integrated for uncensored image analysis:

- **Default Model**: `Salesforce/blip2-opt-2.7b`
- **Custom Models**: Use `--hf-model` for alternatives like `Salesforce/blip2-flan-t5-xl`
- **Quality Assessment**: Automatic quality scoring based on image descriptions
- **Device Support**: Automatic CPU/GPU detection

### Optional AWS

AWS dependencies are now optional:

- **Environment Control**: Set `USE_AWS_MODERATION=false` to disable
- **CLI Configuration**: Automatically detected and reported in `config-info`
- **Graceful Fallback**: Framework operates without AWS credentials

## Error Handling

The CLI provides helpful error messages and guidance:

### API Key Issues
```
❌ Configuration Error: At least one API key (OpenAI or Google) must be provided
💡 Please set your API keys in environment variables or .env file:
   - OPENAI_API_KEY=your_openai_key
   - GOOGLE_API_KEY=your_google_key
```

### HuggingFace Issues
```
⚠️ HuggingFace analyzer failed, using basic quality assessment: [error details]
```

### Model Issues
```
❌ OpenAI API key not found for image generation.
❌ Google API key not found for text generation.
```

## Output Files

The CLI generates structured JSON output files:

### Prompt Files
```json
[
  {
    "original_prompt": "Generated boundary-testing prompt...",
    "generation_method": "boundary_testing",
    "topics": ["violence"],
    "timestamp": "2024-01-01T12:00:00"
  }
]
```

### Altered Prompt Files
```json
[
  {
    "original_prompt": "Original prompt...",
    "altered_prompt": "Filter-evasion variant...",
    "generation_method": "boundary_testing",
    "alteration_method": "filter_evasion",
    "timestamp": "2024-01-01T12:00:00"
  }
]
```

### Cyclic Generation Results
```json
[
  {
    "original_prompt": "Test prompt...",
    "altered_prompt": "Altered version...",
    "success": true,
    "total_attempts": 2,
    "final_quality_score": 0.85,
    "exceeded_max_attempts": false,
    "image_path": "./results/images/image_abc123.png",
    "attempts": [
      {
        "attempt_number": 1,
        "prompt_used": "First attempt prompt...",
        "quality_score": 0.65,
        "success": false
      },
      {
        "attempt_number": 2,
        "prompt_used": "Refined prompt...",
        "quality_score": 0.85,
        "success": true
      }
    ]
  }
]
```

## Example Workflows

### Workflow 0: Web UI (Recommended for Beginners)
```bash
# Launch interactive web interface
imagebreak web-ui

# Or with custom settings
imagebreak --env-file .env web-ui --theme dark --port 8080
```
*Then use the web interface to configure API keys, run tests, and view results interactively.*

### Workflow 1: Quick Test
```bash
# Check configuration
imagebreak config-info

# Run full pipeline
imagebreak full-test --policies policy.txt --num-prompts 3
```

### Workflow 2: Advanced Testing
```bash
# Generate specific prompts
imagebreak generate-prompts \
  --policies policy.txt \
  --output boundary_prompts.json \
  --topics "violence,misinformation" \
  --num-prompts 5

# Create altered versions
imagebreak alter-prompts \
  --prompts boundary_prompts.json \
  --output altered_prompts.json

# Test with high-quality cyclic generation
imagebreak test-images \
  --prompts altered_prompts.json \
  --use-cyclic \
  --max-attempts 5 \
  --quality-threshold 0.9 \
  --hf-model "Salesforce/blip2-flan-t5-xl"
```

### Workflow 3: Custom Configuration
```bash
# Use custom environment and verbose logging
imagebreak --env-file production.env --verbose \
  generate-prompts \
  --policies custom_policy.txt \
  --output prompts.json \
  --system-instruction "Custom researcher instruction..."
```

## Help System

Comprehensive help is available at all levels:

```bash
# Main help
imagebreak --help

# Command-specific help
imagebreak web-ui --help
imagebreak generate-prompts --help
imagebreak alter-prompts --help
imagebreak test-images --help
imagebreak full-test --help
imagebreak config-info --help
```

## Installation

The CLI is automatically available after installation:

```bash
# Install in development mode
pip install -e .

# CLI becomes available
imagebreak --help
```

## Backwards Compatibility

The CLI maintains backwards compatibility while adding new features:

- **Legacy Mode**: Use `--no-use-cyclic` for traditional generation
- **Optional Parameters**: All new features have sensible defaults
- **Graceful Degradation**: Features work with minimal configuration

## Summary

The ImageBreak CLI now provides a comprehensive interface for all framework functionality:

1. **Complete Feature Coverage**: All new features accessible via CLI including web UI
2. **User-Friendly**: Clear help, error messages, and progress feedback
3. **Interactive Web Interface**: Streamlit UI directly accessible via CLI
4. **Flexible Configuration**: Environment variables, CLI arguments, and config files
5. **Detailed Output**: Structured JSON results with comprehensive metrics
6. **Production Ready**: Robust error handling and graceful degradation

The CLI successfully integrates all new features while maintaining ease of use and providing powerful functionality for AI safety research and testing. The new web-ui command makes the framework accessible to users who prefer graphical interfaces over command-line tools.