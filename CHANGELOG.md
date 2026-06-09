# Changelog

## 0.1.0 — scaffold

### Realign (Step 1.5 — gelockte Profil-Mechanik, FLEET-29 / FLEET-31)

- Device-Name **profil-getrieben** (`{label} Media State`) → Entity-Slug
  `<profil>_media_state_*` (benni/eltern), `suggested_object_id` entfernt.
- Profil-Config + Auto-Bind 1:1 aus `benni_core_state`: Add-Flow `user`
  (Profil-Select) → `entities` (Override-only-Storage), `coordinator._entity_id`
  (options ▶ data ▶ PROFILE_PREFILL[profile]), Existenz-Filter im Prefill.
- unique_id domain+entry-scoped (`{DOMAIN}_{entry_id}_{key}`); Single-Instance
  via `_async_current_entries()`.
- WS `get_status` um `profile` / `profile_label` ergänzt.
- **Quiet bleibt L1 (FLEET-31):** `quiet_mode` + `quiet_mode_reason` ins Roster
  aufgenommen (Stubs; Detection in Phase 3).
- event-driven Coordinator beibehalten (kein 30-s-Poll wie core_state).


- Step-1-Scaffold: lauffähiges, leeres Skeleton der Integration.
- Profil-Hub (benni/eltern) + Auto-Bind (Override ▶ Profil-Map ▶ leer).
- Single-Instance Config-Flow (unique_id `benni_media_state_singleton`) + Options-Menü-Gerüst.
- DataUpdateCoordinator (event-driven, kein Polling) mit HA-freier `logic.decide()`-Stub.
- Entity-Roster (Sensoren + Binary-Sensoren) aus `coordinator.data`, stabile Defaults.
- WebSocket-Command `benni_media_state/get_status` + Vanilla-Debug-Panel.
- Smoke-Tests grün. **Keine Fachlogik portiert.**
