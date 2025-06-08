# Your Personal MCP Remote Builder for GitHub and Docker Registries

This project is a Gradio-based web and MCP server that automates building Docker images from remote GitHub repositories and publishes them to either the GitHub Container Registry (GHCR) or Docker Hub.

Gradio MCP lets you trigger your builds from anywhere - right from your IDE or local LLM using the MCP protocol, programmatically from your codebase or Github workflow, or via the Gradio web UI.

## The Problem

Using GitHub for CI/CD for personal projects can be frustrating, as Github's default runners are often too small and fail at even moderately complex Docker image builds due to memory constraints. And at present larger runners are only available for enterprise customers.

The HuggingFace Spaces ecosystem is ideal for this use case; you can easily choose a machine of any size and flavor you want, and it always scales to zero when not in use.

## Features

- Build Docker images from any public GitHub repository.
- Push images to either GHCR or Docker Hub.
- Use as a MCP server (for LLM/agent integration, e.g., Cursor IDE, Claude Desktop), codebase or Github workflow, or as a web app.
- Deployable on Hugging Face Spaces (scales to zero when not in use).

---

## Usage Patterns

- **Gradio Web UI:** Use the Gradio web UI to input your repo, credentials, and image details, then build and push with a click.
- **MCP Tool:** Connect from an MCP-compatible client (like Cursor IDE) and trigger builds remotely by calling the `build_and_push_image` tool, passing all required parameters (including your registry token).
- **Codebase:** Use the `build_and_push_image` tool in your codebase or Github workflow.

---

## Local Installation & Setup

1. **Clone the repository:**

   ```bash
   git clone <your-repo-url>
   cd <your-repo-directory>
   ```

2. **Install dependencies (with MCP support):**

   ```bash
   pip install "gradio[mcp]"
   ```

3. **Start the app:**
   ```bash
   python app.py
   ```
   - The web UI will be available at `http://localhost:7860`
   - The MCP server endpoint will be at `http://localhost:7860/gradio_api/mcp/sse`

---

## Using on HuggingFace Spaces

1. **Clone this repository into a new HuggingFace Space.**
2. **Set the Space hardware as needed (CPU is usually sufficient).**
3. **The app will be available at:**
   ```
   https://<your-space-username>-<your-space-name>.hf.space
   ```
4. **The MCP endpoint will be:**
   ```
   https://<your-space-username>-<your-space-name>.hf.space/gradio_api/mcp/sse
   ```
5. **You can now use the web UI or connect from an MCP client (e.g., Cursor IDE) using the MCP endpoint.**

---

## Example Usage

### Web UI

- Open the app in your browser (locally or on Spaces).
- Fill in the GitHub repo URL, registry token, image name, username, and select the registry.
- Click "Build and Push Image" to start the process and view the logs in real time.

### MCP Client (e.g., Cursor IDE, Claude Desktop)

- Connect to the MCP endpoint (see above).
- Call the tool with the required parameters, for example:

```python
build_and_push_image(
    repo_url="https://github.com/youruser/yourrepo",
    registry_token="YOUR_DOCKERHUB_OR_GHCR_TOKEN",
    image_name="your-image-name",
    username="yourusername",
    registry="Docker Hub"  # or "GitHub Container Registry (GHCR)"
)
```

Or, in natural language:

> Build and push my repo as a Docker image to Docker Hub. Use this token: `YOUR_DOCKERHUB_TOKEN`.

---

## Security Note

**Never share your registry tokens publicly.** Only use them in trusted environments.
