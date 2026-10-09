"""Small ComfyUI HTTP client used by the MCP bridge."""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

_PROMPT_ID = re.compile(r"[A-Za-z0-9_-]+")
_FOLDER_TYPES = {"output", "input", "temp"}


class ComfyError(RuntimeError):
    """ComfyUI rejected a call or a job failed."""


def normalize_base_url(url: str) -> str:
    return url.rstrip("/")


def validate_prompt_id(prompt_id: str) -> str:
    if not prompt_id or not _PROMPT_ID.fullmatch(prompt_id):
        raise ValueError(f"invalid prompt_id: {prompt_id!r}")
    return prompt_id


def validate_folder_type(folder_type: str) -> str:
    if folder_type not in _FOLDER_TYPES:
        raise ValueError(f"invalid folder type: {folder_type!r}")
    return folder_type


def image_format(filename: str) -> str:
    suffix = filename.rsplit(".", 1)[-1].lower() if "." in filename else "png"
    if suffix == "jpeg":
        return "jpg"
    if suffix in {"png", "jpg", "webp", "gif"}:
        return suffix
    return "png"


def images_from_entry(entry: dict[str, Any]) -> list[dict[str, str]]:
    images: list[dict[str, str]] = []
    outputs = entry.get("outputs") or {}
    if not isinstance(outputs, dict):
        return images
    for node_output in outputs.values():
        if not isinstance(node_output, dict):
            continue
        for image in node_output.get("images") or []:
            if isinstance(image, dict) and image.get("filename"):
                images.append(
                    {
                        "filename": str(image.get("filename")),
                        "subfolder": str(image.get("subfolder") or ""),
                        "type": str(image.get("type") or "output"),
                    }
                )
    return images


def execution_error(entry: dict[str, Any]) -> str | None:
    status = entry.get("status") or {}
    if not isinstance(status, dict):
        return None
    messages = status.get("messages") or []
    if isinstance(messages, list):
        for message in messages:
            if (
                isinstance(message, list)
                and len(message) >= 2
                and message[0] == "execution_error"
                and isinstance(message[1], dict)
            ):
                detail = message[1]
                text = detail.get("exception_message") or detail.get("exception_type")
                if text:
                    return str(text)
    if status.get("status_str") == "error":
        return "ComfyUI execution failed"
    return None


def history_entry(payload: Any, prompt_id: str) -> dict[str, Any] | None:
    """Accept either `{prompt_id: entry}` or a bare entry."""
    if not isinstance(payload, dict) or not payload:
        return None
    if prompt_id in payload and isinstance(payload[prompt_id], dict):
        return payload[prompt_id]
    if "outputs" in payload or "status" in payload:
        return payload
    return None


class ComfyClient:
    def __init__(self, base_url: str, timeout: float = 60):
        self.base_url = normalize_base_url(base_url)
        self.timeout = timeout

    def request(
        self,
        method: str,
        path: str,
        body: bytes | None = None,
        content_type: str | None = None,
    ) -> tuple[int, bytes]:
        headers = {}
        if content_type:
            headers["Content-Type"] = content_type
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=body,
            headers=headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return response.status, response.read()
        except urllib.error.HTTPError as error:
            return error.code, error.read()

    def queue_prompt(self, prompt_workflow_json: str) -> str:
        try:
            workflow = json.loads(prompt_workflow_json)
        except json.JSONDecodeError as error:
            raise ComfyError(f"prompt_workflow_json is not valid JSON: {error}") from error
        if not isinstance(workflow, dict):
            raise ComfyError("prompt_workflow_json must be a JSON object")
        payload = json.dumps({"prompt": workflow}).encode()
        _status, body = self.request("POST", "/prompt", payload, "application/json")
        return body.decode()

    def system_stats(self) -> str:
        status, body = self.request("GET", "/system_stats")
        if status != 200:
            raise ComfyError(body.decode(errors="replace"))
        return body.decode()

    def history(self, prompt_id: str = "") -> dict[str, Any]:
        path = "/history"
        if prompt_id:
            path = f"/history/{urllib.parse.quote(validate_prompt_id(prompt_id))}"
        status, body = self.request("GET", path)
        if status != 200:
            raise ComfyError(body.decode(errors="replace"))
        payload = json.loads(body.decode() or "{}")
        if not isinstance(payload, dict):
            raise ComfyError("ComfyUI history was not a JSON object")
        return payload

    def view(self, filename: str, subfolder: str = "", folder_type: str = "output") -> bytes:
        from comfyui_mcp.export import safe_filename, safe_subfolder

        query = urllib.parse.urlencode(
            {
                "filename": safe_filename(filename),
                "subfolder": safe_subfolder(subfolder),
                "type": validate_folder_type(folder_type),
            }
        )
        status, body = self.request("GET", f"/view?{query}")
        if status != 200:
            raise ComfyError(body.decode(errors="replace") or f"view failed with HTTP {status}")
        return body

    def wait_for_entry(self, prompt_id: str, timeout: float, poll_interval: float = 0.5) -> dict[str, Any]:
        prompt_id = validate_prompt_id(prompt_id)
        deadline = time.monotonic() + timeout
        while True:
            payload = self.history(prompt_id)
            entry = history_entry(payload, prompt_id)
            if entry:
                error = execution_error(entry)
                if error:
                    raise ComfyError(error)
                status = entry.get("status") if isinstance(entry.get("status"), dict) else {}
                if images_from_entry(entry) or status.get("completed") or status.get("status_str") == "success":
                    return entry
            if time.monotonic() >= deadline:
                raise ComfyError(f"timed out waiting for prompt {prompt_id}")
            time.sleep(poll_interval)
