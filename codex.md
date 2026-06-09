# Codex Instructions — benni_media_state

Lies zuerst `CLAUDE.md` im GitHub-Root + `FAHRPLAN.md` in diesem Repo.

## MCP-Server

`einhornzentrale` (Canary, read-only Diagnose). Nicht `haos_benni` (Prod).

## Aktueller Status

**Step-1-Scaffold (0.1.0).** Owner der Extraktion ist Claude (Opus). Nie dieselbe
Integration gleichzeitig wie Claude bearbeiten — Abgrenzung über `owner:`-Label
auf dem FLEET-Board.

## Anti-Patterns

- Kein `bennis_toolbox`-Namespace, kein Cross-Modul-Python-Import zu
  `benni_media_policy` (Konsum nur über Entity-State).
- Slug-Stabilität wahren — Entity-IDs nicht churnen.
- Keine Fachlogik vorbauen, solange das Lastenheft (Step 3) nicht reviewt ist.
