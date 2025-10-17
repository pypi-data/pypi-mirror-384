import pytest
from ppio_sandbox.core import Sandbox


@pytest.mark.skip_debug()
def test_sync_pause(template):
    sbx = Sandbox.create(template, timeout=50)
    try:
        assert sbx.is_running()
        assert sbx._envd_version is not None
        sbx.beta_pause(sync=True)
        assert sbx.is_running() == False
    finally:
        sbx.kill()