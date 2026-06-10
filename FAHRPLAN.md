# FAHRPLAN — benni_media_state

L1 Context-Feeder. Aus `bennis_toolbox/.../benni_media_context/` extrahiert
(1→2-Split: dieser Feeder + `benni_media_policy`).

## Step 1 — Scaffold ✅ (0.1.0)

Lauffähiges, leeres Skeleton, Struktur gespiegelt von `benni_light_policy`:
Hub + Auto-Bind + WS-Contract + Vanilla-Panel. **Keine Fachlogik.**

## Phase 3 — Context-Extraktion ✅ (0.2.0, FLEET-30)

- Context-Teil aus `benni_media_context` gecarvt (detect_* + decide), HA-frei.
- B2-Gate FINAL (Titel-Ebene via ETM-Raw, Enum = Sound-Mode) + R6 (PS5-Menü
  → grind, Sticky-Edge).
- Quiet entkoppelt (FLEET-31): Detection bleibt L1, schaltet kein Szenario.
- private_time: Stash-Streams / ETM-Stash-Enum (FLEET-43) / manueller Schalter.
- Volles Quellmodell + Live-Prefill (benni), Debounce 4 s.

## Phase 4 — Lastenheft + Cut-over (offen, FLEET-36)

- Konsumenten umkonfigurieren (light_policy, core_state, YAML) auf die
  `<profil>_media_state_*`-Entities; Toolbox-Modul danach löschen (Strangler).
- Entity-Roster final bestätigen; Shadow-Vergleich Toolbox vs. media_state.

## Konsum-Vertrag

`benni_media_policy` konsumiert diesen Feeder **nur über Entity-State** — nie per
Python-Import. Slug-Stabilität wahren (Konsumenten nicht churnen).

## Verifikation

Lokal kein HA/dulwich → `py_compile` + pure-logic-Tests. Rest live auf
`einhornzentrale` (Canary); `haos_benni` (Prod) bleibt unangetastet.
