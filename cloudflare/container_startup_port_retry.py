from __future__ import annotations

import re
import sys
from pathlib import Path


MARKER = "GENESIS_CONTAINER_STARTING_PORT_RETRY_V1"
METHOD = "async startContainerIfNotRunning(waitOptions, options) {"
PORT_LOOKUP = re.compile(
    r"const port = this\.container\.getTcpPort\(waitOptions\.portToCheck\);\s*try \{"
)


def patch_source(source: str) -> tuple[str, str]:
    if MARKER in source:
        if source.count(MARKER) != 1 or PORT_LOOKUP.search(source):
            raise ValueError("Existing startup retry marker has an invalid helper shape")
        return source, "already-patched"

    if source.count(METHOD) != 1:
        raise ValueError(
            "Expected exactly one known startContainerIfNotRunning method; "
            "refusing to patch an unfamiliar SDK bundle"
        )
    if len(PORT_LOOKUP.findall(source)) != 1:
        raise ValueError(
            "Expected one container-start port lookup outside its retry catch"
        )

    retryable_lookup = (
        f"try {{ /* {MARKER}: retry transient not-running while start is provisioning */\n"
        "        const port = this.container.getTcpPort(waitOptions.portToCheck);"
    )
    patched = PORT_LOOKUP.sub(retryable_lookup, source, count=1)
    return patched, "installed"


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: container_startup_port_retry.py <worker-bundle.js>")

    path = Path(sys.argv[1])
    source = path.read_text(encoding="utf-8")
    patched, result = patch_source(source)
    if patched.count(MARKER) != 1 or PORT_LOOKUP.search(patched):
        raise SystemExit("Startup port lookup is not inside the SDK retry catch")
    if patched.count(METHOD) != 1:
        raise SystemExit("Container startup helper structure failed validation")

    if patched != source:
        path.write_text(patched, encoding="utf-8")
    if result == "installed":
        print("GENESIS transient startup port lookup retry installed")
    else:
        print("GENESIS transient startup port lookup retry already present")


if __name__ == "__main__":
    main()
