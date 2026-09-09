# Agent instructions — site-coverage-planner

QGIS line-of-sight / coverage planning toolkit. Module 1 = CCTV camera coverage (FoV +
DORI bands + viewshed). Spike — expiry ~1–2 sessions unless converted to Active.

- **Stack:** Python 3.11+ (QGIS ships 3.12), PyQGIS / GDAL for the plugin layer. Pure
  optics/DORI math in `site_coverage_planner/optics.py` is QGIS-free and unit-tested.
- **Vault note:** `ProjectVault/03_Concepts_and_Backburner/QGIS CCTV Coverage Plugin.md` —
  read it for the prior-art table, steal-list, and v0 scope before non-trivial work.
  Canonical over anything stale here.
- **Runtime preflight:** `python` on PATH; `pip install -e .[dev]` then `pytest` (5 tests).
  QGIS not required for the test suite.
- **Deploy:** not deployed. Eventual target: QGIS plugin repository (public).
- **Platform:** QGIS runs on Windows here; the plugin loads from the Windows QGIS
  profile plugins dir.

## Operating contract (Claude Code + Codex)

Austin's global rules live in `~/.claude/CLAUDE.md` + `CLAUDE-shared.md` (Claude Code) and
`~/.codex/AGENTS.md` (Codex) — same contract, both agents. Load-bearing: simplest viable
solution first (no new scripts/infra unless asked), confirm the path before editing, todos
are per-project (never a global TASKS.md), the git workflow in that contract (session end
syncs every touched repo — commit, push, merge/prune — without asking), session-end
`/document` capture to the vault if the work produced a decision/fix/learning.

`HANDOFF.md` at repo root, if present, is the live cross-agent baton — read it on start,
act on or update your own entries, delete stale ones.
