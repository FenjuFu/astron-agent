import os
from typing import Any

from langchain_sandbox import PyodideSandbox

from workflow.configs.app_config import (
    DEFAULT_CODE_EXEC_MEMORY_LIMIT_MB,
    DEFAULT_CODE_EXEC_TIMEOUT_SEC,
    MAX_CODE_EXEC_MEMORY_LIMIT_MB,
    MAX_CODE_EXEC_TIMEOUT_SEC,
    MIN_CODE_EXEC_MEMORY_LIMIT_MB,
    MIN_CODE_EXEC_TIMEOUT_SEC,
)
from workflow.engine.nodes.code.executor.base_executor import BaseExecutor
from workflow.exception.e import CustomException
from workflow.exception.errors.err_code import CodeEnum
from workflow.extensions.otlp.trace.span import Span

MAX_ERROR_MESSAGE_LENGTH = 4096


class LangchainExecutor(BaseExecutor):
    """
    Code executor using Langchain Pyodide sandbox.

    Executes Python code in a browser-based sandbox environment using Pyodide,
    providing isolation and security through the Langchain sandbox implementation.
    """

    async def execute(
        self, language: str, code: str, timeout: int, span: Span, **kwargs: Any
    ) -> str:
        """
        Execute code using Langchain Pyodide sandbox.

        :param language: Programming language (currently only python supported)
        :param code: Code string to execute
        :param timeout: Maximum execution time in seconds
        :param span: Tracing span for logging
        :param kwargs: Additional execution parameters
        :return: Execution result as string
        :raises CustomException: If code execution fails
        """
        try:
            # Keep every Deno permission disabled.  Pyodide's default
            # node_modules read/write permissions are retained internally by the
            # official wrapper so it can load its runtime dependencies; user
            # Python code cannot access the workflow container's filesystem,
            # environment, network, subprocess, or FFI.
            sandbox = PyodideSandbox(
                allow_env=False,
                allow_read=False,
                allow_write=False,
                allow_net=False,
                allow_run=False,
                allow_ffi=False,
            )
            bounded_timeout = _bounded_timeout(timeout)
            bounded_memory_limit = _bounded_memory_limit()
            result = await sandbox.execute(
                code,
                timeout_seconds=bounded_timeout,
                memory_limit_mb=bounded_memory_limit,
            )
            if result.status == "success":
                return result.stdout if result.stdout else ""
            error_message = (result.stderr or "Code execution failed").strip()
            raise CustomException(
                err_code=(
                    CodeEnum.CODE_EXECUTION_TIMEOUT_ERROR
                    if _is_timeout_error(error_message)
                    else CodeEnum.CODE_EXECUTION_ERROR
                ),
                err_msg=error_message[:MAX_ERROR_MESSAGE_LENGTH],
            )

        except CustomException as e:
            raise e

        except Exception as e:
            raise CustomException(
                err_code=CodeEnum.CODE_EXECUTION_ERROR,
                cause_error=e,
            ) from e


def _bounded_timeout(timeout: int) -> int:
    """Normalize a requested timeout to the safe Pyodide execution range."""
    try:
        requested_timeout = int(timeout)
    except (TypeError, ValueError):
        requested_timeout = DEFAULT_CODE_EXEC_TIMEOUT_SEC
    return max(
        MIN_CODE_EXEC_TIMEOUT_SEC,
        min(requested_timeout, MAX_CODE_EXEC_TIMEOUT_SEC),
    )


def _bounded_memory_limit() -> int:
    """Read and clamp the optional Pyodide V8 heap limit."""
    # The configuration model validates this value at startup.  Reading the
    # environment here as well keeps the executor robust in tests and when a
    # process reloads configuration without rebuilding the settings object.
    try:
        requested_limit = int(
            os.getenv(
                "CODE_EXEC_MEMORY_LIMIT_MB", str(DEFAULT_CODE_EXEC_MEMORY_LIMIT_MB)
            )
        )
    except (TypeError, ValueError):
        requested_limit = DEFAULT_CODE_EXEC_MEMORY_LIMIT_MB
    return max(
        MIN_CODE_EXEC_MEMORY_LIMIT_MB,
        min(requested_limit, MAX_CODE_EXEC_MEMORY_LIMIT_MB),
    )


def _is_timeout_error(message: str) -> bool:
    """Recognize timeout diagnostics emitted by the Pyodide wrapper."""
    normalized = message.lower()
    return "timed out" in normalized or "timeout" in normalized
