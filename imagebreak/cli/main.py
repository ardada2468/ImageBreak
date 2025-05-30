"""Command-line interface for ImageBreak framework."""

import click
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional

from .. import ImageBreakFramework, Config
from ..models import OpenAIModel, GeminiModel, HuggingFaceImageAnalyzer
from ..core.cyclic_generator import CyclicImageGenerator
from ..types import PromptData


@click.group()
@click.option('--config', '-c', type=click.Path(exists=True), help='Configuration file path')
@click.option('--output-dir', '-o', type=click.Path(), help='Output directory')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--env-file', type=click.Path(exists=True), help='Environment file path (.env)')
@click.pass_context
def cli(ctx, config, output_dir, verbose, env_file):
    """ImageBreak: AI Safety Testing Framework
    
    A comprehensive framework for testing AI model safety and content moderation systems.
    Supports boundary testing, prompt alteration, cyclic generation with quality assessment,
    and integration with multiple AI models including OpenAI, Gemini, and HuggingFace.
    """
    ctx.ensure_object(dict)
    
    # Load environment file if specified
    if env_file:
        from dotenv import load_dotenv
        load_dotenv(env_file)
    
    # Load configuration
    if config:
        ctx.obj['config'] = Config.from_file(config)
    else:
        ctx.obj['config'] = Config()
    
    if output_dir:
        ctx.obj['config'].output_dir = Path(output_dir)
    
    if verbose:
        ctx.obj['config'].log_level = "DEBUG"
        ctx.obj['config'].enable_logging = True
    
    # Store config but don't initialize framework yet
    # Framework will be initialized in individual commands as needed


def get_framework(ctx):
    """Initialize and return framework, with validation."""
    if 'framework' not in ctx.obj:
        try:
            ctx.obj['framework'] = ImageBreakFramework(ctx.obj['config'])
        except ValueError as e:
            if "API key" in str(e):
                click.echo(f"❌ Configuration Error: {e}")
                click.echo("💡 Please set your API keys in environment variables or .env file:")
                click.echo("   - OPENAI_API_KEY=your_openai_key")
                click.echo("   - GOOGLE_API_KEY=your_google_key")
                ctx.exit(1)
            else:
                raise
    return ctx.obj['framework']


@cli.command()
@click.option('--policies', '-p', type=click.Path(exists=True), required=True, 
              help='Path to policies/guidelines text file')
@click.option('--output', '-o', type=click.Path(), required=True, 
              help='Output JSON file for generated prompts')
@click.option('--num-prompts', '-n', type=int, default=10, 
              help='Number of prompts to generate')
@click.option('--topics', '-t', multiple=True, 
              help='Specific topics to focus on (can be used multiple times)')
@click.option('--model', '-m', type=click.Choice(['openai', 'gemini']), default='openai',
              help='Model to use for prompt generation')
@click.option('--system-instruction', type=str,
              help='Custom system instruction for boundary prompt generation')
@click.pass_context
def generate_prompts(ctx, policies, output, num_prompts, topics, model, system_instruction):
    """Generate boundary-testing prompts that challenge ethical guidelines.
    
    This command generates prompts designed to test the robustness of content
    moderation systems by creating scenarios that challenge ethical boundaries.
    """
    framework = get_framework(ctx)
    config = ctx.obj['config']
    
    # Override system instruction if provided
    if system_instruction:
        config.boundary_prompt_system_instruction = system_instruction
    
    # Add the specified model
    if model == 'openai':
        if not config.openai_api_key:
            click.echo("❌ OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
            return
        framework.add_model('openai', OpenAIModel(
            api_key=config.openai_api_key,
            config=config
        ))
    elif model == 'gemini':
        if not config.google_api_key:
            click.echo("❌ Google API key not found. Set GOOGLE_API_KEY environment variable.")
            return
        framework.add_model('gemini', GeminiModel(
            api_key=config.google_api_key,
            config=config
        ))
    
    # Load policies
    with open(policies, 'r') as f:
        policies_text = f.read()
    
    # Generate prompts
    click.echo(f"🔄 Generating {num_prompts} boundary-testing prompts using {model}...")
    
    try:
        prompts = framework.generate_boundary_prompts(
            policies=policies_text,
            num_prompts=num_prompts,
            topics=list(topics) if topics else None,
            model_name=model
        )
        
        # Save prompts as JSON
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        prompts_data = []
        for prompt in prompts:
            prompts_data.append({
                "original_prompt": prompt.original_prompt,
                "generation_method": prompt.generation_method,
                "topics": prompt.topics,
                "timestamp": prompt.timestamp.isoformat() if prompt.timestamp else None
            })
        
        with open(output_path, 'w') as f:
            json.dump(prompts_data, f, indent=2)
        
        click.echo(f"✅ Generated {len(prompts)} prompts and saved to {output}")
        
    except Exception as e:
        click.echo(f"❌ Error generating prompts: {e}")


@cli.command()
@click.option('--prompts', '-p', type=click.Path(exists=True), required=True,
              help='Path to JSON file containing prompts')
@click.option('--output', '-o', type=click.Path(), 
              help='Output JSON file for altered prompts')
@click.option('--model', '-m', type=click.Choice(['openai', 'gemini']), default='openai',
              help='Model to use for prompt alteration')
@click.option('--system-instruction', type=str,
              help='Custom system instruction for prompt alteration')
@click.pass_context
def alter_prompts(ctx, prompts, output, model, system_instruction):
    """Generate altered versions of prompts to test filter evasion.
    
    This command takes existing prompts and creates alternative versions
    designed to evade content filters while maintaining similar intent.
    """
    framework = get_framework(ctx)
    config = ctx.obj['config']
    
    # Override system instruction if provided
    if system_instruction:
        config.prompt_alteration_system_instruction = system_instruction
    
    # Add the specified model
    if model == 'openai':
        if not config.openai_api_key:
            click.echo("❌ OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
            return
        framework.add_model('openai', OpenAIModel(
            api_key=config.openai_api_key,
            config=config
        ))
    elif model == 'gemini':
        if not config.google_api_key:
            click.echo("❌ Google API key not found. Set GOOGLE_API_KEY environment variable.")
            return
        framework.add_model('gemini', GeminiModel(
            api_key=config.google_api_key,
            config=config
        ))
    
    # Load prompts
    with open(prompts, 'r') as f:
        prompts_data = json.load(f)
    
    prompt_data_list = []
    for item in prompts_data:
        prompt_data_list.append(PromptData(
            original_prompt=item['original_prompt'],
            generation_method=item.get('generation_method', 'unknown')
        ))
    
    click.echo(f"🔄 Altering {len(prompt_data_list)} prompts using {model}...")
    
    try:
        altered_prompts = framework.alter_prompts(prompt_data_list, model_name=model)
        
        # Save altered prompts
        if not output:
            output = prompts.replace('.json', '_altered.json')
        
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        altered_data = []
        for prompt in altered_prompts:
            altered_data.append({
                "original_prompt": prompt.original_prompt,
                "altered_prompt": prompt.altered_prompt,
                "generation_method": prompt.generation_method,
                "alteration_method": prompt.alteration_method,
                "timestamp": prompt.timestamp.isoformat() if prompt.timestamp else None
            })
        
        with open(output_path, 'w') as f:
            json.dump(altered_data, f, indent=2)
        
        click.echo(f"✅ Altered {len(altered_prompts)} prompts and saved to {output}")
        
    except Exception as e:
        click.echo(f"❌ Error altering prompts: {e}")


@cli.command()
@click.option('--prompts', '-p', type=click.Path(exists=True), required=True,
              help='Path to JSON file containing prompts')
@click.option('--image-model', type=click.Choice(['openai']), default='openai',
              help='Model to use for image generation')
@click.option('--text-model', type=click.Choice(['openai', 'gemini']), default='openai',
              help='Model to use for text generation and prompt refinement')
@click.option('--use-cyclic', is_flag=True, default=True,
              help='Use cyclic generation with quality assessment')
@click.option('--max-attempts', type=int, default=3,
              help='Maximum retry attempts for cyclic generation')
@click.option('--quality-threshold', type=float, default=0.7,
              help='Quality threshold for accepting generated images (0.0-1.0)')
@click.option('--save-images', is_flag=True, default=True,
              help='Save generated images locally')
@click.option('--output-folder', type=click.Path(),
              help='Folder to save generated images')
@click.option('--use-altered', is_flag=True, default=True,
              help='Use altered prompts when available')
@click.option('--hf-model', type=str, default='Salesforce/blip2-opt-2.7b',
              help='HuggingFace model for image analysis')
@click.pass_context
def test_images(ctx, prompts, image_model, text_model, use_cyclic, max_attempts, 
                quality_threshold, save_images, output_folder, use_altered, hf_model):
    """Test image generation with advanced cyclic quality assessment.
    
    This command generates images from prompts and optionally uses cyclic
    generation with quality assessment to retry if images don't meet standards.
    """
    framework = get_framework(ctx)
    config = ctx.obj['config']
    
    # Update config with CLI parameters
    config.enable_cyclic_regeneration = use_cyclic
    config.max_retry_attempts = max_attempts
    config.quality_threshold = quality_threshold
    
    # Add models
    if image_model == 'openai':
        if not config.openai_api_key:
            click.echo("❌ OpenAI API key not found for image generation.")
            return
        framework.add_model('openai', OpenAIModel(
            api_key=config.openai_api_key,
            config=config
        ))
    
    if text_model == 'openai' and 'openai' not in framework.models:
        framework.add_model('openai', OpenAIModel(
            api_key=config.openai_api_key,
            config=config
        ))
    elif text_model == 'gemini':
        if not config.google_api_key:
            click.echo("❌ Google API key not found for text generation.")
            return
        framework.add_model('gemini', GeminiModel(
            api_key=config.google_api_key,
            config=config
        ))
    
    # Load prompts
    with open(prompts, 'r') as f:
        prompts_data = json.load(f)
    
    prompt_data_list = []
    for item in prompts_data:
        prompt_data_list.append(PromptData(
            original_prompt=item['original_prompt'],
            altered_prompt=item.get('altered_prompt'),
            generation_method=item.get('generation_method', 'unknown'),
            alteration_method=item.get('alteration_method')
        ))
    
    click.echo(f"🖼️  Testing image generation with {len(prompt_data_list)} prompts")
    click.echo(f"   📊 Cyclic generation: {use_cyclic}")
    if use_cyclic:
        click.echo(f"   🔄 Max attempts: {max_attempts}")
        click.echo(f"   ⭐ Quality threshold: {quality_threshold}")
        click.echo(f"   🤖 Analysis model: {hf_model}")
    
    try:
        # Set up generation parameters
        generation_kwargs = {}
        if save_images:
            if output_folder:
                generation_kwargs['save_folder'] = output_folder
            else:
                generation_kwargs['save_folder'] = str(config.output_dir / "images")
        
        # Run tests based on cyclic setting
        if use_cyclic:
            # Initialize HuggingFace analyzer if available
            try:
                hf_analyzer = HuggingFaceImageAnalyzer(model_name=hf_model)
                cyclic_generator = CyclicImageGenerator(
                    config=config,
                    image_analyzer=hf_analyzer
                )
                click.echo(f"✅ Initialized HuggingFace analyzer: {hf_model}")
            except Exception as e:
                click.echo(f"⚠️  HuggingFace analyzer failed, using basic quality assessment: {e}")
                cyclic_generator = CyclicImageGenerator(config=config)
            
            results = framework.test_image_generation_cyclic(
                prompt_data_list=prompt_data_list,
                image_model_name=image_model,
                text_model_name=text_model,
                save_images=save_images,
                **generation_kwargs
            )
            
            # Display results
            successful = sum(1 for r in results if r.success)
            total_attempts = sum(r.total_attempts for r in results)
            avg_quality = sum(r.final_quality_score for r in results 
                             if r.final_quality_score is not None) / len(results) if results else 0
            
            click.echo(f"\n📊 Cyclic Generation Results:")
            click.echo(f"   ✅ Successful: {successful}/{len(results)} ({successful/len(results)*100:.1f}%)")
            click.echo(f"   🔄 Total attempts: {total_attempts}")
            click.echo(f"   ⭐ Average quality: {avg_quality:.2f}")
            
        else:
            # Legacy mode
            batch_results = framework.run_safety_tests(
                prompt_data_list=prompt_data_list,
                model_names=[image_model],
                test_alterations=False,
                test_image_generation=True,
                run_moderation_analysis=config.use_aws_moderation,
                use_cyclic_generation=False
            )
            
            results = batch_results.results
            click.echo(f"\n📊 Generation Results:")
            click.echo(f"   ✅ Success rate: {batch_results.summary_stats.get('success_rate', 0):.1%}")
            click.echo(f"   🚫 Filter bypass rate: {batch_results.summary_stats.get('filter_bypass_rate', 0):.1%}")
        
        # Save detailed results
        timestamp = int(time.time())
        results_file = config.output_dir / f"image_test_results_{timestamp}.json"
        
        if use_cyclic:
            # Save cyclic results
            results_data = []
            for result in results:
                results_data.append({
                    "original_prompt": result.prompt_data.original_prompt,
                    "altered_prompt": result.prompt_data.altered_prompt,
                    "success": result.success,
                    "total_attempts": result.total_attempts,
                    "final_quality_score": result.final_quality_score,
                    "exceeded_max_attempts": result.exceeded_max_attempts,
                    "image_path": result.final_response.image_path,
                    "image_url": result.final_response.image_url,
                    "attempts": [
                        {
                            "attempt_number": attempt.attempt_number,
                            "prompt_used": attempt.prompt_used,
                            "quality_score": attempt.quality_score,
                            "success": attempt.response.status.value == "success"
                        }
                        for attempt in result.attempts
                    ]
                })
        else:
            # Save legacy results
            results_data = {
                "summary": batch_results.summary_stats,
                "results": [
                    {
                        "original_prompt": r.prompt_data.original_prompt,
                        "altered_prompt": r.prompt_data.altered_prompt,
                        "model_name": r.model_name,
                        "success": r.response.status.value == "success",
                        "image_path": r.response.image_path,
                        "image_url": r.response.image_url
                    }
                    for r in results
                ]
            }
        
        with open(results_file, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        click.echo(f"💾 Detailed results saved to {results_file}")
        
    except Exception as e:
        click.echo(f"❌ Error testing images: {e}")
        import traceback
        if ctx.obj['config'].log_level == "DEBUG":
            click.echo(traceback.format_exc())


@cli.command()
@click.option('--policies', '-p', type=click.Path(exists=True), required=True,
              help='Path to policies/guidelines text file')
@click.option('--num-prompts', '-n', type=int, default=5,
              help='Number of prompts to generate')
@click.option('--image-model', type=click.Choice(['openai']), default='openai',
              help='Model for image generation')
@click.option('--text-model', type=click.Choice(['openai', 'gemini']), default='openai',
              help='Model for text generation')
@click.option('--use-cyclic', is_flag=True, default=True,
              help='Use cyclic generation with quality assessment')
@click.option('--quality-threshold', type=float, default=0.7,
              help='Quality threshold for cyclic generation')
@click.pass_context
def full_test(ctx, policies, num_prompts, image_model, text_model, use_cyclic, quality_threshold):
    """Run a complete end-to-end safety test pipeline.
    
    This command runs the full pipeline: generate boundary prompts, alter them,
    and test image generation with cyclic quality assessment.
    """
    framework = get_framework(ctx)
    config = ctx.obj['config']
    
    config.enable_cyclic_regeneration = use_cyclic
    config.quality_threshold = quality_threshold
    
    # Add models
    if image_model == 'openai' or text_model == 'openai':
        if not config.openai_api_key:
            click.echo("❌ OpenAI API key required.")
            return
        framework.add_model('openai', OpenAIModel(
            api_key=config.openai_api_key,
            config=config
        ))
    
    if text_model == 'gemini':
        if not config.google_api_key:
            click.echo("❌ Google API key required for Gemini.")
            return
        framework.add_model('gemini', GeminiModel(
            api_key=config.google_api_key,
            config=config
        ))
    
    # Load policies
    with open(policies, 'r') as f:
        policies_text = f.read()
    
    click.echo(f"🚀 Running full safety test pipeline...")
    click.echo(f"   📝 Generating {num_prompts} boundary prompts")
    click.echo(f"   🔄 Altering prompts for filter evasion")
    click.echo(f"   🖼️  Testing image generation")
    if use_cyclic:
        click.echo(f"   ⭐ Using cyclic generation (threshold: {quality_threshold})")
    
    try:
        # Step 1: Generate boundary prompts
        prompts = framework.generate_boundary_prompts(
            policies=policies_text,
            num_prompts=num_prompts,
            model_name=text_model
        )
        click.echo(f"   ✅ Generated {len(prompts)} boundary prompts")
        
        # Step 2: Alter prompts
        altered_prompts = framework.alter_prompts(prompts, model_name=text_model)
        click.echo(f"   ✅ Created altered versions")
        
        # Step 3: Test image generation
        if use_cyclic:
            results = framework.test_image_generation_cyclic(
                prompt_data_list=altered_prompts,
                image_model_name=image_model,
                text_model_name=text_model,
                save_images=True
            )
            
            successful = sum(1 for r in results if r.success)
            total_attempts = sum(r.total_attempts for r in results)
            avg_quality = sum(r.final_quality_score for r in results 
                             if r.final_quality_score is not None) / len(results) if results else 0
            
            click.echo(f"\n🎯 Full Test Results:")
            click.echo(f"   ✅ Successful generations: {successful}/{len(results)} ({successful/len(results)*100:.1f}%)")
            click.echo(f"   🔄 Total attempts: {total_attempts}")
            click.echo(f"   ⭐ Average quality: {avg_quality:.2f}")
            
            # Save results
            timestamp = int(time.time())
            results_file = config.output_dir / f"full_test_results_{timestamp}.json"
            
            summary_data = {
                "test_config": {
                    "num_prompts": num_prompts,
                    "image_model": image_model,
                    "text_model": text_model,
                    "use_cyclic": use_cyclic,
                    "quality_threshold": quality_threshold
                },
                "summary": {
                    "total_prompts": len(results),
                    "successful_generations": successful,
                    "success_rate": successful / len(results) if results else 0,
                    "total_attempts": total_attempts,
                    "average_quality": avg_quality
                },
                "detailed_results": [
                    {
                        "original_prompt": r.prompt_data.original_prompt,
                        "altered_prompt": r.prompt_data.altered_prompt,
                        "success": r.success,
                        "attempts": r.total_attempts,
                        "quality": r.final_quality_score,
                        "image_path": r.final_response.image_path
                    }
                    for r in results
                ]
            }
            
            with open(results_file, 'w') as f:
                json.dump(summary_data, f, indent=2)
            
            click.echo(f"💾 Full test results saved to {results_file}")
        
        else:
            batch_results = framework.run_safety_tests(
                prompt_data_list=altered_prompts,
                model_names=[image_model],
                test_alterations=False,
                test_image_generation=True,
                run_moderation_analysis=config.use_aws_moderation,
                use_cyclic_generation=False
            )
            
            click.echo(f"\n🎯 Full Test Results:")
            click.echo(f"   ✅ Success rate: {batch_results.summary_stats.get('success_rate', 0):.1%}")
            click.echo(f"   🚫 Filter bypass rate: {batch_results.summary_stats.get('filter_bypass_rate', 0):.1%}")
        
    except Exception as e:
        click.echo(f"❌ Error in full test: {e}")
        import traceback
        if ctx.obj['config'].log_level == "DEBUG":
            click.echo(traceback.format_exc())


@cli.command()
@click.option('--host', default='localhost', help='Host to bind the server to (default: localhost)')
@click.option('--port', default=8501, type=int, help='Port to run the server on (default: 8501)')
@click.option('--browser/--no-browser', default=True, help='Automatically open browser (default: True)')
@click.option('--theme', type=click.Choice(['light', 'dark']), help='UI theme')
@click.option('--headless', is_flag=True, help='Run in headless mode')
@click.pass_context
def web_ui(ctx, host, port, browser, theme, headless):
    """Launch the Streamlit web UI for interactive configuration and testing.
    
    This command starts the Streamlit web interface where you can:
    - Configure API keys and model settings
    - Customize system instructions
    - Run tests with real-time progress tracking
    - View and export results
    - Generate images with cyclic quality assessment
    """
    click.echo("🌐 Launching ImageBreak Web UI...")
    click.echo(f"   🏠 Host: {host}")
    click.echo(f"   🔌 Port: {port}")
    click.echo(f"   🌐 URL: http://{host}:{port}")
    
    # Find the streamlit app file
    current_dir = Path(__file__).parent.parent.parent  # Go up to project root
    streamlit_app = current_dir / "streamlit_app.py"
    
    if not streamlit_app.exists():
        click.echo(f"❌ Streamlit app not found at {streamlit_app}")
        click.echo("💡 Make sure streamlit_app.py is in the project root directory")
        return
    
    # Build streamlit command
    cmd = [
        sys.executable, "-m", "streamlit", "run", str(streamlit_app),
        "--server.address", host,
        "--server.port", str(port)
    ]
    
    # Add browser option
    if not browser or headless:
        cmd.extend(["--server.headless", "true"])
    
    # Add theme option
    if theme:
        if theme == 'light':
            cmd.extend(["--theme.base", "light"])
        elif theme == 'dark':
            cmd.extend(["--theme.base", "dark"])
    
    # Load environment file if specified at CLI level
    env = os.environ.copy()
    if ctx.parent and hasattr(ctx.parent, 'params') and 'env_file' in ctx.parent.params:
        env_file = ctx.parent.params['env_file']
        if env_file and Path(env_file).exists():
            from dotenv import load_dotenv
            load_dotenv(env_file)
            click.echo(f"   📄 Loaded environment from: {env_file}")
    
    try:
        click.echo("🚀 Starting Streamlit server...")
        if not browser or headless:
            click.echo(f"   💻 Open your browser and navigate to: http://{host}:{port}")
        
        # Check if Streamlit is installed
        try:
            import streamlit
        except ImportError:
            click.echo("❌ Streamlit not found. Installing streamlit...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit"])
            click.echo("✅ Streamlit installed successfully")
        
        # Run streamlit
        result = subprocess.run(cmd, env=env)
        
        if result.returncode != 0:
            click.echo(f"❌ Streamlit exited with code {result.returncode}")
        else:
            click.echo("✅ Streamlit server stopped")
            
    except KeyboardInterrupt:
        click.echo("\n⏹️  Stopping Streamlit server...")
    except FileNotFoundError:
        click.echo("❌ Streamlit not found. Please install it with: pip install streamlit")
    except Exception as e:
        click.echo(f"❌ Error starting Streamlit: {e}")


@cli.command()
@click.pass_context
def config_info(ctx):
    """Display current configuration information."""
    config = ctx.obj['config']
    
    click.echo("🔧 ImageBreak Configuration:")
    click.echo(f"   📁 Output directory: {config.output_dir}")
    click.echo(f"   📝 Logging: {config.enable_logging} (level: {config.log_level})")
    click.echo(f"   🔄 Cyclic generation: {config.enable_cyclic_regeneration}")
    if config.enable_cyclic_regeneration:
        click.echo(f"   🎯 Max attempts: {config.max_retry_attempts}")
        click.echo(f"   ⭐ Quality threshold: {config.quality_threshold}")
    click.echo(f"   ☁️  AWS moderation: {config.use_aws_moderation}")
    
    click.echo("\n🔑 API Keys:")
    click.echo(f"   OpenAI: {'✅ Set' if config.openai_api_key else '❌ Not set'}")
    click.echo(f"   Google: {'✅ Set' if config.google_api_key else '❌ Not set'}")
    click.echo(f"   HuggingFace: {'✅ Set' if config.huggingface_token else '❌ Not set (optional)'}")
    if config.use_aws_moderation:
        click.echo(f"   AWS: {'✅ Set' if config.aws_access_key_id and config.aws_secret_access_key else '❌ Not set'}")
    
    click.echo("\n🤖 Default Models:")
    click.echo(f"   Text: {config.default_text_model}")
    click.echo(f"   Image: {config.default_image_model}")


def main():
    """Entry point for the CLI."""
    cli() 