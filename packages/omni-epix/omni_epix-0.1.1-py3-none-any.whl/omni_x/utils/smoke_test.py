"""General smoke test script for validating environments that follow the BaseEnv protocol.

This script validates that a generated environment:
1. Can be loaded and instantiated
2. Implements the BaseEnv protocol
3. Can successfully reset and step through episodes
4. Has a working get_success() method

This is substrate-agnostic and doesn't apply any wrappers.
Might require some environment-specific dependencies to be installed.
"""

import sys
import traceback
from dataclasses import dataclass

import tyro

from omni_x.utils.env import load_env_class_from_file, BaseEnv


@dataclass
class Args:
    env_file: str
    """Path to Python file containing environment class"""
    num_steps: int = 20
    """Number of steps to run with random policy"""


if __name__ == "__main__":
    args = tyro.cli(Args)
    try:
        Env = load_env_class_from_file(args.env_file)
        env: BaseEnv = Env()
        _, _ = env.reset()
        for step in range(args.num_steps):
            action = env.action_space.sample()
            _, _, terminated, truncated, _ = env.step(action)

            if terminated or truncated:
                _, _ = env.reset()
        _ = env.get_success()

        if hasattr(env, "close"):
            env.close()  # type: ignore[attr-defined]

        print(f"Smoke test passed: {args.num_steps} steps completed successfully", file=sys.stdout)
        sys.exit(0)
    except Exception:
        # Print full traceback to stderr for LLM feedback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)
