import gradio as gr
import subprocess
import os
import tempfile
import shutil
from pathlib import Path
import logging
from urllib.parse import urlparse
import re
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def format_status_message(message, status="info"):
    """
    Format a status message with HTML styling.
    
    Args:
        message (str): The message to format
        status (str): One of "info", "success", "error"
        
    Returns:
        str: HTML formatted message
    """
    colors = {
        "info": "#2196F3",    # Blue
        "success": "#4CAF50", # Green
        "error": "#F44336"    # Red
    }
    color = colors.get(status, colors["info"])
    timestamp = time.strftime("%H:%M:%S")
    return f'<div style="color: {color}; margin: 5px 0; font-family: monospace;"><span style="color: #666;">[{timestamp}]</span> {message}</div>'

def extract_github_username(repo_url):
    """
    Extract GitHub username from repository URL.
    
    Args:
        repo_url (str): GitHub repository URL
        
    Returns:
        str: GitHub username
    """
    # Handle both HTTPS and SSH URLs
    if repo_url.startswith('git@'):
        # SSH format: git@github.com:username/repo.git
        return repo_url.split(':')[1].split('/')[0]
    else:
        # HTTPS format: https://github.com/username/repo.git
        path = urlparse(repo_url).path
        return path.strip('/').split('/')[0]

def validate_image_name(image_name):
    """
    Validate that the image name follows Docker tag naming conventions.
    
    Args:
        image_name (str): The image name to validate
        
    Returns:
        tuple: (bool, str) - (is_valid, error_message)
    """
    if not image_name:
        return False, "Image name cannot be empty"
    
    # Docker tag naming rules:
    # - Can contain lowercase letters, digits, and separators (., -, _)
    # - Must start with a letter or digit
    # - Must not end with a separator
    if not re.match(r'^[a-z0-9][a-z0-9._-]*[a-z0-9]$', image_name):
        return False, "Image name must contain only lowercase letters, numbers, and separators (., -, _), and must start and end with a letter or number"
    
    return True, ""

def build_and_push_image(repo_url, registry_token, image_name, username=None, registry="GitHub Container Registry (GHCR)", dockerfile_subdir="."):
    temp_dir = None
    status_messages = []
    original_cwd = os.getcwd()  # Save the original working directory
    try:
        is_valid, error_msg = validate_image_name(image_name)
        if not is_valid:
            status_messages.append(format_status_message(f"Invalid image name: {error_msg}", "error"))
            yield _format_log(status_messages)
            return

        gh_username = username if username else extract_github_username(repo_url)
        if registry == "Docker Hub":
            registry_url = "docker.io"
            full_image_name = f"{gh_username}/{image_name}"
        else:
            registry_url = "ghcr.io"
            full_image_name = f"ghcr.io/{gh_username}/{image_name}"

        steps = [
            (f"Starting build process for {full_image_name}...", "info"),
            (f"Authenticating with {registry_url}...", "info")
        ]
        for msg, st in steps:
            status_messages.append(format_status_message(msg, st))
            logger.info(f"→ {msg}")
            yield _format_log(status_messages)

        login_cmd = ["docker", "login", registry_url, "-u", gh_username, "--password-stdin"]
        result = subprocess.run(login_cmd, input=registry_token, capture_output=True, text=True)
        if result.returncode != 0:
            status_messages.append(format_status_message(f"Failed to authenticate with {registry_url}: {result.stderr}", "error"))
            logger.error(f"Failed to authenticate with {registry_url}: {result.stderr}")
            yield _format_log(status_messages)
            return
        status_messages.append(format_status_message(f"Successfully authenticated with {registry_url}", "success"))
        logger.info(f"✓ Successfully authenticated with {registry_url}")
        yield _format_log(status_messages)

        temp_dir = tempfile.mkdtemp()
        status_messages.append(format_status_message(f"Created temporary directory: {temp_dir}", "info"))
        logger.info(f"→ Created temporary directory: {temp_dir}")
        yield _format_log(status_messages)

        status_messages.append(format_status_message(f"Cloning repository: {repo_url}", "info"))
        logger.info(f"→ Cloning repository: {repo_url}")
        yield _format_log(status_messages)
        clone_cmd = ["git", "clone", repo_url, temp_dir]
        result = subprocess.run(clone_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            status_messages.append(format_status_message(f"Failed to clone repository: {result.stderr}", "error"))
            logger.error(f"Failed to clone repository: {result.stderr}")
            yield _format_log(status_messages)
            return
        status_messages.append(format_status_message("Repository cloned successfully", "success"))
        logger.info("✓ Repository cloned successfully")
        yield _format_log(status_messages)

        status_messages.append(format_status_message(f"Changing to repository directory: {temp_dir}", "info"))
        logger.info(f"→ Changing to repository directory: {temp_dir}")
        os.chdir(temp_dir)
        yield _format_log(status_messages)

        # Check for Dockerfile in the specified subdirectory
        dockerfile_path = os.path.join(temp_dir, dockerfile_subdir, "Dockerfile")
        if not os.path.exists(dockerfile_path):
            status_messages.append(format_status_message(f"No Dockerfile found in the specified subdirectory: {dockerfile_subdir}", "error"))
            logger.error(f"No Dockerfile found in the specified subdirectory: {dockerfile_subdir}")
            yield _format_log(status_messages)
            return
        status_messages.append(format_status_message(f"Dockerfile found in {dockerfile_subdir}", "success"))
        logger.info(f"✓ Dockerfile found in {dockerfile_subdir}")
        yield _format_log(status_messages)

        # Build the Docker image using the specified subdirectory as context
        status_messages.append(format_status_message(f"Building Docker image: {full_image_name}", "info"))
        logger.info(f"→ Building Docker image: {full_image_name}")
        yield _format_log(status_messages)
        build_cmd = [
            "docker", "build", "-t", full_image_name, "-f", dockerfile_path, os.path.join(temp_dir, dockerfile_subdir)
        ]
        result = subprocess.run(build_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            status_messages.append(format_status_message(f"Failed to build Docker image: {result.stderr}", "error"))
            logger.error(f"Failed to build Docker image: {result.stderr}")
            yield _format_log(status_messages)
            return
        status_messages.append(format_status_message("Docker image built successfully", "success"))
        logger.info("✓ Docker image built successfully")
        yield _format_log(status_messages)

        status_messages.append(format_status_message(f"Pushing Docker image to {registry_url}...", "info"))
        logger.info(f"→ Pushing Docker image to {registry_url}...")
        yield _format_log(status_messages)
        push_cmd = ["docker", "push", full_image_name]
        result = subprocess.run(push_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            status_messages.append(format_status_message(f"Failed to push Docker image: {result.stderr}", "error"))
            logger.error(f"Failed to push Docker image: {result.stderr}")
            yield _format_log(status_messages)
            return
        status_messages.append(format_status_message(f"Successfully built and pushed image: {full_image_name}", "success"))
        logger.info(f"✓ Successfully built and pushed image: {full_image_name}")
        yield _format_log(status_messages)
        status_messages.append(format_status_message("Build process completed successfully!", "success"))
        yield _format_log(status_messages)
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        logger.error(error_msg)
        status_messages.append(format_status_message(error_msg, "error"))
        yield _format_log(status_messages)
    finally:
        try:
            os.chdir(original_cwd)
        except Exception:
            pass
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            status_messages.append(format_status_message(f"Cleaned up temporary directory: {temp_dir}", "info"))
            yield _format_log(status_messages)

def _format_log(status_messages):
    return f'<div style="background-color: #1E1E1E; padding: 15px; border-radius: 5px; border: 1px solid #333; font-family: monospace;">{"".join(status_messages)}</div>'

about_md = """
# Your Personal MCP Remote Builder for GitHub and Docker Registries

This project is a Gradio-based web and MCP server that automates building Docker images from remote GitHub repositories and publishes them to either the GitHub Container Registry (GHCR) or Docker Hub.

## The Problem

Using GitHub for CI/CD for personal projects can be frustrating, as Github's default runners are often too small and fail at even moderately complex Docker image builds due to memory constraints. And at present larger runners are only available for enterprise customers.

## Why Gradio + HuggingFace Spaces

Gradio gives your MCP setup even more freedom — you can kick off builds from anywhere: straight from your IDE or a local LLM using the MCP protocol, programmatically via your codebase or GitHub workflow, or by using the Gradio web UI.

HuggingFace Spaces is perfect for this use case – clone the app there and you can easily pick whatever size or type of machine you want to run it on, and when you’re not using it, it automatically scales right down to zero.
"""

with gr.Blocks() as demo:
    with gr.Tab("Builder"):
        gr.Markdown("# Your Personal MCP Remote Builder for Github and Docker Registries")
        with gr.Column():
            repo_url = gr.Textbox(
                label="GitHub Repository URL",
                value="https://github.com/neonwatty/gradio-mcp-test-build-repo"
            )
            registry_token = gr.Textbox(
                label="Registry Token", 
                type="password",
                value=""
            )
            image_name = gr.Textbox(
                label="Image Name",
                value="gradio-mcp-test-build-repo"
            )
            username = gr.Textbox(label="GitHub Username (optional)")
            registry = gr.Dropdown(
                label="Registry",
                choices=["GitHub Container Registry (GHCR)", "Docker Hub"],
                value="GitHub Container Registry (GHCR)"
            )
            dockerfile_subdir = gr.Textbox(
                label="Dockerfile Subdirectory (relative to repo root)",
                value=".",
                info="Path to the subdirectory containing the Dockerfile. Use '.' for the root."
            )
            build_button = gr.Button("Build and Push Image")
            output = gr.HTML(
                label="Build Progress",
                value='<div style="background-color: #1E1E1E; padding: 15px; border-radius: 5px; border: 1px solid #333; font-family: monospace;"></div>'
            )

        build_button.click(
            fn=build_and_push_image,
            inputs=[repo_url, registry_token, image_name, username, registry, dockerfile_subdir],
            outputs=output,
            concurrency_limit=1
        )
    with gr.Tab("About"):
        gr.Markdown(about_md)

demo.queue().launch(mcp_server=True)
