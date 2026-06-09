# FAHRPLAN — benni_media_state

L1 Context-Feeder. Aus `bennis_toolbox/.../benni_media_context/` extrahiert
(1→2-Split: dieser Feeder + `benni_media_policy`).

## Step 1 — Scaffold ✅ (0.1.0)

Lauffähiges, leeres Skeleton, Struktur gespiegelt von `benni_light_policy`:
Hub + Auto-Bind + WS-Contract + Vanilla-Panel. **Keine Fachlogik.**

## Step 2 — Logik-Extraktion (offen)

- `decide()`-Body aus `benni_media_context/logic.py` nach `logic.py` heben
  (HA-frei, Logik unverändert lassen — konservativer Lift, Shadow-Modus).
- Inputs-Contract an die echten Roh-Quellen angleichen.
- Pure-logic-Tests aus der Toolbox mitnehmen/anpassen.

## Step 3 — Lastenheft (offen)

- Reviewtes Lastenheft einarbeiten: Verhaltens-Spec, B2-Fix
  (`gaming nur bei classifier-Enum >= 1`, Gate in `detect_gaming`).
- Quiet/Private-Schichtgrenze klären (Detection bleibt ggf. hier in media_state).
- Entity-Roster finalisieren (aktuell vorläufig).

## Konsum-Vertrag

`benni_media_policy` konsumiert diesen Feeder **nur über Entity-State** — nie per
Python-Import. Slug-Stabilität wahren (Konsumenten nicht churnen).

## Verifikation

Lokal kein HA/dulwich → `py_compile` + pure-logic-Tests. Rest live auf
`einhornzentrale` (Canary); `haos_benni` (Prod) bleibt unangetastet.
