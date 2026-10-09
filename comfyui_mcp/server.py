"""MCP bridge: queue ComfyUI, then fetch and archive the images."""

from __future__ import annotations

import json
import os
from pathlib import Path

from fastmcp import FastMCP
from fastmcp.utilities.types import Image

from comfyui_mcp.comfy import ComfyClient, image_format, images_from_entry
from comfyui_mcp.export import write_exports

mcp = FastMCP(
    "ComfyUI-Bridge",
    version="4.2.0",
    instructions=(
        "Queue ComfyUI workflows, then use check_output with the prompt_id "
        "to view the image. Finished files are copied to OneDrive or Google Drive."
    ),
)


def _client() -> ComfyClient:
    return ComfyClient(os.environ.get("COMFYUI_URL", "http://127.0.0.1:8188"))


def _export(filename: str, data: bytes) -> list[str]:
    return write_exports(
        filename,
        data,
        Path.home(),
        os.environ.get("COMFYUI_EXPORT_DIR"),
    )


def _image_block(filename: str, data: bytes) -> Image:
    return Image(data=data, format=image_format(filename))


@mcp.tool
def queue_prompt(prompt_workflow_json: str) -> str:
    """Queue a prompt workflow JSON to the local ComfyUI engine."""
    return _client().queue_prompt(prompt_workflow_json)


@mcp.tool
def check_system_stats() -> str:
    """Check ComfyUI system stats and hardware utilization."""
    return _client().system_stats()


@mcp.tool
def get_history(prompt_id: str = "") -> str:
    """Return ComfyUI history. Pass prompt_id for one job, or omit it for the recent history."""
    return json.dumps(_client().history(prompt_id))


@mcp.tool
def get_image(filename: str, subfolder: str = "", folder_type: str = "output") -> list:
    """Fetch one saved ComfyUI image and copy it to OneDrive or Google Drive when available."""
    data = _client().view(filename, subfolder, folder_type)
    paths = _export(filename, data)
    summary = json.dumps(
        {"filename": filename, "subfolder": subfolder, "type": folder_type, "exported_to": paths}
    )
    return [summary, _image_block(filename, data)]


@mcp.tool
def check_output(prompt_id: str) -> list:
    """Wait for a queued prompt, return its images, and copy them to OneDrive or Google Drive."""
    timeout = float(os.environ.get("COMFYUI_WAIT_SECONDS", "300"))
    entry = _client().wait_for_entry(prompt_id, timeout=timeout)
    images = images_from_entry(entry)
    if not images:
        raise RuntimeError(f"prompt {prompt_id} finished without images")
    blocks: list = []
    exported = []
    for image in images:
        data = _client().view(image["filename"], image["subfolder"], image["type"])
        paths = _export(image["filename"], data)
        exported.append({**image, "exported_to": paths})
        blocks.append(_image_block(image["filename"], data))
    summary = json.dumps({"prompt_id": prompt_id, "images": exported})
    return [summary, *blocks]


def main() -> None:
    host = os.environ.get("COMFYUI_BRIDGE_HOST", "127.0.0.1")
    port = int(os.environ.get("COMFYUI_BRIDGE_PORT", "8765"))
    mcp.run(transport="sse", host=host, port=port)


if __name__ == "__main__":
    main()
