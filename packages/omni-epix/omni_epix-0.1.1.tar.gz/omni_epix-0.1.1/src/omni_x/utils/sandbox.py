"""Sandbox utilities for running untrusted code in Docker containers."""

import subprocess
from dataclasses import dataclass
from pathlib import Path

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
    check: bool,
    mounts: dict[Path, tuple[Path, str]] | None = None,
    env_vars: dict[str, str] | None = None,
) -> subprocess.CompletedProcess:
    """Run script in sandbox (Docker if enabled, else local uv run).

    Args:
        script: Path to Python script to run
        args: Command-line arguments to pass to script
        config: Sandbox configuration
        mounts: Dict of host_path: (container_path, mode) where mode is 'ro' or 'rw'
        env_vars: Environment variables to set in container (e.g., WANDB_API_KEY)
        check: If True, raise CalledProcessError on non-zero exit

    Returns:
        subprocess.CompletedProcess with stdout/stderr captured

    Raises:
        subprocess.CalledProcessError: If command fails and check=True
        subprocess.TimeoutExpired: If command exceeds timeout
    """
    if not config.enabled:
        cmd = ["uv", "run", "python", str(script)] + args
        return subprocess.run(cmd, capture_output=True, text=True, check=check)

    if not _image_exists(config.image):
        _build_image(config.image, config.dockerfile, config.build_context)

    cmd = ["docker", "run", "--rm"]

    if config.gpu:
        cmd.extend(["--gpus", "all"])

    cmd.extend(["--memory", config.memory_limit])
    cmd.extend(["--cpus", config.cpus])

    cmd.extend(["--network", config.network])

    # mounts
    for host_path, (container_path, mode) in (mounts or {}).items():
        host_path = host_path.resolve()  # Absolute path required
        cmd.extend(["-v", f"{host_path}:{container_path}:{mode}"])

    # env vars
    for key, val in (env_vars or {}).items():
        cmd.extend(["-e", f"{key}={val}"])

    # image and command
    cmd.append(config.image)
    cmd.extend(["python", str(script)] + args)

    return subprocess.run(cmd, capture_output=True, text=True, check=check, timeout=config.timeout)


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
