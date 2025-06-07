import gradio as gr

def build_and_push_image(repo_url, github_token, image_name=None):
    """
    Clones a GitHub repository, builds a Docker image, and pushes it to GitHub Container Registry (GHCR).

    Args:
        repo_url (str): URL of the GitHub repository.
        github_token (str): GitHub Personal Access Token with appropriate scopes.
        image_name (str, optional): Desired name for the Docker image.

    Returns:
        str: Status message indicating success or failure.
    """
    # Implementation of cloning, building, and pushing the Docker image
    # ...
    return "Image built and pushed successfully."

with gr.Blocks() as demo:
    gr.Markdown("# Docker Builder MCP Server")
    repo_url = gr.Textbox(label="GitHub Repository URL")
    github_token = gr.Textbox(label="GitHub Token", type="password")
    image_name = gr.Textbox(label="Image Name (optional)")
    output = gr.Textbox(label="Output")
    build_button = gr.Button("Build and Push Image")

    build_button.click(
        fn=build_and_push_image,
        inputs=[repo_url, github_token, image_name],
        outputs=output
    )

demo.launch(mcp_server=True)
