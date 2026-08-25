from pathlib import Path

import pytest

from workflow.configs.app_config import CodeExecutorConfig
from workflow.engine.nodes.code.executor.base_executor import CodeExecutorFactory
from workflow.engine.nodes.code.executor.local.local_executor import LocalExecutor
from workflow.exception.e import CustomException


@pytest.mark.parametrize("executor_type", ["", "disabled", "local"])
def test_unsafe_or_missing_executor_fails_closed(executor_type: str) -> None:
    with pytest.raises(CustomException, match="local executor is disabled"):
        CodeExecutorFactory.create_executor(executor_type)


def test_code_executor_configuration_defaults_to_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("CODE_EXEC_TYPE", raising=False)

    assert CodeExecutorConfig().exec_type == "disabled"


@pytest.mark.asyncio
async def test_local_executor_never_executes_submitted_code(tmp_path: Path) -> None:
    marker = tmp_path / "must-not-exist"
    submitted_code = f"open({str(marker)!r}, 'w').write('executed')"

    with pytest.raises(CustomException, match="disabled for security"):
        await LocalExecutor().execute(
            language="python",
            code=submitted_code,
            timeout=1,
            span=None,  # type: ignore[arg-type]
        )

    assert not marker.exists()
    assert not hasattr(LocalExecutor, "_safe_exec")
