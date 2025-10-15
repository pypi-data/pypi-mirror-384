from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Optional, Sequence

LAMMY_MARKER = "Lammy"


def sanitize_alias(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9-]+", "-", value.strip().lower())
    normalized = re.sub(r"-{2,}", "-", normalized).strip("-")
    return normalized or "vm"


def default_alias(prefix: str, name: str, fallback: str) -> str:
    slug = sanitize_alias(name) if name else sanitize_alias(fallback)
    return f"{prefix}-{slug}"


def ensure_ssh_entry(
    alias: str,
    hostname: str,
    *,
    user: str = "ubuntu",
    identity_file: Optional[str] = None,
    port: int = 22,
    config_path: Optional[Path] = None,
) -> Path:
    target_path = config_path or (Path.home() / ".ssh" / "config")
    target_path.parent.mkdir(parents=True, exist_ok=True)
    marker_start = f"# {LAMMY_MARKER} {alias} start"
    marker_end = f"# {LAMMY_MARKER} {alias} end"

    lines = [marker_start, f"Host {alias}", f"  HostName {hostname}", f"  User {user}"]
    if port and port != 22:
        lines.append(f"  Port {port}")
    if identity_file:
        expanded = Path(identity_file).expanduser()
        lines.append(f"  IdentityFile {expanded}")
        lines.append("  IdentitiesOnly yes")
    lines.extend(
        [
            "  ServerAliveInterval 60",
            "  ServerAliveCountMax 5",
            "  StrictHostKeyChecking accept-new",
            marker_end,
            "",
        ]
    )
    entry = "\n".join(lines)

    if target_path.exists():
        try:
            original = target_path.read_text(encoding="utf-8")
        except OSError:
            original = ""
    else:
        original = ""

    pattern = re.compile(
        rf"{re.escape(marker_start)}\n.*?{re.escape(marker_end)}\n?",
        flags=re.DOTALL,
    )
    updated = pattern.sub("", original).strip()
    if updated:
        updated += "\n\n" + entry
    else:
        updated = entry

    tmp_path = target_path.with_suffix(".tmp")
    with tmp_path.open("w", encoding="utf-8") as handle:
        handle.write(updated.strip() + "\n")
    os.replace(tmp_path, target_path)
    try:
        os.chmod(target_path, 0o600)
    except OSError:
        pass
    return target_path


def ssh_command(alias: str, extra_args: Optional[Sequence[str]] = None) -> Sequence[str]:
    args: list[str] = ["ssh", alias]
    if extra_args:
        args.extend(extra_args)
    return args


def open_ssh_session(alias: str, *, extra_args: Optional[Sequence[str]] = None) -> int:
    cmd = ssh_command(alias, extra_args)
    try:
        proc = subprocess.run(cmd, check=False)
    except FileNotFoundError as exc:
        raise RuntimeError("ssh command not found on PATH") from exc
    return proc.returncode
