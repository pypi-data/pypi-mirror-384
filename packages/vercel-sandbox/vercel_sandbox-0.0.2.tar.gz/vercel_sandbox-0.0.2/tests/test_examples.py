from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path


async def run_example(script_path: Path, sem: asyncio.Semaphore) -> tuple[Path, int, str, str]:
    async with sem:
        print("Running", script_path.name)
        env = {**os.environ, "CI": "1"}
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            str(script_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        try:
            stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=180.0)
            returncode = proc.returncode if proc.returncode is not None else -1
        except asyncio.TimeoutError:
            proc.kill()
            try:
                await proc.wait()
            except Exception:
                pass
            stdout_b, stderr_b = b"", b"Timed out"
            returncode = -1

        stdout = stdout_b.decode(errors="replace")
        stderr = stderr_b.decode(errors="replace")
        return script_path, returncode, stdout, stderr


async def async_test_examples_run() -> None:
    examples_dir = Path(__file__).resolve().parents[1] / "examples"
    assert examples_dir.is_dir()

    example_files = [p for p in examples_dir.iterdir() if p.is_file() and p.suffix == ".py"]
    assert example_files, "No example .py files found in examples/"

    max_concurrency = min(10, len(example_files))
    sem = asyncio.Semaphore(max_concurrency)

    tasks = [run_example(p, sem) for p in example_files]
    results = await asyncio.gather(*tasks)

    failures: list[str] = []
    for script_path, returncode, stdout, stderr in results:
        print(f"{script_path.name} returned {returncode}")
        if returncode != 0:
            failures.append(
                f"{script_path.name} failed with code {returncode}\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}"
            )

    assert not failures, "\n\n".join(failures)

    print("All examples ran successfully")


def test_examples_run() -> None:
    asyncio.run(async_test_examples_run())


if __name__ == "__main__":
    test_examples_run()
