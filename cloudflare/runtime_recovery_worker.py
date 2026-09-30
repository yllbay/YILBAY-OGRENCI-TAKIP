from pathlib import Path
import sys

p = Path(sys.argv[1])
src = p.read_text(encoding='utf-8')
anchor = '  defaultPort = 8e3;\n  sleepAfter = "2h";'
assert src.count(anchor) == 1
src = src.replace(anchor, anchor + '''
  // GENESIS_LOCAL_SQLITE_R2_V1: a read-only health path and bounded cold start.
  pingEndpoint = "ping/_health";
  recoveryStartup = null;
  async fetch(request) {
    if (!this.recoveryStartup) {
      this.recoveryStartup = this.startAndWaitForPorts(
        [8000], {instanceGetTimeoutMS: 20000, portReadyTimeoutMS: 120000}
      ).finally(() => { this.recoveryStartup = null; });
    }
    await this.recoveryStartup;
    return super.fetch(request);
  }
''', 1)
p.write_text(src, encoding='utf-8')
print('GENESIS read-only container health and cold-start window installed')
