
import os
import sys
import time
import subprocess
import tempfile

from pathlib import Path
from pydantic import BaseModel, ConfigDict, Field

from app.tools.registry import register_tool


# ---------------------------------
# 1. Argument Validation
# ---------------------------------

class PythonExecutorArgs(BaseModel):

    model_config = ConfigDict(
        strict=True,
        extra="forbid"
    )

    code: str = Field(
        min_length=1,
        max_length=10000
    )

    timeout_seconds: int = Field(
        default=5,
        ge=1,
        le=10
    )


# ---------------------------------
# 2. Output Configuration
# ---------------------------------

MAX_OUTPUT_CHARS = 4000
MAX_OUTPUT_BYTES = 1024 * 1024  # 1 MB


def limit_output(output: str) -> str:

    if len(output) > MAX_OUTPUT_CHARS:
        return (
            output[:MAX_OUTPUT_CHARS]
            + "\n... OUTPUT TRUNCATED ..."
        )

    return output


# ---------------------------------
# 3. Process Termination
# ---------------------------------

def terminate_process(process):

    if process.poll() is not None:
        return

    if os.name == "nt":

        try:
            subprocess.run(
                [
                    "taskkill",
                    "/PID",
                    str(process.pid),
                    "/T",
                    "/F"
                ],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5,
                check=False
            )

        except (subprocess.TimeoutExpired, OSError):
            # Fallback if taskkill fails.
            try:
                process.kill()
            except OSError:
                pass

    else:
        try:
            process.kill()
        except OSError:
            pass

    try:
        process.wait(timeout=5)

    except subprocess.TimeoutExpired:
        try:
            process.kill()
        except OSError:
            pass

        process.wait()


# ---------------------------------
# 4. Python Executor
# ---------------------------------

@register_tool(
    "python_executor",
    PythonExecutorArgs,
    requires_approval=True
)
def python_executor(
    code: str,
    timeout_seconds: int = 5
) -> dict:

    # Validate arguments even when called directly.
    args = PythonExecutorArgs(
        code=code,
        timeout_seconds=timeout_seconds
    )

    start_time = time.perf_counter()

    with tempfile.TemporaryDirectory(
        prefix="autoagent_"
    ) as working_dir:

        child_env = {
            key: os.environ[key]
            for key in (
                "PATH",
                "SystemRoot",
                "WINDIR",
                "TEMP",
                "TMP"
            )
            if key in os.environ
        }

        stdout_path = Path(working_dir) / "stdout.txt"
        stderr_path = Path(working_dir) / "stderr.txt"

        process = None

        try:

            with open(stdout_path, "wb") as stdout_file, \
                 open(stderr_path, "wb") as stderr_file:

                process = subprocess.Popen(
                    [
                        sys.executable,
                        "-I",
                        "-S",
                        "-c",
                        args.code
                    ],
                    cwd=working_dir,
                    env=child_env,
                    stdin=subprocess.DEVNULL,
                    stdout=stdout_file,
                    stderr=stderr_file,
                    shell=False
                )

                # Monitor execution.
                while process.poll() is None:

                    elapsed = time.perf_counter() - start_time

                    if elapsed > args.timeout_seconds:

                        terminate_process(process)

                        raise TimeoutError(
                            f"Python execution exceeded "
                            f"{args.timeout_seconds} seconds"
                        )

                    output_size = (
                        stdout_path.stat().st_size
                        + stderr_path.stat().st_size
                    )

                    if output_size > MAX_OUTPUT_BYTES:

                        terminate_process(process)

                        raise RuntimeError(
                            "Python execution exceeded "
                            "the 1 MB output limit"
                        )

                    time.sleep(0.05)

                return_code = process.returncode

            # Check output size once more after process completion.
            output_size = (
                stdout_path.stat().st_size
                + stderr_path.stat().st_size
            )

            if output_size > MAX_OUTPUT_BYTES:

                raise RuntimeError(
                    "Python execution exceeded "
                    "the 1 MB output limit"
                )

            stdout = stdout_path.read_bytes().decode(
                "utf-8",
                errors="replace"
            )

            stderr = stderr_path.read_bytes().decode(
                "utf-8",
                errors="replace"
            )

            # Remove only trailing newline characters.
            stdout = stdout.rstrip("\r\n")
            stderr = stderr.rstrip("\r\n")

            duration = time.perf_counter() - start_time

            return {
                "status": (
                    "success"
                    if return_code == 0
                    else "error"
                ),
                "stdout": limit_output(stdout),
                "stderr": limit_output(stderr),
                "return_code": return_code,
                "execution_time": round(duration, 4)
            }

        except subprocess.TimeoutExpired as exc:

            if process is not None:
                terminate_process(process)

            raise TimeoutError(
                "Python execution timed out"
            ) from exc


# ---------------------------------
# 5. Test Python Executor
# ---------------------------------

if __name__ == "__main__":

    code = """
numbers = [10, 20, 30, 40, 50]

result = sum(numbers)

print("Numbers:", numbers)
print("Sum:", result)
"""

    result = python_executor(
        code=code,
        timeout_seconds=5
    )

    print("\nExecution Result:")
    print("Status:", result["status"])
    print("Output:", result["stdout"])
    print("Error:", result["stderr"])
    print("Return Code:", result["return_code"])
    print("Execution Time:", result["execution_time"])
