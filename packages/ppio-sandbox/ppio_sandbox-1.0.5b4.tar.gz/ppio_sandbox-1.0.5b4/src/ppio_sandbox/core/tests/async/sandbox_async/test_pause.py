import pytest
from ppio_sandbox.core import AsyncSandbox

@pytest.mark.skip_debug()
async def test_sync_pause(template):
    sbx = await AsyncSandbox.create(template, timeout=50)
    try:
        assert await sbx.is_running()
        assert sbx._envd_version is not None
        await sbx.beta_pause(sync=True)
        assert await sbx.is_running() == False
    finally:
        await sbx.kill()