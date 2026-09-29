from __future__ import annotations

import re
import sys
from pathlib import Path


MARKER = "GENESIS_CONTAINER_STARTING_PORT_RETRY_V1"
WAIT_MARKER = "GENESIS_WAIT_FOR_PORT_STARTING_RETRY_V1"
METHOD = "async startContainerIfNotRunning(waitOptions, options) {"
WAIT_METHOD = "async waitForPort(waitOptions) {"
NOT_RUNNING_MESSAGE = "The container is not running, consider calling start()"
PORT_LOOKUP = re.compile(
    r"const port = this\.container\.getTcpPort\(waitOptions\.portToCheck\);\s*try \{"
)
WAIT_PORT_LOOKUP = re.compile(
    r"const port = waitOptions\.portToCheck;\s*const tcpPort = this\.container\.getTcpPort\(port\);"
)
WAIT_PORT_TRY = re.compile(
    r"try\s*\{\s*const combinedSignal\s*=\s*addTimeoutSignal\(waitOptions\.signal,\s*PING_TIMEOUT_MS\);"
)
WAIT_NOT_RUNNING_GUARD = re.compile(r"if\s*\(!this\.container\.running\)\s*\{")


def patch_start_container_lookup(source: str) -> str:
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
    return PORT_LOOKUP.sub(retryable_lookup, source, count=1)


def patch_wait_for_port(source: str) -> str:
    if source.count(WAIT_METHOD) != 1:
        raise ValueError("Expected exactly one known waitForPort method")
    method_start = source.index(WAIT_METHOD)
    method_end = source.find("async stop(", method_start)
    if method_end < 0:
        raise ValueError("Could not locate the end of waitForPort before stop()")
    method = source[method_start:method_end]
    if len(WAIT_PORT_LOOKUP.findall(method)) != 1:
        raise ValueError("Expected one waitForPort lookup outside its retry loop")
    if len(WAIT_PORT_TRY.findall(method)) != 1:
        raise ValueError("Expected one waitForPort readiness retry block")
    if len(WAIT_NOT_RUNNING_GUARD.findall(method)) != 1:
        raise ValueError("Expected one waitForPort not-running guard")

    method = WAIT_PORT_LOOKUP.sub("const port = waitOptions.portToCheck;", method, count=1)
    retryable_try = (
        f"try {{ /* {WAIT_MARKER}: allow the native not-running startup transition to retry */\n"
        "        const tcpPort = this.container.getTcpPort(port);\n"
        "        const combinedSignal = addTimeoutSignal(waitOptions.signal, PING_TIMEOUT_MS);"
    )
    method = WAIT_PORT_TRY.sub(retryable_try, method, count=1)
    method = WAIT_NOT_RUNNING_GUARD.sub(
        f'if (!this.container.running && !errorMessage.includes("{NOT_RUNNING_MESSAGE}")) {{',
        method,
        count=1,
    )
    return source[:method_start] + method + source[method_end:]


def patch_source(source: str) -> tuple[str, str]:
    original = source
    if MARKER not in source:
        source = patch_start_container_lookup(source)
    if WAIT_MARKER not in source:
        source = patch_wait_for_port(source)
    return source, "already-patched" if source == original else "installed"


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: container_startup_port_retry.py <worker-bundle.js>")

    path = Path(sys.argv[1])
    source = path.read_text(encoding="utf-8")
    patched, result = patch_source(source)
    if patched.count(MARKER) != 1 or PORT_LOOKUP.search(patched):
        raise SystemExit("Start helper port lookup is not inside the SDK retry catch")
    if patched.count(WAIT_MARKER) != 1 or WAIT_PORT_LOOKUP.search(patched):
        raise SystemExit("waitForPort lookup is not inside its retry loop")
    if patched.count(METHOD) != 1:
        raise SystemExit("Container startup helper structure failed validation")
    wait_start = patched.index(WAIT_METHOD)
    wait_end = patched.find("async stop(", wait_start)
    wait_method = patched[wait_start:wait_end]
    if (
        patched.count(WAIT_METHOD) != 1
        or wait_end < 0
        or WAIT_MARKER not in wait_method
        or f'!errorMessage.includes("{NOT_RUNNING_MESSAGE}")' not in wait_method
    ):
        raise SystemExit("waitForPort startup transition guard failed validation")

    if patched != source:
        path.write_text(patched, encoding="utf-8")
    if result == "installed":
        print("GENESIS transient startup port retries installed")
    else:
        print("GENESIS transient startup port lookup retry already present")


if __name__ == "__main__":
    main()
