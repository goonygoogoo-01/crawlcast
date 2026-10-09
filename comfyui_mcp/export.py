"""Copy finished ComfyUI images into OneDrive or Google Drive folders."""

from __future__ import annotations

import os
import string
from pathlib import Path


OUTPUT_DIR_NAME = "ComfyUI Output"


def safe_filename(filename: str) -> str:
    """Return a single path segment, rejecting traversal."""
    name = os.path.basename(filename.replace("\\", "/"))
    if not name or name in {".", ".."}:
        raise ValueError(f"invalid filename: {filename!r}")
    return name


def safe_subfolder(subfolder: str) -> str:
    """Return a relative subfolder, rejecting absolute paths and '..'."""
    if not subfolder:
        return ""
    normalized = subfolder.replace("\\", "/").strip("/")
    parts = [part for part in normalized.split("/") if part not in {"", "."}]
    if any(part == ".." for part in parts):
        raise ValueError(f"invalid subfolder: {subfolder!r}")
    return "/".join(parts)


def cloud_roots(home: Path, drive_letters: list[str] | None = None) -> list[Path]:
    """Find OneDrive and Google Drive roots that already exist."""
    roots: list[Path] = []
    if home.is_dir():
        for child in sorted(home.iterdir(), key=lambda path: path.name):
            if not child.is_dir():
                continue
            name = child.name
            if name == "OneDrive" or name.startswith("OneDrive "):
                roots.append(child)
                continue
            if name == "My Drive":
                roots.append(child)
                continue
            if name == "Google Drive":
                my_drive = child / "My Drive"
                roots.append(my_drive if my_drive.is_dir() else child)

    letters = drive_letters
    if letters is None and os.name == "nt":
        letters = list(string.ascii_uppercase)
    for letter in letters or []:
        candidate = Path(f"{letter}:/My Drive")
        if candidate.is_dir():
            roots.append(candidate)
    return roots


def export_directories(
    home: Path,
    env_value: str | None = None,
    drive_letters: list[str] | None = None,
) -> list[Path]:
    """Directories that should receive a copy of each finished image."""
    directories: list[Path] = []
    if env_value:
        directories.append(Path(env_value).expanduser())
    for root in cloud_roots(home, drive_letters):
        directories.append(root / OUTPUT_DIR_NAME)

    unique: list[Path] = []
    seen: set[str] = set()
    for directory in directories:
        key = str(directory)
        if key not in seen:
            seen.add(key)
            unique.append(directory)
    return unique


def write_exports(
    filename: str,
    data: bytes,
    home: Path,
    env_value: str | None = None,
    drive_letters: list[str] | None = None,
) -> list[str]:
    """Write image bytes to each available export directory.

    `COMFYUI_EXPORT_DIR` is created when it is set. Cloud copies are written
    only when the OneDrive or Google Drive root already exists.
    """
    name = safe_filename(filename)
    written: list[str] = []
    for directory in export_directories(home, env_value, drive_letters):
        explicit = bool(env_value) and directory == Path(env_value).expanduser()
        if explicit:
            directory.mkdir(parents=True, exist_ok=True)
        elif not directory.parent.is_dir():
            continue
        else:
            directory.mkdir(exist_ok=True)
        path = directory / name
        path.write_bytes(data)
        written.append(str(path))
    return written
