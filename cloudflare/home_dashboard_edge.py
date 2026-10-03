"""Retired GENESIS home edge-overlay installer.

The opening dashboard is native to the container image. Re-introducing a Worker
HTML/JS overlay causes duplicate controls, stale launchers and split-workspace
chrome. Keep this file only as an explicit guard for historical workflows.
"""

raise SystemExit(
    "RETIRED: home_dashboard_edge.py must not patch production. "
    "Use cloudflare/home_dashboard.py for the native GENESIS home."
)
