# Changelog

## 0.2.0 — Phase 3: Context-Extraktion (FLEET-30)

- **logic.py-Carve** aus `bennis_toolbox/benni_media_context`: detect_devices,
  detect_gaming, detect_streaming, detect_tv + Context-Teil von decide.
  Policy-Teile (Volumes, Subwoofer, Orchestratoren) bewusst NICHT übernommen
  (→ benni_media_policy, FLEET-34).
- **B2-Gate FINAL:** PC-Gaming ⇔ ETM-Raw-Titel vorhanden ∧ ≠ „No Game"
  (Titel-Ebene); Enum wählt nur den Sound-Mode-Subcontext (0=default,
  1=grind, 2=headset) — „Enum ≥ 1"-Gate verworfen (Enum 0 = gültiges Spiel).
- **R6:** PS5 an + Titel leer (Menü) → gaming_grind; Titel-Wegfall WÄHREND
  der Session → letzter Subcontext sticky (Coordinator-Zustand).
- **Quiet entkoppelt (FLEET-31):** quiet_mode/_reason als reine Detection
  (extern ▶ Anruf ▶ Tür ▶ Musik-Enum-Mute ▶ Activity) — schaltet KEIN
  Szenario mehr (Toolbox-Kopplung quiet → private_time gestrichen).
- **private_time mit eigener Trigger-Quelle (FLEET-31):** Stash-Streams > 0
  ODER ETM-Stash-Enum ≥ 1 (FLEET-43) ODER manueller Schalter; Priorität
  private > gaming > streaming/tv > idle.
- Volles Context-Quellmodell als CONF-Slots (TV/ATV/PS5/Switch/PC/Denon/
  HomePods + ETM-Raw/Enum + Quiet + private-Trigger), `PROFILE_PREFILL[benni]`
  mit den Live-IDs der Einhornzentrale befüllt.
- Debounce (Default 4 s, Option) statt Sofort-Recompute je State-Change.
- 28 neue pure-logic-Tests (B2, R6, Quiet-Entkopplung, private-Trigger,
  Prioritäten, ATV-Rollback) — 30 gesamt grün.

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
