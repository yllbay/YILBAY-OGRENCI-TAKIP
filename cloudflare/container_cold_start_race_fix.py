from __future__ import annotations

import sys
from pathlib import Path


MARKER = "GENESIS_CONTAINER_COLD_START_COALESCED_V1"
METHOD = "async startContainerIfNotRunning(waitOptions, options) {"
LOCKED_METHOD = "async doStartContainer(waitOptions, options) {"


def patch_source(source: str) -> tuple[str, str]:
    if MARKER in source:
        return source, "already-patched"

    if "this.startInFlight" in source:
        # Recent upstream SDK bundles already carry this race fix.
        if source.count(METHOD) != 1:
            raise ValueError("Found startInFlight but not the known start helper")
        return source.replace(
            METHOD,
            f"// {MARKER}: upstream start coalescing is present\n  {METHOD}",
            1,
        ), "upstream-patched"

    if source.count(METHOD) != 1:
        raise ValueError(
            "Expected exactly one known startContainerIfNotRunning method; "
            "refusing to patch an unfamiliar SDK bundle"
        )
    if LOCKED_METHOD in source:
        raise ValueError("The start helper rename target already exists")

    wrapper = f'''async startContainerIfNotRunning(waitOptions, options) {{
    // {MARKER}: all concurrent cold-start callers share one start result.
    if (this.startInFlight) return this.startInFlight;
    const startPromise = this.doStartContainer(waitOptions, options);
    this.startInFlight = startPromise;
    try {{
      return await startPromise;
    }} finally {{
      if (this.startInFlight === startPromise) this.startInFlight = undefined;
    }}
  }}
  {LOCKED_METHOD}'''
    return source.replace(METHOD, wrapper, 1), "installed"


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: container_cold_start_race_fix.py <worker-bundle.js>")

    path = Path(sys.argv[1])
    source = path.read_text(encoding="utf-8")
    patched, result = patch_source(source)
    if patched.count(MARKER) != 1:
        raise SystemExit("Cold-start coalescing marker was not installed uniquely")
    if result != "upstream-patched":
        if patched.count(METHOD) != 1 or patched.count(LOCKED_METHOD) != 1:
            raise SystemExit("Cold-start helper structure failed post-patch validation")
    else:
        if patched.count(METHOD) != 1:
            raise SystemExit("Upstream cold-start helper structure failed validation")

    if patched != source:
        path.write_text(patched, encoding="utf-8")
    if result == "installed":
        print("GENESIS container cold-start race coalescing installed")
    elif result == "upstream-patched":
        print("GENESIS container cold-start coalescing already present upstream")
    else:
        print("GENESIS container cold-start coalescing already present")


if __name__ == "__main__":
    main()
