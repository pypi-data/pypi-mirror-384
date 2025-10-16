"""
Main CLI interface for autoklug
"""
import asyncio
import os
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Optional

import click
import requests
from click import echo, style

from ...utils import ConfigManager, log_header, log_success, log_error, log_info, detect_project_context, find_best_config_files, ensure_config_files_exist
from ...error_messages import get_user_friendly_error
from ..builders import BlazingFastBuilder
from ...env import save_env, load_env, list_envs, delete_env
from ...run import start_local_server
from ...templates import init, template
from ...monitoring import setup_monitoring, monitoring_status, CloudWatchManager
from ...testing import test, test_function


@click.group()
@click.version_option(version='2.0.3', prog_name='Autoklug')
def cli():
    """🚀 Autoklug - Blazing Fast AWS Lambda Build System"""
    pass


# Build Commands
@cli.command()
@click.option('--tool', '-t', help='Path to .tool configuration file')
@click.option('--env', '-e', help='Path to .env file for environment variables')
@click.option('--force-update-layers', is_flag=True, help='Force update all layers')
@click.option('--verbose', is_flag=True, help='Enable verbose logging')
@click.option('--dry-run', is_flag=True, help='Show what would be built without actually building')
def build(tool, env, force_update_layers, verbose, dry_run):
    """🏗️ Build the complete Lambda infrastructure"""
    
    async def run_build():
        try:
            # Ensure both config files exist (create defaults if missing)
            tool_path, env_path = ensure_config_files_exist(tool, env)
            
            builder = BlazingFastBuilder(tool_path, env_path, force_update_layers)
            
            if dry_run:
                log_header("DRY RUN - BUILD SIMULATION")
                log_info("This would build:")
                log_info(f"  • Tool config: {tool_path}")
                log_info(f"  • Env config: {env_path}")
                log_info(f"  • Force update layers: {force_update_layers}")
                log_info(f"  • Verbose logging: {verbose}")
                log_success("Dry run completed - no actual build performed")
                return
            
            success = await builder.build()
            
            if success:
                log_success("Build completed successfully!")
            else:
                log_error("Build failed!")
                sys.exit(1)
                
        except Exception as e:
            friendly_error = get_user_friendly_error(e, context="Build process")
            log_error(friendly_error)
            sys.exit(1)
    
    asyncio.run(run_build())


@cli.command()
@click.option('--tool', '-t', help='Path to .tool configuration file')
@click.option('--env', '-e', help='Path to .env file for environment variables')
@click.option('--force-update-layers', is_flag=True, help='Force update all layers')
def build_layers(tool, env, force_update_layers):
    """📦 Build Lambda layers only"""
    
    async def run_build_layers():
        try:
            # Ensure both config files exist (create defaults if missing)
            tool_path, env_path = ensure_config_files_exist(tool, env)
            
            builder = BlazingFastBuilder(tool_path, env_path, force_update_layers)
            success = await builder.build_layers_only()
            
            if success:
                log_success("Layer build completed successfully!")
            else:
                log_error("Layer build failed!")
                sys.exit(1)
                
        except Exception as e:
            friendly_error = get_user_friendly_error(e, context="Layer build process")
            log_error(friendly_error)
            sys.exit(1)
    
    asyncio.run(run_build_layers())


@cli.command()
@click.option('--tool', '-t', help='Path to .tool configuration file')
@click.option('--env', '-e', help='Path to .env file for environment variables')
@click.option('--force-update-layers', is_flag=True, help='Force update all layers')
def build_functions(tool, env, force_update_layers):
    """⚡ Build Lambda functions only"""
    
    async def run_build_functions():
        try:
            # Ensure both config files exist (create defaults if missing)
            tool_path, env_path = ensure_config_files_exist(tool, env)
            
            builder = BlazingFastBuilder(tool_path, env_path, force_update_layers)
            success = await builder.build_functions_only()
            
            if success:
                log_success("Function build completed successfully!")
            else:
                log_error("Function build failed!")
                sys.exit(1)
                
        except Exception as e:
            friendly_error = get_user_friendly_error(e, context="Function build process")
            log_error(friendly_error)
            sys.exit(1)
    
    asyncio.run(run_build_functions())


@cli.command()
@click.option('--tool', '-t', help='Path to .tool configuration file')
@click.option('--env', '-e', help='Path to .env file for environment variables')
def build_api(tool, env):
    """🌐 Build API Gateway only"""
    
    async def run_build_api():
        try:
            # Ensure both config files exist (create defaults if missing)
            tool_path, env_path = ensure_config_files_exist(tool, env)
            
            builder = BlazingFastBuilder(tool_path, env_path)
            success = await builder.build_api_only()
            
            if success:
                log_success("API Gateway build completed successfully!")
            else:
                log_error("API Gateway build failed!")
                sys.exit(1)
                
        except Exception as e:
            friendly_error = get_user_friendly_error(e, context="API Gateway build process")
            log_error(friendly_error)
            sys.exit(1)
    
    asyncio.run(run_build_api())


# Development Commands
@cli.command()
@click.option('--tool', '-t', help='Path to .tool configuration file')
@click.option('--env', '-e', help='Path to .env file for environment variables')
@click.option('--port', '-p', default=5000, help='Port to run the server on')
@click.option('--use-authorizer', is_flag=True, help='Enable API Gateway authorizer simulation')
@click.option('--use-auth-cache', is_flag=True, help='Enable caching for authorizer results')
@click.option('--auth-cache-ttl', default=300, help='TTL for authorizer cache in seconds')
def run(tool, env, port, use_authorizer, use_auth_cache, auth_cache_ttl):
    """🚀 Run local development server"""
    
    try:
        # Ensure both config files exist (create defaults if missing)
        tool_path, env_path = ensure_config_files_exist(tool, env)
        
        log_header("STARTING DEVELOPMENT SERVER")
        start_local_server(
            tool_path=tool_path,
            env_path=env_path,
            use_authorizer=use_authorizer,
            use_auth_cache=use_auth_cache,
            auth_cache_ttl=auth_cache_ttl,
            port=port
        )
        
    except Exception as e:
        friendly_error = get_user_friendly_error(e, context="Development server startup")
        log_error(friendly_error)
        sys.exit(1)


@cli.command()
@click.argument('template_name')
@click.option('--output-dir', '-o', default='.', help='Output directory for generated files')
@click.option('--force', is_flag=True, help='Overwrite existing files')
def init_template(template_name, output_dir, force):
    """📋 Initialize project with a template"""
    
    try:
        log_header(f"INITIALIZING TEMPLATE: {template_name}")
        success = init(template_name, output_dir, force)
        
        if success:
            log_success(f"Template '{template_name}' initialized successfully!")
        else:
            log_error("Template initialization failed!")
            sys.exit(1)
            
    except Exception as e:
        friendly_error = get_user_friendly_error(e, context="Template initialization")
        log_error(friendly_error)
        sys.exit(1)


@cli.command()
@click.argument('template_name')
def show_template(template_name):
    """📄 Show template content"""
    
    try:
        log_header(f"SHOWING TEMPLATE: {template_name}")
        template(template_name)
        
    except Exception as e:
        friendly_error = get_user_friendly_error(e, context="Template display")
        log_error(friendly_error)
        sys.exit(1)


# Environment Commands
@cli.command()
@click.option('--tool', '-t', help='Path to .tool configuration file')
@click.option('--env', '-e', help='Path to .env file for environment variables')
@click.option('--name', '-n', help='Environment name to save as')
def env_save(tool, env, name):
    """💾 Save environment to AWS Secrets Manager"""
    
    async def run_save():
        try:
            # Ensure both config files exist (create defaults if missing)
            tool_path, env_path = ensure_config_files_exist(tool, env)
            
            builder = BlazingFastBuilder(tool_path, env_path)
            
            log_header("SAVING ENVIRONMENT")
            success = await save_env(builder.config, name)
            
            if success:
                log_success("Environment saved successfully!")
            else:
                log_error("Environment save failed!")
                sys.exit(1)
                
        except Exception as e:
            friendly_error = get_user_friendly_error(e, context="Environment save")
            log_error(friendly_error)
            sys.exit(1)
    
    asyncio.run(run_save())


@cli.command()
@click.option('--tool', '-t', help='Path to .tool configuration file')
@click.option('--env', '-e', help='Path to .env file for environment variables')
@click.option('--name', '-n', help='Environment name to load')
def env_load(tool, env, name):
    """📥 Load environment from AWS Secrets Manager"""
    
    async def run_load():
        try:
            # Ensure both config files exist (create defaults if missing)
            tool_path, env_path = ensure_config_files_exist(tool, env)
            
            builder = BlazingFastBuilder(tool_path, env_path)
            
            log_header("LOADING ENVIRONMENT")
            success = await load_env(builder.config, name)
            
            if success:
                log_success("Environment loaded successfully!")
            else:
                log_error("Environment load failed!")
                sys.exit(1)
                
        except Exception as e:
            friendly_error = get_user_friendly_error(e, context="Environment load")
            log_error(friendly_error)
            sys.exit(1)
    
    asyncio.run(run_load())


@cli.command()
@click.option('--tool', '-t', help='Path to .tool configuration file')
@click.option('--env', '-e', help='Path to .env file for environment variables')
def env_list(tool, env):
    """📋 List available environments"""
    
    async def run_list():
        try:
            # Ensure both config files exist (create defaults if missing)
            tool_path, env_path = ensure_config_files_exist(tool, env)
            
            builder = BlazingFastBuilder(tool_path, env_path)
            
            log_header("AVAILABLE ENVIRONMENTS")
            await list_envs(builder.config)
            
        except Exception as e:
            friendly_error = get_user_friendly_error(e, context="Environment list")
            log_error(friendly_error)
            sys.exit(1)
    
    asyncio.run(run_list())


@cli.command()
@click.option('--tool', '-t', help='Path to .tool configuration file')
@click.option('--env', '-e', help='Path to .env file for environment variables')
@click.option('--name', '-n', help='Environment name to delete')
def env_delete(tool, env, name):
    """🗑️ Delete environment from AWS Secrets Manager"""
    
    async def run_delete():
        try:
            # Ensure both config files exist (create defaults if missing)
            tool_path, env_path = ensure_config_files_exist(tool, env)
            
            builder = BlazingFastBuilder(tool_path, env_path)
            
            log_header("DELETING ENVIRONMENT")
            success = await delete_env(builder.config, name)
            
            if success:
                log_success("Environment deleted successfully!")
            else:
                log_error("Environment deletion failed!")
                sys.exit(1)
                
        except Exception as e:
            friendly_error = get_user_friendly_error(e, context="Environment deletion")
            log_error(friendly_error)
            sys.exit(1)
    
    asyncio.run(run_delete())


# Layer Commands
@cli.command()
@click.argument('layer_path', type=click.Path())
@click.option('--force', is_flag=True, help='Force overwrite existing files')
def layer_jumpstart(layer_path: str, force: bool):
    """🚀 Jumpstart a layer with bootstrap content from CloudFront"""
    
    layer_path = Path(layer_path).resolve()
    
    if not layer_path.exists():
        echo(style(f"❌ Layer path does not exist: {layer_path}", fg='red'))
        sys.exit(1)
    
    if not layer_path.is_dir():
        echo(style(f"❌ Layer path is not a directory: {layer_path}", fg='red'))
        sys.exit(1)
    
    log_header(f"JUMPSTARTING LAYER: {layer_path}")
    
    try:
        # Download bootstrap content from CloudFront
        bootstrap_url = "https://d1g8r8v8v8v8v8.cloudfront.net/bootstrap.zip"
        
        log_info("Downloading bootstrap content...")
        response = requests.get(bootstrap_url, timeout=30)
        response.raise_for_status()
        
        # Extract to layer directory
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_file:
            temp_file.write(response.content)
            temp_file_path = temp_file.name
        
        try:
            with zipfile.ZipFile(temp_file_path, 'r') as zip_ref:
                # Check if files already exist
                existing_files = []
                for file_info in zip_ref.filelist:
                    target_path = layer_path / file_info.filename
                    if target_path.exists() and not force:
                        existing_files.append(file_info.filename)
                
                if existing_files and not force:
                    echo(style(f"❌ Files already exist: {existing_files}", fg='red'))
                    echo(style("Use --force to overwrite existing files", fg='yellow'))
                    sys.exit(1)
                
                # Extract files
                zip_ref.extractall(layer_path)
                
                log_success(f"Layer jumpstarted successfully!")
                log_info(f"Extracted {len(zip_ref.filelist)} files to {layer_path}")
                
        finally:
            os.unlink(temp_file_path)
            
    except requests.RequestException as e:
        log_error(f"Failed to download bootstrap content: {e}")
        sys.exit(1)
    except zipfile.BadZipFile as e:
        log_error(f"Invalid zip file: {e}")
        sys.exit(1)
    except Exception as e:
        friendly_error = get_user_friendly_error(e, context="Layer jumpstart")
        log_error(friendly_error)
        sys.exit(1)


# Monitoring Commands
@cli.command()
@click.option('--tool', '-t', help='Path to .tool configuration file')
@click.option('--env', '-e', help='Path to .env file for environment variables')
def monitor_setup(tool, env):
    """🔧 Setup monitoring and observability"""
    
    try:
        # Ensure both config files exist (create defaults if missing)
        tool_path, env_path = ensure_config_files_exist(tool, env)
        
        log_header("SETTING UP MONITORING")
        setup_monitoring(tool_path, env_path)
        
    except Exception as e:
        friendly_error = get_user_friendly_error(e, context="Monitoring setup")
        log_error(friendly_error)
        sys.exit(1)


@cli.command()
@click.option('--tool', '-t', help='Path to .tool configuration file')
@click.option('--env', '-e', help='Path to .env file for environment variables')
@click.option('--function', '-f', help='Specific function to monitor')
def monitor_status(tool, env, function):
    """📊 Check monitoring status"""
    
    try:
        # Ensure both config files exist (create defaults if missing)
        tool_path, env_path = ensure_config_files_exist(tool, env)
        
        log_header("MONITORING STATUS")
        monitoring_status(tool_path, env_path, function)
        
    except Exception as e:
        friendly_error = get_user_friendly_error(e, context="Monitoring status")
        log_error(friendly_error)
        sys.exit(1)


# Testing Commands
@cli.command()
@click.option('--tool', '-t', help='Path to .tool configuration file')
@click.option('--env', '-e', help='Path to .env file for environment variables')
@click.option('--local', is_flag=True, help='Run local tests only')
@click.option('--remote', is_flag=True, help='Run remote tests only')
def test_run(tool, env, local, remote):
    """🧪 Run comprehensive tests"""
    
    try:
        # Ensure both config files exist (create defaults if missing)
        tool_path, env_path = ensure_config_files_exist(tool, env)
        
        log_header("RUNNING TESTS")
        test(tool_path, env_path, local_only=local, remote_only=remote)
        
    except Exception as e:
        friendly_error = get_user_friendly_error(e, context="Test execution")
        log_error(friendly_error)
        sys.exit(1)


@cli.command()
@click.argument('function_name')
@click.option('--tool', '-t', help='Path to .tool configuration file')
@click.option('--env', '-e', help='Path to .env file for environment variables')
@click.option('--payload', '-p', help='Test payload (JSON string)')
def test_function(function_name, tool, env, payload):
    """🧪 Test a specific function"""
    
    try:
        # Ensure both config files exist (create defaults if missing)
        tool_path, env_path = ensure_config_files_exist(tool, env)
        
        log_header(f"TESTING FUNCTION: {function_name}")
        test_function(tool_path, env_path, function_name, payload)
        
    except Exception as e:
        friendly_error = get_user_friendly_error(e, context="Function testing")
        log_error(friendly_error)
        sys.exit(1)


# Utility Commands
@cli.command()
@click.option('--tool', '-t', help='Path to .tool configuration file')
@click.option('--env', '-e', help='Path to .env file for environment variables')
def config(tool, env):
    """⚙️ Show configuration information"""
    try:
        # Ensure both config files exist (create defaults if missing)
        tool_path, env_path = ensure_config_files_exist(tool, env)
        
        # Load configuration
        config = ConfigManager(tool_path, env_path)
        
        log_header("CONFIGURATION INFORMATION")
        log_info(f"Tool config: {tool_path}")
        log_info(f"Env config: {env_path}")
        log_info(f"App name: {config.tool_config.get('APP_NAME', 'Not set')}")
        log_info(f"AWS region: {config.tool_config.get('AWS_REGION', 'Not set')}")
        log_info(f"AWS account: {config.tool_config.get('AWS_ACCOUNT_ID', 'Not set')}")
        log_info(f"Lambda runtime: {config.tool_config.get('LAMBDA_RUNTIME', 'Not set')}")
        log_info(f"API path: {config.api_path}")
        log_info(f"Layer path: {config.layer_path}")
        log_info(f"Public build: {config.is_public_build}")
        
    except Exception as e:
        friendly_error = get_user_friendly_error(e, context="Configuration loading")
        echo(style(friendly_error, fg='red'))
        raise click.Abort()


@cli.command()
@click.option('--tool', '-t', help='Path to .tool configuration file')
@click.option('--env', '-e', help='Path to .env file for environment variables')
def detect(tool, env):
    """🔍 Show project detection information"""
    try:
        context = detect_project_context()
        detected_tool, detected_env = find_best_config_files(context)
        
        log_header("PROJECT CONTEXT DETECTION")
        log_info(f"Current directory: {context['current_dir']}")
        log_info(f"Detected infrastructure: {context['infra']}")
        log_info(f"Public API detected: {context['is_public']}")
        
        log_info(f"Configuration files:")
        log_info(f"  Tool files found: {context['tool_files']}")
        log_info(f"  Env files found: {context['env_files']}")
        log_info(f"  Selected tool file: {detected_tool}")
        log_info(f"  Selected env file: {detected_env}")
        
        log_info(f"Project structure:")
        log_info(f"  API paths found: {context['api_paths']}")
        log_info(f"  Layer paths found: {context['layer_paths']}")
        
    except Exception as e:
        friendly_error = get_user_friendly_error(e, context="Project detection")
        echo(style(friendly_error, fg='red'))
        raise click.Abort()
