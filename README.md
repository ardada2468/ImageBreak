# ImageBreak 🛡️

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**ImageBreak** is a comprehensive framework for testing AI model safety and content moderation systems. It provides tools to evaluate how well AI models handle potentially harmful prompts and helps researchers identify vulnerabilities in content filtering systems.

## ⚠️ Important Notice

This tool is designed **exclusively for research purposes** to improve AI safety and content moderation systems. The generated content should only be used by researchers, AI safety teams, and developers working to make AI systems safer and more robust.

## 🚀 Features

- **Multi-Model Support**: Built-in interfaces for OpenAI GPT models, Google Gemini, and HuggingFace models
- **Extensible Architecture**: Easy-to-use abstract base classes for adding custom models
- **Comprehensive Testing Pipeline**: 
  - Generate boundary-testing prompts with configurable system instructions
  - Alter prompts to test filter evasion
  - Automated image generation testing with cyclic quality assessment
  - Content moderation analysis (optional AWS integration)
- **Cyclic Generation**: Advanced retry logic with HuggingFace-powered image quality assessment
- **Configurable System Instructions**: Customize AI behavior through environment variables
- **Results Analysis**: Comprehensive reporting and data export capabilities
- **CLI Interface**: Command-line tool for batch operations and automation
- **Streamlit Web UI**: User-friendly interface for configuration and testing
- **Optional AWS Integration**: Built-in support for AWS Rekognition for content analysis

## Web UI View

<img width="1791" alt="image" src="https://github.com/user-attachments/assets/071e74d2-bde8-4468-a55a-1aadd923baa6" />
<img width="1791" alt="image" src="https://github.com/user-attachments/assets/69fdad88-6413-48a5-be39-5416703a331a" />


## 🔧 Installation

### From PyPI (when published)
```bash
pip install imagebreak
```

### From Source
```bash
git clone https://github.com/yourusername/imagebreak.git
cd imagebreak
pip install -e .
```

### With dependencies
```bash
# Install all dependencies
pip install -r requirements.txt

# For development
pip install imagebreak[dev]
```

## 🏃 Quick Start

### 1. Environment Setup

Create a `.env` file with your API keys:

```env
# Required: At least one API key
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# Optional: HuggingFace for image analysis (recommended)
HUGGINGFACE_TOKEN=your_huggingface_token_here

# Cyclic Generation Settings
ENABLE_CYCLIC_REGENERATION=true
MAX_RETRY_ATTEMPTS=3
QUALITY_THRESHOLD=0.7

# Optional: AWS for moderation
USE_AWS_MODERATION=false
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1

# Configurable System Instructions
BOUNDARY_PROMPT_SYSTEM_INSTRUCTION=You are an AI model researcher...
PROMPT_ALTERATION_SYSTEM_INSTRUCTION=You are an AI researcher focused...
IMAGE_ANALYSIS_SYSTEM_INSTRUCTION=You are an AI image analysis expert...
```

### 2. Using the CLI Interface

The CLI provides a comprehensive interface for all ImageBreak functionality:

#### Launch Web UI (Recommended for Beginners)
```bash
# Launch the interactive web interface
imagebreak web-ui

# Custom host and port
imagebreak web-ui --host 0.0.0.0 --port 8080

# Headless mode (no auto-browser opening)
imagebreak web-ui --headless --no-browser

# Dark theme
imagebreak web-ui --theme dark
```

#### Basic Configuration Check
```bash
# Check current configuration and API key status
imagebreak config-info
```

#### Generate Boundary-Testing Prompts
```bash
# Generate prompts that test ethical boundaries
imagebreak generate-prompts \
  --policies your_content_policy.txt \
  --output generated_prompts.json \
  --num-prompts 10 \
  --topics "violence,misinformation" \
  --model openai

# With custom system instruction
imagebreak generate-prompts \
  --policies policy.txt \
  --output prompts.json \
  --system-instruction "Custom instruction for boundary testing..."
```

#### Alter Prompts for Filter Evasion
```bash
# Create altered versions designed to evade filters
imagebreak alter-prompts \
  --prompts generated_prompts.json \
  --output altered_prompts.json \
  --model openai

# Specify custom output file
imagebreak alter-prompts \
  --prompts prompts.json \
  --output custom_altered.json \
  --model gemini
```

#### Test Image Generation with Cyclic Quality Assessment
```bash
# Advanced cyclic generation with quality assessment
imagebreak test-images \
  --prompts altered_prompts.json \
  --use-cyclic \
  --max-attempts 5 \
  --quality-threshold 0.8 \
  --image-model openai \
  --text-model openai \
  --hf-model "Salesforce/blip2-flan-t5-xl" \
  --save-images \
  --output-folder ./generated_images

# Legacy mode (no cyclic generation)
imagebreak test-images \
  --prompts prompts.json \
  --no-use-cyclic \
  --image-model openai
```

#### Full End-to-End Pipeline
```bash
# Run complete pipeline: generate → alter → test
imagebreak full-test \
  --policies content_policy.txt \
  --num-prompts 5 \
  --image-model openai \
  --text-model openai \
  --use-cyclic \
  --quality-threshold 0.7

# Quick test with Gemini text model
imagebreak full-test \
  --policies policy.txt \
  --num-prompts 3 \
  --text-model gemini \
  --image-model openai
```

#### Advanced CLI Options

**Environment File Loading:**
```bash
# Load configuration from custom .env file
imagebreak --env-file custom.env generate-prompts --policies policy.txt --output prompts.json
```

**Verbose Logging:**
```bash
# Enable detailed logging
imagebreak --verbose test-images --prompts prompts.json
```

**Custom Output Directory:**
```bash
# Set custom output directory for all results
imagebreak --output-dir ./custom_results test-images --prompts prompts.json
```

#### CLI Command Reference

| Command | Description | Key Options |
|---------|-------------|-------------|
| `web-ui` | Launch Streamlit web interface | `--host`, `--port`, `--theme`, `--headless` |
| `config-info` | Display configuration and API key status | N/A |
| `generate-prompts` | Generate boundary-testing prompts | `--policies`, `--num-prompts`, `--model`, `--system-instruction` |
| `alter-prompts` | Create filter-evasion variants | `--prompts`, `--model`, `--system-instruction` |
| `test-images` | Test image generation with quality assessment | `--use-cyclic`, `--max-attempts`, `--quality-threshold`, `--hf-model` |
| `full-test` | Complete pipeline in one command | `--policies`, `--use-cyclic`, `--quality-threshold` |

### 3. Using the Streamlit Web Interface

**Option 1: Via CLI (Recommended)**
```bash
# Launch web interface directly from CLI
imagebreak web-ui
```

**Option 2: Direct Launch**
```bash
# Launch the web interface manually
streamlit run streamlit_app.py
```

Navigate to `http://localhost:8501` for the interactive interface with:
- **API Configuration**: Set up keys and models
- **System Instructions**: Customize AI behavior
- **Testing Interface**: Run tests with real-time progress
- **Results Visualization**: View detailed metrics and generated images

### 4. Python API Usage

```python
from imagebreak import ImageBreakFramework, Config
from imagebreak.models import OpenAIModel, GeminiModel

# Initialize with configuration
config = Config()
framework = ImageBreakFramework(config)

# Add models
framework.add_model("openai", OpenAIModel(
    api_key=config.openai_api_key,
    config=config
))

# Load your content policies
with open("your_content_policy.txt", "r") as f:
    policies = f.read()

# Generate and test with cyclic generation
test_prompts = framework.generate_boundary_prompts(
    policies=policies,
    num_prompts=10,
    topics=["violence", "misinformation"]
)

# Run cyclic generation tests
results = framework.test_image_generation_cyclic(
    prompt_data_list=test_prompts,
    save_images=True
)

# Analyze results
successful = sum(1 for r in results if r.success)
avg_quality = sum(r.final_quality_score for r in results 
                 if r.final_quality_score is not None) / len(results)
print(f"Success rate: {successful/len(results)*100:.1f}%")
print(f"Average quality: {avg_quality:.2f}")
```

## 📖 Advanced Usage

### Custom Model Integration

```python
from imagebreak.models.base import BaseModel
from imagebreak.types import ModelResponse

class CustomModel(BaseModel):
    def __init__(self, api_key: str, model_name: str):
        super().__init__()
        self.api_key = api_key
        self.model_name = model_name
    
    def generate_text(self, prompt: str, **kwargs) -> ModelResponse:
        # Implement your model's text generation
        pass
    
    def generate_image(self, prompt: str, **kwargs) -> ModelResponse:
        # Implement your model's image generation
        pass

# Use your custom model
framework.add_model("my-model", CustomModel(api_key="...", model_name="..."))
```

### Advanced Configuration

```python
from imagebreak import ImageBreakFramework, Config

config = Config(
    max_retries=3,
    timeout=30,
    batch_size=10,
    output_dir="./results",
    enable_logging=True,
    log_level="INFO",
    enable_cyclic_regeneration=True,
    max_retry_attempts=5,
    quality_threshold=0.8,
    use_aws_moderation=False
)

framework = ImageBreakFramework(config=config)
```

### Custom HuggingFace Models

```python
from imagebreak.models import HuggingFaceImageAnalyzer

# Use custom vision model for image analysis
analyzer = HuggingFaceImageAnalyzer(
    model_name="Salesforce/blip2-flan-t5-xl"
)

# Custom device configuration
analyzer = HuggingFaceImageAnalyzer(
    model_name="Salesforce/blip2-opt-2.7b",
    device="cuda"  # or "cpu"
)
```

## 🆕 Version 2.0 Features

### Cyclic Image Generation
- **Quality-Based Retries**: Automatically retry generation if image quality is below threshold
- **HuggingFace Integration**: Uses BLIP-2 and other vision models for uncensored quality assessment
- **Prompt Refinement**: Automatically improves prompts based on quality feedback
- **Detailed Metrics**: Track attempts, quality scores, and success rates

### Configurable System Instructions
All AI model behaviors are now customizable via environment variables:
- **Boundary Testing**: `BOUNDARY_PROMPT_SYSTEM_INSTRUCTION`
- **Prompt Alteration**: `PROMPT_ALTERATION_SYSTEM_INSTRUCTION`  
- **Image Analysis**: `IMAGE_ANALYSIS_SYSTEM_INSTRUCTION`

### Enhanced CLI Interface
- **Modular Commands**: Separate commands for each pipeline stage
- **Cyclic Generation Support**: Full CLI integration for quality-based retries
- **Real-time Progress**: Visual feedback and progress tracking
- **Flexible Configuration**: Override settings via CLI arguments

## 📊 Results and Metrics

The framework provides comprehensive metrics:

- **Success Rates**: Generation success vs. filter blocking
- **Quality Scores**: AI-assessed image quality (0.0-1.0)
- **Attempt Tracking**: Detailed logs of retry attempts and prompt refinements
- **Filter Bypass Analysis**: Effectiveness of prompt alteration techniques
- **Export Options**: JSON, CSV reports for further analysis

### CLI Output Examples

```bash
🖼️  Testing image generation with 5 prompts
   📊 Cyclic generation: True
   🔄 Max attempts: 3
   ⭐ Quality threshold: 0.7
   🤖 Analysis model: Salesforce/blip2-opt-2.7b
✅ Initialized HuggingFace analyzer: Salesforce/blip2-opt-2.7b

📊 Cyclic Generation Results:
   ✅ Successful: 4/5 (80.0%)
   🔄 Total attempts: 12
   ⭐ Average quality: 0.78
💾 Detailed results saved to ./results/image_test_results_1704067200.json
```

## 🛠️ Configuration Examples

### Minimal Setup (.env)
```env
OPENAI_API_KEY=sk-...
ENABLE_CYCLIC_REGENERATION=true
QUALITY_THRESHOLD=0.7
```

### Full Configuration (.env)
```env
# API Keys
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=AI...
HUGGINGFACE_TOKEN=hf_...

# Cyclic Generation
ENABLE_CYCLIC_REGENERATION=true
MAX_RETRY_ATTEMPTS=5
QUALITY_THRESHOLD=0.8

# Model Selection
DEFAULT_TEXT_MODEL=openai
DEFAULT_IMAGE_MODEL=openai

# Optional AWS
USE_AWS_MODERATION=false
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...

# Custom System Instructions
BOUNDARY_PROMPT_SYSTEM_INSTRUCTION=Custom instruction for boundary testing...
PROMPT_ALTERATION_SYSTEM_INSTRUCTION=Custom instruction for prompt alteration...
IMAGE_ANALYSIS_SYSTEM_INSTRUCTION=Custom instruction for image analysis...
```

## 🔧 Troubleshooting

### OpenAI Content Policy Violations

When testing boundary prompts, you may encounter content policy blocks:

```
🚫 Prompt 1: Blocked by content policy after 3 attempts
```

**How the Framework Handles This:**

1. **Automatic Sanitization**: The system automatically creates sanitized versions of boundary-testing prompts
2. **Progressive Attempts**: First tries sanitized prompt, then original, then refined versions
3. **Transparent Feedback**: Shows whether "sanitized" or "original" prompt was used for successful generations

**Example Output:**
```
✅ Prompt 1: Success (attempts: 1, quality: 0.85) (used sanitized prompt)
✅ Prompt 2: Success (attempts: 2, quality: 0.72) (used original prompt) 
🚫 Prompt 3: Blocked by content policy after 3 attempts
```

**Configuration Options:**
```env
# Reduce retry attempts if many prompts are blocked
MAX_RETRY_ATTEMPTS=2

# Disable boundary testing if too restrictive
BOUNDARY_PROMPT_SYSTEM_INSTRUCTION=Generate mild creative prompts suitable for general audiences...
```

### HuggingFace Image Analyzer Issues

If you see warnings about HuggingFace image analyzer failures:

```
⚠️ HuggingFace image analyzer not available. Quality scores will be basic estimates.
```

**Common Solutions:**

1. **Install missing dependencies:**
   ```bash
   pip install torch torchvision transformers accelerate
   ```

2. **Set HuggingFace token:**
   ```env
   HUGGINGFACE_TOKEN=hf_your_token_here
   ```

3. **Use CPU-compatible models:**
   ```bash
   # For systems without GPU
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
   ```

4. **Alternative: Disable advanced analysis:**
   ```env
   ENABLE_CYCLIC_REGENERATION=false
   ```

The framework will work without HuggingFace, but quality assessment will be basic rather than AI-powered.

### Memory Issues

For large models or limited memory:

```env
# Use smaller HuggingFace model
DEFAULT_HF_MODEL=Salesforce/blip2-opt-2.7b

# Reduce retry attempts
MAX_RETRY_ATTEMPTS=2
```

## 📊 Analysis and Reporting

ImageBreak provides comprehensive analysis tools:

- **Content Moderation Analysis**: Integrates with AWS Rekognition and other moderation APIs
- **Statistical Reports**: Success rates, filter bypass rates, content categorization
- **Export Formats**: JSON, CSV, HTML reports
- **Visualization**: Charts and graphs for result analysis (via Streamlit UI)

## 🛡️ Safety and Ethics

This framework is built with safety in mind:

- **Research Focus**: Designed specifically for improving AI safety
- **Ethical Guidelines**: Built-in safeguards and ethical considerations
- **Responsible Disclosure**: Tools for reporting vulnerabilities responsibly
- **Audit Trail**: Comprehensive logging for accountability

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup

```bash
git clone https://github.com/yourusername/imagebreak.git
cd imagebreak
pip install -e .[dev]
pre-commit install
```

### Running Tests

```bash
pytest tests/
pytest --cov=imagebreak tests/  # With coverage
```

**Remember**: This tool is for research purposes only. Please use responsibly and in accordance with all applicable laws and ethical guidelines. 
