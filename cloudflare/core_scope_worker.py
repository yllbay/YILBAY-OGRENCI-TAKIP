"""Disable the legacy GENESIS edge home launcher.

The native home dashboard is the only home UI source. This transform removes any
previous V1-V4 injected overlay payload from the live Worker without touching
container data, DB or R2.
"""
import re

MARKER = "GENESIS_EDGE_HOME_OVERLAY_DISABLED_V5"
DISABLED = '<!-- GENESIS_HOME_DASHBOARD_EDGE_V1 GENESIS_EDGE_HOME_OVERLAY_DISABLED_V5 -->'

def patch(module: bytes) -> bytes:
    text = module.decode("utf-8")
    if MARKER in text and 'id="genesisCoreHomeLauncher"' not in text and 'id="edgeHomeQuestionStudio"' not in text:
        return module
    if "GENESIS_HOME_DASHBOARD_EDGE_V1" not in text:
        raise RuntimeError("GENESIS edge home marker missing")

    pattern = re.compile(r'<style id="genesisHomeDashboardEdgeStyle">.*?</script>', re.S)
    text, count = pattern.subn(DISABLED, text, count=1)
    if count != 1:
        raise RuntimeError(f"GENESIS edge overlay removal failed: {count}")

    assert MARKER in text
    assert 'id="genesisCoreHomeLauncher"' not in text
    assert 'id="edgeHomeQuestionStudio"' not in text
    assert 'MutationObserver(sync)' not in text
    return text.encode("utf-8")
