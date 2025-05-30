# ImageBreak CLI Help

This document provides comprehensive help for the ImageBreak command-line interface.

## Main Command

```bash
imagebreak --help
```

```
Usage: imagebreak [OPTIONS] COMMAND [ARGS]...

  ImageBreak: AI Safety Testing Framework

  A comprehensive framework for testing AI model safety and content
  moderation systems. Supports boundary testing, prompt alteration, cyclic
  generation with quality assessment, and integration with multiple AI models
  including OpenAI, Gemini, and HuggingFace.

Options:
  -c, --config PATH     Configuration file path
  -o, --output-dir PATH Output directory
  -v, --verbose         Enable verbose logging
  --env-file PATH       Environment file path (.env)
  --help                Show this message and exit.

Commands:
  alter-prompts     Generate altered versions of prompts to test filter...
  config-info       Display current configuration information.
  full-test         Run a complete end-to-end safety test pipeline.
  generate-prompts  Generate boundary-testing prompts that challenge...
  test-images       Test image generation with advanced cyclic quality...
  web-ui            Launch the Streamlit web UI for interactive...
```

## Commands

### 0. web-ui (Recommended Starting Point)

Launch the interactive Streamlit web interface for easy configuration and testing.

```bash
imagebreak web-ui [OPTIONS]
```

**Options:**
- `--host TEXT`: Host to bind the server to (default: localhost)
- `--port INTEGER`: Port to run the server on (default: 8501)
- `--browser / --no-browser`: Automatically open browser (default: True)
- `--theme [light|dark]`: UI theme
- `--headless`: Run in headless mode

**Examples:**

```bash
# Basic launch (opens browser automatically)
imagebreak web-ui

# Custom host and port
imagebreak web-ui --host 0.0.0.0 --port 8080

# Server mode (no browser, headless)
imagebreak web-ui --headless --no-browser --port 8502

# Dark theme
imagebreak web-ui --theme dark

# Load custom environment file
imagebreak --env-file production.env web-ui

# With verbose logging
imagebreak --verbose web-ui
```

**Features Available in Web UI:**
- 📊 **Configuration Dashboard**: Set API keys, models, and system instructions
- 🧪 **Interactive Testing**: Run tests with real-time progress tracking
- 📈 **Results Visualization**: View detailed metrics and generated images
- 💾 **Export Options**: Download results as JSON/CSV
- 🔄 **Cyclic Generation**: Configure quality assessment settings
- 🎨 **System Instructions**: Customize AI behavior through UI

### 1. config-info

Display current configuration and API key status.

```bash
imagebreak config-info
```

**Example Output:**
```
🔧 ImageBreak Configuration:
   📁 Output directory: ./results
   📝 Logging: True (level: INFO)
   🔄 Cyclic generation: True
   🎯 Max attempts: 3
   ⭐ Quality threshold: 0.7
   ☁️  AWS moderation: False

🔑 API Keys:
   OpenAI: ✅ Set
   Google: ❌ Not set
   HuggingFace: ✅ Set (optional)

🤖 Default Models:
   Text: openai
   Image: openai
```

### 2. generate-prompts

Generate boundary-testing prompts that challenge ethical guidelines.

```bash
imagebreak generate-prompts [OPTIONS]
```

**Options:**
- `-p, --policies PATH` (required): Path to policies/guidelines text file
- `-o, --output PATH` (required): Output JSON file for generated prompts
- `-n, --num-prompts INTEGER`: Number of prompts to generate (default: 10)
- `-t, --topics TEXT`: Specific topics to focus on (can be used multiple times)
- `-m, --model [openai|gemini]`: Model to use for prompt generation (default: openai)
- `--system-instruction TEXT`: Custom system instruction for boundary prompt generation

**Examples:**

```bash
# Basic usage
imagebreak generate-prompts \
  --policies content_policy.txt \
  --output prompts.json \
  --num-prompts 5

# With specific topics
imagebreak generate-prompts \
  --policies policy.txt \
  --output prompts.json \
  --topics "violence" \
  --topics "misinformation" \
  --model gemini

# With custom system instruction
imagebreak generate-prompts \
  --policies policy.txt \
  --output prompts.json \
  --system-instruction "You are a specialized AI safety researcher focusing on edge cases..."
```

### 3. alter-prompts

Generate altered versions of prompts to test filter evasion.

```bash
imagebreak alter-prompts [OPTIONS]
```

**Options:**
- `-p, --prompts PATH` (required): Path to JSON file containing prompts
- `-o, --output PATH`: Output JSON file for altered prompts (auto-generated if not specified)
- `-m, --model [openai|gemini]`: Model to use for prompt alteration (default: openai)
- `--system-instruction TEXT`: Custom system instruction for prompt alteration

**Examples:**

```bash
# Basic usage
imagebreak alter-prompts \
  --prompts original_prompts.json \
  --output altered_prompts.json

# Using Gemini model
imagebreak alter-prompts \
  --prompts prompts.json \
  --model gemini

# Auto-generated output filename (adds "_altered" suffix)
imagebreak alter-prompts --prompts prompts.json
```

### 4. test-images

Test image generation with advanced cyclic quality assessment.

```bash
imagebreak test-images [OPTIONS]
```

**Options:**
- `-p, --prompts PATH` (required): Path to JSON file containing prompts
- `--image-model [openai]`: Model to use for image generation (default: openai)
- `--text-model [openai|gemini]`: Model to use for text generation and prompt refinement (default: openai)
- `--use-cyclic / --no-use-cyclic`: Use cyclic generation with quality assessment (default: enabled)
- `--max-attempts INTEGER`: Maximum retry attempts for cyclic generation (default: 3)
- `--quality-threshold FLOAT`: Quality threshold for accepting generated images 0.0-1.0 (default: 0.7)
- `--save-images / --no-save-images`: Save generated images locally (default: enabled)
- `--output-folder PATH`: Folder to save generated images
- `--use-altered / --no-use-altered`: Use altered prompts when available (default: enabled)
- `--hf-model TEXT`: HuggingFace model for image analysis (default: Salesforce/blip2-opt-2.7b)

**Examples:**

```bash
# Basic cyclic generation
imagebreak test-images \
  --prompts altered_prompts.json \
  --use-cyclic \
  --max-attempts 5 \
  --quality-threshold 0.8

# Custom HuggingFace model
imagebreak test-images \
  --prompts prompts.json \
  --hf-model "Salesforce/blip2-flan-t5-xl" \
  --quality-threshold 0.6

# Legacy mode (no cyclic generation)
imagebreak test-images \
  --prompts prompts.json \
  --no-use-cyclic

# Custom output folder
imagebreak test-images \
  --prompts prompts.json \
  --output-folder ./my_images \
  --use-cyclic
```

### 5. full-test

Run a complete end-to-end safety test pipeline.

```bash
imagebreak full-test [OPTIONS]
```

**Options:**
- `-p, --policies PATH` (required): Path to policies/guidelines text file
- `-n, --num-prompts INTEGER`: Number of prompts to generate (default: 5)
- `--image-model [openai]`: Model for image generation (default: openai)
- `--text-model [openai|gemini]`: Model for text generation (default: openai)
- `--use-cyclic / --no-use-cyclic`: Use cyclic generation with quality assessment (default: enabled)
- `--quality-threshold FLOAT`: Quality threshold for cyclic generation (default: 0.7)

**Examples:**

```bash
# Complete pipeline with default settings
imagebreak full-test \
  --policies content_policy.txt

# Large test with high quality threshold
imagebreak full-test \
  --policies policy.txt \
  --num-prompts 10 \
  --quality-threshold 0.9 \
  --use-cyclic

# Using Gemini for text operations
imagebreak full-test \
  --policies policy.txt \
  --text-model gemini \
  --image-model openai
```

## Global Options

These options can be used with any command:

### Environment File Loading
```bash
imagebreak --env-file custom.env [COMMAND]
```

Load configuration from a custom .env file instead of the default.

### Verbose Logging
```bash
imagebreak --verbose [COMMAND]
```

Enable detailed logging for debugging and monitoring.

### Custom Output Directory
```bash
imagebreak --output-dir ./custom_results [COMMAND]
```

Set a custom directory for all output files and images.

### Configuration File
```bash
imagebreak --config config.json [COMMAND]
```

Load settings from a JSON configuration file.

## Complete Example Workflow

```bash
# 1. Check configuration
imagebreak config-info

# 2. Generate boundary prompts
imagebreak generate-prompts \
  --policies content_policy.txt \
  --output boundary_prompts.json \
  --num-prompts 5 \
  --topics "violence,explicit content"

# 3. Create altered versions
imagebreak alter-prompts \
  --prompts boundary_prompts.json \
  --output altered_prompts.json

# 4. Test with cyclic generation
imagebreak test-images \
  --prompts altered_prompts.json \
  --use-cyclic \
  --max-attempts 3 \
  --quality-threshold 0.7 \
  --save-images

# OR: Run everything in one command
imagebreak full-test \
  --policies content_policy.txt \
  --num-prompts 5 \
  --use-cyclic \
  --quality-threshold 0.7
```

## Error Handling

The CLI provides helpful error messages:

- **Missing API Keys**: "❌ OpenAI API key not found. Set OPENAI_API_KEY environment variable."
- **Invalid Files**: File not found errors with clear paths
- **Model Errors**: Detailed error messages for model failures
- **Configuration Issues**: Validation errors with specific fix suggestions

## Output Files

The CLI generates several types of output files:

### Prompt Files (JSON)
```json
[
  {
    "original_prompt": "Generated prompt text...",
    "generation_method": "boundary_testing",
    "topics": ["violence"],
    "timestamp": "2024-01-01T12:00:00"
  }
]
```

### Altered Prompt Files (JSON)
```json
[
  {
    "original_prompt": "Original text...",
    "altered_prompt": "Altered text...",
    "generation_method": "boundary_testing",
    "alteration_method": "filter_evasion",
    "timestamp": "2024-01-01T12:00:00"
  }
]
```

### Test Results (JSON)
```json
[
  {
    "original_prompt": "Prompt text...",
    "altered_prompt": "Altered text...",
    "success": true,
    "total_attempts": 2,
    "final_quality_score": 0.85,
    "exceeded_max_attempts": false,
    "image_path": "./results/images/image_abc123.png",
    "attempts": [
      {
        "attempt_number": 1,
        "prompt_used": "First prompt version...",
        "quality_score": 0.65,
        "success": false
      },
      {
        "attempt_number": 2,
        "prompt_used": "Refined prompt version...",
        "quality_score": 0.85,
        "success": true
      }
    ]
  }
]
``` 