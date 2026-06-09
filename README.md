# benni_media_state

Media-Context-Feeder (L1) als eigenständige HACS-Custom-Integration.

Leitet aus Roh-Quellen (Media-Player, Title-Classifier, Headset …) einen
**Media-Context** ab und stellt ihn als HA-Entities bereit. Entscheidet
**nichts** — kein Apply. Die Audio-/Volume-Policy lebt im Schwester-Modul
[`benni_media_policy`](https://github.com/Levtos/benni_media_policy), das diesen
Feeder ausschließlich **über Entity-State** konsumiert (kein Python-Import).

**Status:** `0.1.0` — Step-1-Scaffold. Lauffähiges, leeres Skeleton (Hub +
Auto-Bind + WS-Contract + Vanilla-Debug-Panel). **Keine Fachlogik portiert.**

## Schicht

L1 Context/Feeder — Teil des `benni_*`-Fleets. Wird aus dem Legacy-Monolithen
`bennis_toolbox/.../benni_media_context/` extrahiert (1→2-Split: dieser Feeder +
`benni_media_policy`).

## Entity-Roster (vorläufig — finalisiert das Lastenheft in Step 3)

| Entity | Bedeutung |
| --- | --- |
| `sensor.benni_media_state_media_context` | abgeleiteter Context (+ Attribute) |
| `sensor.benni_media_state_media_subcontext` | Subcontext |
| `sensor.benni_media_state_media_device` | aktives Gerät |
| `sensor.benni_media_state_gaming_source` | Gaming-Quelle |
| `sensor.benni_media_state_gaming_platform` | Gaming-Plattform |
| `binary_sensor.benni_media_state_headset_active` | Headset aktiv |
| `binary_sensor.benni_media_state_entertainment_active` | Entertainment aktiv |
| `binary_sensor.benni_media_state_quiet_mode` | Quiet-Mode aktiv (L1, FLEET-31) |
| `sensor.benni_media_state_quiet_mode_reason` | Begründung für Quiet-Mode |

> Der Entity-Präfix folgt dem **Profil** (Device-Name, `has_entity_name`):
> Route Benni → `…benni_media_state_*`, Route Eltern → `…eltern_media_state_*`.

## WebSocket

`benni_media_state/get_status` → `{ profile, profile_label, bindings, data }` (für das Panel).

## Roadmap

- **Step 1 (hier):** Scaffold. ✅
- **Step 2:** Ableitungs-Logik aus `benni_media_context/logic.py` extrahieren.
- **Step 3:** Reviewtes Lastenheft einarbeiten (Verhaltens-Spec, B2-Fix, Quiet/Private-Grenze).

Siehe `FAHRPLAN.md`.
