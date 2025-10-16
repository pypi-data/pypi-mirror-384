import pytest

from ppio_sandbox.core import Sandbox
from ppio_sandbox.core.sandbox.sandbox_api import SandboxQuery, SandboxState
import time


@pytest.mark.skip_debug()
def test_start(template):
    sbx = Sandbox.create(template, timeout=5)
    try:
        assert sbx.is_running()
        assert sbx._envd_version is not None
    finally:
        sbx.kill()


@pytest.mark.skip_debug()
def test_metadata(template):
    sbx = Sandbox.create(template, timeout=5, metadata={"test-key": "test-value"})

    try:
        paginator = Sandbox.list(
            query=SandboxQuery(metadata={"test-key": "test-value"})
        )
        sandboxes = paginator.next_items()

        for sbx_info in sandboxes:
            if sbx.sandbox_id == sbx_info.sandbox_id:
                assert sbx_info.metadata is not None
                assert sbx_info.metadata["test-key"] == "test-value"
                break
        else:
            assert False, "Sandbox not found"
    finally:
        sbx.kill()


@pytest.mark.skip_debug()
def test_start_with_node_id(template):
    target_node_id = "2e554595"
    sbx = Sandbox.create(template, timeout=5, node_id=target_node_id)
    node_id = sbx.sandbox_id.split("-")[1]
    try:
        assert target_node_id == node_id
    finally:
        sbx.kill()


@pytest.mark.skip_debug()
def test_start_with_auto_pause(template):
    sbx = Sandbox.create(template, timeout=3, auto_pause=True, metadata={"test-auto-pause": "1"})
    sandbox_id = sbx.sandbox_id.split("-")[0]
    # wait for the sandbox to auto pause
    time.sleep(5)
    try:
        paginator = Sandbox.list(
            query=SandboxQuery(state=[SandboxState.PAUSED], metadata={"test-auto-pause": "1"})
        )
        sandboxes = paginator.next_items()
        exists = any(s.sandbox_id.startswith(sandbox_id) for s in sandboxes)
        assert exists
    finally:
        sbx.kill()
