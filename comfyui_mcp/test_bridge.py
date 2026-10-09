"""Tests for ComfyUI history parsing, export, and the MCP tools."""

from __future__ import annotations

import asyncio
import json
import os
import threading
import unittest
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from comfyui_mcp.comfy import (
    ComfyClient,
    ComfyError,
    execution_error,
    images_from_entry,
)
from comfyui_mcp.export import safe_filename, safe_subfolder, write_exports

PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xf0"
    b"\x50\x0f\x00\x04\x85\x01\x80\x84\xa9\x8c!\x00\x00\x00\x00IEND\xaeB`\x82"
)


class FakeComfy(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.history_payload = {}
        self.views = {}
        self.prompts = []
        self.stats = {"system": {"os": "test"}, "devices": []}
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, _format, *_args):
                return

            def _send(self, status, body, content_type="application/json"):
                data = body if isinstance(body, bytes) else body.encode()
                self.send_response(status)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def do_GET(self):
                parsed = urllib.parse.urlparse(self.path)
                if parsed.path == "/system_stats":
                    self._send(200, json.dumps(outer.stats))
                    return
                if parsed.path.startswith("/history"):
                    parts = parsed.path.split("/")
                    if len(parts) == 3 and parts[2]:
                        prompt_id = urllib.parse.unquote(parts[2])
                        entry = outer.history_payload.get(prompt_id)
                        payload = {prompt_id: entry} if entry else {}
                    else:
                        payload = outer.history_payload
                    self._send(200, json.dumps(payload))
                    return
                if parsed.path == "/view":
                    query = urllib.parse.parse_qs(parsed.query)
                    filename = query.get("filename", [""])[0]
                    body = outer.views.get(filename)
                    if body is None:
                        self._send(404, "missing")
                        return
                    self._send(200, body, "image/png")
                    return
                self._send(404, "nope")

            def do_POST(self):
                length = int(self.headers.get("Content-Length", "0"))
                raw = self.rfile.read(length)
                if self.path != "/prompt":
                    self._send(404, "nope")
                    return
                try:
                    payload = json.loads(raw.decode())
                except json.JSONDecodeError:
                    self._send(400, json.dumps({"error": "bad json"}))
                    return
                if "bad" in (payload.get("prompt") or {}):
                    self._send(400, json.dumps({"error": "node", "node_errors": {"bad": {}}}))
                    return
                outer.prompts.append(payload)
                self._send(200, json.dumps({"prompt_id": "job-1", "number": 1, "node_errors": {}}))

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.port = self.httpd.server_address[1]

    def run(self):
        self.httpd.serve_forever()

    def close(self):
        self.httpd.shutdown()
        self.httpd.server_close()


class ExportTests(unittest.TestCase):
    def test_rejects_traversal(self):
        self.assertEqual(safe_filename("../secret.png"), "secret.png")
        with self.assertRaises(ValueError):
            safe_filename("..")
        with self.assertRaises(ValueError):
            safe_subfolder("a/../../b")

    def test_writes_env_dir_and_existing_cloud_roots(self):
        home = Path(self.id().replace(".", "_"))
        root = Path("/tmp/comfyui-export-test") / home
        if root.exists():
            for child in sorted(root.rglob("*"), reverse=True):
                if child.is_file():
                    child.unlink()
                else:
                    child.rmdir()
        onedrive = root / "OneDrive"
        onedrive.mkdir(parents=True)
        gdrive = root / "Google Drive" / "My Drive"
        gdrive.mkdir(parents=True)
        env_dir = root / "explicit"
        written = set(
            write_exports(
                "tile.png",
                b"png-bytes",
                root,
                str(env_dir),
            )
        )
        self.assertEqual(
            written,
            {
                str(env_dir / "tile.png"),
                str(onedrive / "ComfyUI Output" / "tile.png"),
                str(gdrive / "ComfyUI Output" / "tile.png"),
            },
        )
        self.assertEqual((onedrive / "ComfyUI Output" / "tile.png").read_bytes(), b"png-bytes")
        self.assertEqual((gdrive / "ComfyUI Output" / "tile.png").read_bytes(), b"png-bytes")


class ComfyClientTests(unittest.TestCase):
    def setUp(self):
        self.server = FakeComfy()
        self.server.start()
        self.client = ComfyClient(f"http://127.0.0.1:{self.server.port}", timeout=5)

    def tearDown(self):
        self.server.close()

    def test_queue_returns_prompt_id_and_validation_body(self):
        ok = json.loads(self.client.queue_prompt('{"1": {"class_type": "SaveImage", "inputs": {}}}'))
        self.assertEqual(ok["prompt_id"], "job-1")
        bad = json.loads(self.client.queue_prompt('{"bad": {"class_type": "Nope"}}'))
        self.assertIn("node_errors", bad)

    def test_system_stats(self):
        stats = json.loads(self.client.system_stats())
        self.assertEqual(stats["system"]["os"], "test")

    def test_wait_then_view(self):
        self.server.history_payload["job-1"] = {
            "outputs": {
                "9": {
                    "images": [
                        {"filename": "z-image-turbo_00001_.png", "subfolder": "", "type": "output"}
                    ]
                }
            },
            "status": {"completed": True, "status_str": "success", "messages": []},
        }
        self.server.views["z-image-turbo_00001_.png"] = PNG
        entry = self.client.wait_for_entry("job-1", timeout=2)
        images = images_from_entry(entry)
        self.assertEqual(images[0]["filename"], "z-image-turbo_00001_.png")
        self.assertTrue(self.client.view(images[0]["filename"]).startswith(b"\x89PNG"))

    def test_execution_error_stops_the_wait(self):
        self.server.history_payload["job-err"] = {
            "outputs": {},
            "status": {
                "completed": True,
                "status_str": "error",
                "messages": [["execution_error", {"exception_message": "out of memory"}]],
            },
        }
        with self.assertRaises(ComfyError) as caught:
            self.client.wait_for_entry("job-err", timeout=2)
        self.assertIn("out of memory", str(caught.exception))
        self.assertEqual(execution_error(self.server.history_payload["job-err"]), "out of memory")


class ToolTests(unittest.TestCase):
    def setUp(self):
        self.server = FakeComfy()
        self.server.start()
        self.server.history_payload["job-1"] = {
            "outputs": {
                "9": {
                    "images": [
                        {"filename": "floor.png", "subfolder": "tiles", "type": "output"}
                    ]
                }
            },
            "status": {"completed": True, "status_str": "success", "messages": []},
        }
        self.server.views["floor.png"] = PNG
        self._env = {
            "COMFYUI_URL": f"http://127.0.0.1:{self.server.port}",
            "COMFYUI_EXPORT_DIR": "/tmp/comfyui-mcp-tool-export",
            "COMFYUI_WAIT_SECONDS": "2",
        }
        self._previous = {key: os.environ.get(key) for key in self._env}
        os.environ.update(self._env)
        export_dir = Path(self._env["COMFYUI_EXPORT_DIR"])
        if export_dir.exists():
            for child in export_dir.glob("*"):
                child.unlink()

    def tearDown(self):
        self.server.close()
        for key, value in self._previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_check_output_returns_image_and_writes_export(self):
        from fastmcp import Client

        from comfyui_mcp.server import mcp

        async def run():
            async with Client(mcp) as client:
                result = await client.call_tool_mcp("check_output", {"prompt_id": "job-1"})
            return result

        result = asyncio.run(run())
        types = [block.type for block in result.content]
        self.assertIn("text", types)
        self.assertIn("image", types)
        summary = json.loads(next(block.text for block in result.content if block.type == "text"))
        self.assertEqual(summary["images"][0]["filename"], "floor.png")
        exported = Path("/tmp/comfyui-mcp-tool-export/floor.png")
        self.assertEqual(exported.read_bytes(), PNG)


if __name__ == "__main__":
    unittest.main()
