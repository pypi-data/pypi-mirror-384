import tempfile
from dataclasses import dataclass
from pathlib import Path

from omni_x.core import EnvGenerator, Run, Task, log
from omni_x.utils.llm.base import InstructorClient
from omni_x.utils.llm.logging import log_llm_call
from omni_x.utils.llm.prompts import EnvOutput, build_env_fix_messages, build_env_gen_messages
from omni_x.utils.sandbox import SandboxConfig, run_sandboxed


class LLMEnvGenerator(EnvGenerator):
    """Generate environment code using an LLM.

    Uses successful parent tasks as examples, builds prompts, calls LLM, and updates the task.
    If the generated code fails smoke testing, feeds error back to LLM for up to max_fix_attempts.
    """

    @dataclass(frozen=True)
    class Config:
        substrate_description: str
        max_fix_attempts: int
        smoke_test_steps: int
        smoke_test_script: Path
        sandbox: SandboxConfig
        llm: InstructorClient.Config

    def __init__(self, config: Config) -> None:
        self.config = config
        self.client = InstructorClient(config.llm)

    def __call__(self, run: Run, task: Task) -> None:
        assert task.description is not None, "Task must have description before generating environment"  # type narrow

        parents = [run.archive.get(idx) for idx in task.parents or []]
        example_tasks = [t for t in parents if t.success is not None and t.success]

        # initial env generation
        messages = build_env_gen_messages(
            substrate_desc=self.config.substrate_description,
            task_description=task.description,
            example_tasks=example_tasks,
        )

        result, completion = self.client.create_with_completion(response_model=EnvOutput, messages=messages)
        generated_code = result.code

        metadata = log_llm_call(
            log_dir=run.dir / "llm_logs",
            task_id=task.id,
            step="env_generator",
            result=result,
            completion=completion,
        )
        task.metadata.setdefault("llm_calls", []).append(metadata)

        # smoke test loop - try to fix compile/runtime errors
        for attempt in range(self.config.max_fix_attempts):
            smoke_test_passed, error_traceback = self._run_smoke_test(generated_code)

            if smoke_test_passed:
                task.code = generated_code
                log(f"Smoke test passed attempt {attempt + 1}", run=run, task=task)
                return

            error_log_file = run.dir / "llm_logs" / f"{task.id}_smoke_test_attempt_{attempt + 1}.txt"
            error_log_file.parent.mkdir(parents=True, exist_ok=True)
            error_log_file.write_text(f"=== SMOKE TEST ERROR (Attempt {attempt + 1}) ===\n\n{error_traceback}")
            log(
                f"Smoke test failed attempt {attempt + 1}/{self.config.max_fix_attempts}, see {error_log_file.relative_to(run.dir)}",
                run=run,
                task=task,
            )

            if attempt > self.config.max_fix_attempts - 1:
                log("Max fix attempts reached. Discarding task.", run=run, task=task)
                task.done = True
                return

            fix_messages = build_env_fix_messages(
                substrate_desc=self.config.substrate_description,
                task_description=task.description,
                previous_code=generated_code,
                error_traceback=error_traceback,
                example_tasks=example_tasks,
            )

            result, completion = self.client.create_with_completion(response_model=EnvOutput, messages=fix_messages)
            generated_code = result.code

            fix_metadata = log_llm_call(
                log_dir=run.dir / "llm_logs",
                task_id=task.id,
                step=f"env_generator_fix_{attempt + 1}",
                result=result,
                completion=completion,
            )
            task.metadata.setdefault("llm_calls", []).append(fix_metadata)

    def _run_smoke_test(self, code: str) -> tuple[bool, str]:
        """Run smoke test on generated code.

        Returns:
            (success, error_traceback): success is True if smoke test passed, error_traceback contains stderr if failed
        """
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            env_file = f.name

        try:
            result = run_sandboxed(
                script=self.config.smoke_test_script,
                args=["--env-file", "/workspace/env.py", "--num-steps", str(self.config.smoke_test_steps)],
                config=self.config.sandbox,
                mounts={
                    Path(env_file): (Path("/workspace/env.py"), "ro"),
                },
                check=False,
            )
            return result.returncode == 0, result.stderr or ""
        finally:
            Path(env_file).unlink(missing_ok=True)
