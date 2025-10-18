"""Sandbox utilities for running untrusted code in Docker containers."""

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from omni_x.core import log


@dataclass
class SandboxConfig:
    """Configuration for running commands in Docker sandbox."""

    enabled: bool
    """Run in Docker (True) or locally with uv run (False)"""

    image: str
    """Docker image name, e.g., 'omni-x-minigrid:latest'"""

    dockerfile: Path
    """Path to Dockerfile for auto-build if image missing"""

    build_context: Path
    """Docker build context directory (where COPY paths are relative to)"""

    network: str
    """Docker network mode: 'bridge' for internet (wandb), 'none' for isolation"""

    memory_limit: str
    """Memory limit, e.g., '4g'"""

    cpus: str
    """CPU limit, e.g., '2' or '0-3'"""

    gpu: bool
    """Enable GPU access (--gpus all)"""

    timeout: int
    """Kill container after N seconds"""


def run_sandboxed(
    script: Path,
    args: list[str],
    config: SandboxConfig,
    log_file: Path | None,
    check: bool = True,
    mounts: dict[str | Path, tuple[str | Path, Literal["ro", "rw"]]] | None = None,
    env_vars: dict[str, str] | None = None,
) -> subprocess.CompletedProcess:
    """Run a python script in a sandbox (Docker if enabled, else local uv run).

    Args:
        code: Path to Python script to run
        args: Command-line arguments to pass to script
        config: Sandbox configuration
        log_file: Path to save stdout/stderr logs (if None, logs not saved)
        check: If True, raise CalledProcessError on non-zero exit
        mounts: Dict of host_path: (container_path, mode) where mode is 'ro' or 'rw'
        env_vars: Environment variables to set in container (e.g., WANDB_API_KEY)

    Returns:
        subprocess.CompletedProcess with stdout/stderr captured

    Raises:
        RuntimeError: If command fails (wraps CalledProcessError with log preview)
        subprocess.TimeoutExpired: If command exceeds timeout
    """

    def save_logs(info) -> None:
        if log_file is not None:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            log_file.write_text(f"=== STDOUT ===\n{info.stdout}\n\n=== STDERR ===\n{info.stderr}")

    try:
        if not config.enabled:
            cmd = ["uv", "run", "python", str(script)] + args
            result = subprocess.run(cmd, capture_output=True, text=True, check=check)
            save_logs(result)
            return result

        if not _image_exists(config.image):
            _build_image(config.image, config.dockerfile, config.build_context)

        cmd = ["docker", "run", "--rm"]

        # run container as the invoking host user to avoid root-owned artifacts
        cmd.extend(["--user", f"{os.getuid()}:{os.getgid()}"])

        if config.gpu:
            cmd.extend(["--gpus", "all"])

        cmd.extend(["--memory", config.memory_limit])
        cmd.extend(["--cpus", config.cpus])
        cmd.extend(["--network", config.network])

        for host_path, (container_path, mode) in (mounts or {}).items():
            host_path = Path(host_path).resolve()
            cmd.extend(["-v", f"{host_path}:{container_path}:{mode}"])

        for key, val in (env_vars or {}).items():
            cmd.extend(["-e", f"{key}={val}"])

        cmd.append(config.image)
        cmd.extend(["python", str(script)] + args)

        result = subprocess.run(cmd, capture_output=True, text=True, check=check, timeout=config.timeout)
        save_logs(result)
        return result

    except subprocess.CalledProcessError as e:
        save_logs(e)
        raise RuntimeError(
            f"Log: {log_file}\nExit code: {e.returncode}\nstderr (last 1000 chars):\n{(e.stderr or '')[-1000:]}"
        ) from e


def _image_exists(image: str) -> bool:
    """Check if Docker image exists locally."""
    result = subprocess.run(["docker", "images", "-q", image], capture_output=True, text=True, check=False)
    return bool(result.stdout.strip())


def _build_image(image: str, dockerfile: Path, build_context: Path) -> None:
    if not dockerfile.exists():
        raise FileNotFoundError(f"Dockerfile not found: {dockerfile}")

    log(
        "Building...",
        image=image,
        dockerfile="/".join(dockerfile.parts[-4:]),
        build_context="/".join(build_context.parts[-3:]),
    )
    _ = subprocess.run(["docker", "build", "-t", image, "-f", str(dockerfile), str(build_context)], check=True)
    log("Docker build complete.", image=image)


def get_wandb_env() -> dict[str, str]:
    """Get WandB environment variables if set."""
    env_vars = {}
    if wandb_key := os.getenv("WANDB_API_KEY"):
        env_vars["WANDB_API_KEY"] = wandb_key
    if wandb_entity := os.getenv("WANDB_ENTITY"):
        env_vars["WANDB_ENTITY"] = wandb_entity
    return env_vars
