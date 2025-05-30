#!/usr/bin/env python3
"""
Basic usage example for ImageBreak framework.

This example demonstrates how to:
1. Set up the framework
2. Add models  
3. Generate test prompts
4. Run safety tests
5. Generate reports
"""

import os
from pathlib import Path

from imagebreak import ImageBreakFramework, Config
from imagebreak.models import OpenAIModel, GeminiModel
from imagebreak.types import PromptData


def main():
    """Run a basic ImageBreak safety test."""
    
    # 1. Initialize configuration
    config = Config(
        output_dir=Path("./results"),
        enable_logging=True,
        log_level="INFO",
        rate_limit_delay=2.0  # Be nice to APIs
    )
    
    # 2. Initialize framework
    framework = ImageBreakFramework(config)
    
    # 3. Add models to test
    try:
        framework.add_model("gpt-4", OpenAIModel(model="gpt-4"))
        print("✓ Added OpenAI GPT-4 model")
    except ValueError as e:
        print(f"⚠ Could not add OpenAI model: {e}")
    
    try:
        framework.add_model("gemini-pro", GeminiModel(model="gemini-pro"))
        print("✓ Added Gemini Pro model")
    except ValueError as e:
        print(f"⚠ Could not add Gemini model: {e}")
    
    if not framework.list_models():
        print("❌ No models available. Please check your API keys.")
        return
    
    # 4. Define content policies to test
    policies = """
    Content Policy Example:
    
    We prohibit content that:
    - Contains explicit violence or gore
    - Depicts illegal activities
    - Shows explicit sexual content
    - Promotes hate speech or discrimination
    - Contains graphic depictions of self-harm
    
    Our AI systems should refuse to generate such content.
    """
    
    # 5. Generate boundary-testing prompts
    print("\n🔍 Generating boundary-testing prompts...")
    test_prompts = framework.generate_boundary_prompts(
        policies=policies,
        num_prompts=5,
        topics=["violence", "illegal activities"],
        model_name=framework.list_models()[0]  # Use first available model
    )
    
    print(f"✓ Generated {len(test_prompts)} test prompts")
    
    # 6. Run comprehensive safety tests
    print("\n🧪 Running safety tests...")
    results = framework.run_safety_tests(
        prompt_data_list=test_prompts,
        model_names=framework.list_models(),
        test_alterations=True,
        test_image_generation=True,
        run_moderation_analysis=True  # Will use AWS if configured
    )
    
    # 7. Display summary results
    print("\n📊 Test Results Summary:")
    print(f"Total tests: {results.summary_stats.get('total_tests', 0)}")
    print(f"Successful generations: {results.summary_stats.get('successful_generations', 0)}")
    print(f"Blocked by filters: {results.summary_stats.get('blocked_by_filters', 0)}")
    print(f"Errors: {results.summary_stats.get('errors', 0)}")
    print(f"Success rate: {results.summary_stats.get('success_rate', 0):.1%}")
    print(f"Filter bypass rate: {results.summary_stats.get('filter_bypass_rate', 0):.1%}")
    
    # 8. Generate detailed report
    print("\n📝 Generating report...")
    report_path = framework.generate_report(
        batch_results=results,
        format="html"
    )
    print(f"✓ Report saved to: {report_path}")
    
    print("\n✅ Basic safety test completed!")


if __name__ == "__main__":
    main() 