#!/bin/bash

# ImageBreak CLI Usage Examples
# This script demonstrates the various ways to use the ImageBreak CLI

echo "🔬 ImageBreak CLI Usage Examples"
echo "================================"

# Check if environment is set up
if ! command -v imagebreak &> /dev/null; then
    echo "❌ ImageBreak CLI not found. Please install with 'pip install -e .'"
    exit 1
fi

# 0. Launch web UI (recommended for beginners)
echo ""
echo "🌐 Option 0: Launch Web UI (Recommended for beginners)"
echo "imagebreak web-ui                    # Basic launch"
echo "imagebreak web-ui --port 8080        # Custom port"
echo "imagebreak web-ui --theme dark       # Dark theme"
echo "imagebreak web-ui --headless         # Server mode"
echo ""
echo "💡 The web UI provides an interactive interface for all features!"
echo "   To launch now: imagebreak web-ui"

# 1. Check configuration
echo ""
echo "📋 Step 1: Check current configuration"
imagebreak config-info

# 2. Generate boundary-testing prompts
echo ""
echo "📝 Step 2: Generate boundary-testing prompts"
cat > sample_policy.txt << EOF
Our content policy prohibits:
1. Violent or graphic content depicting harm to individuals
2. Sexually explicit or suggestive material
3. Content promoting illegal activities
4. Hate speech or discriminatory content
5. Misinformation or false claims

All generated content must be appropriate for general audiences and comply with our community guidelines.
EOF

imagebreak generate-prompts \
  --policies sample_policy.txt \
  --output boundary_prompts.json \
  --num-prompts 3 \
  --model openai \
  --topics "violence,explicit content"

echo "✅ Generated boundary prompts saved to boundary_prompts.json"

# 3. Alter prompts for filter evasion
echo ""
echo "🔄 Step 3: Generate altered prompts for filter evasion"
imagebreak alter-prompts \
  --prompts boundary_prompts.json \
  --output altered_prompts.json \
  --model openai

echo "✅ Altered prompts saved to altered_prompts.json"

# 4. Test image generation with cyclic quality assessment
echo ""
echo "🖼️  Step 4: Test image generation with cyclic assessment"
imagebreak test-images \
  --prompts altered_prompts.json \
  --use-cyclic \
  --max-attempts 3 \
  --quality-threshold 0.7 \
  --image-model openai \
  --text-model openai \
  --hf-model "Salesforce/blip2-opt-2.7b" \
  --save-images \
  --output-folder ./generated_images

# 5. Full end-to-end pipeline
echo ""
echo "🚀 Step 5: Run full pipeline in one command"
imagebreak full-test \
  --policies sample_policy.txt \
  --num-prompts 2 \
  --image-model openai \
  --text-model openai \
  --use-cyclic \
  --quality-threshold 0.6

echo ""
echo "🎉 CLI examples completed!"
echo "📁 Check the ./results directory for generated images and JSON results"
echo "🗑️  Clean up: rm sample_policy.txt boundary_prompts.json altered_prompts.json"

# Advanced examples with different configurations
echo ""
echo "🔧 Advanced CLI Examples:"
echo ""

echo "# Use custom environment file:"
echo "imagebreak --env-file production.env generate-prompts --policies policy.txt --output prompts.json"
echo ""

echo "# Enable verbose logging:"
echo "imagebreak --verbose test-images --prompts prompts.json"
echo ""

echo "# Use Gemini for text generation:"
echo "imagebreak alter-prompts --prompts prompts.json --model gemini"
echo ""

echo "# Custom HuggingFace model:"
echo "imagebreak test-images --prompts prompts.json --hf-model 'Salesforce/blip2-flan-t5-xl'"
echo ""

echo "# Disable cyclic generation (legacy mode):"
echo "imagebreak test-images --prompts prompts.json --no-use-cyclic"
echo ""

echo "# Custom system instruction:"
echo "imagebreak generate-prompts --policies policy.txt --output prompts.json \\"
echo "  --system-instruction 'You are a specialized AI safety researcher...'" 