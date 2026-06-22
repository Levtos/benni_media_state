# Changelog

## 0.8.2 - FLEET-147: AppleTV Master ReBind

- Repoint Benni AppleTV source defaults and saved raw/legacy AppleTV bindings to `sensor.benni_master_appletv`.
- Treat the Core-Devices AppleTV Master `idle` activity enum as the old player `paused` state for streaming detection and device priority.
- Keep Cockpit AppleTV app/title observability compatible with both raw player and master attributes.

## 0.8.1 - Master ReBind

- Repointed Benni profile active-source defaults from obsolete
  `sensor.benni_device_*` Core-Devices outputs to the existing device masters
  (`sensor.benni_master_pc`, `ps5`, `switch`, `denon`).
- Kept TV on `sensor.benni_master_tv` as the primary `is_active` source and
  stopped auto-binding the legacy TV active fallback.
- Added legacy entity normalization so saved ConfigEntry data/options that
  still contain old active-source IDs resolve to the corresponding master.
- Updated config/options labels and added HA-free guardrail tests for the
  master-backed defaults.

## 0.7.2 — Switch-Steckdose vorübergehend ignoriert (Stopgap)

- **Entscheidung:** Der 120-s-Latch aus 0.7.1 war auf Schätzdaten gebaut. Echte
  Playing-Watt der Switch-Steckdose fehlen / widersprechen sich (Lastenheft
  „Logik" idle ≤20/active ≥50 W mit nicht existierender Entität
  `sensor.switch_nintendo_power`; Recorder 21 Tage nie über 3 W). Bis echte
  idle/playing-Werte aus `sensor.living_switch_plug_power` vorliegen, wird
  geraten — also wird die Switch-Steckdose vorerst NICHT als Kontext-Quelle
  genutzt.
- **`switch_dock` hart auf False** in `_build_inputs` (mit Verweis FLEET-95).
  Der Roh-State bleibt im Cockpit sichtbar (`devices.switch.ignored=True`),
  treibt aber keine Entscheidung mehr → kein Radio-Churn.
- **Latch zurückgebaut:** `logic.latch_rising_edge`, `switch_latch_seconds`,
  Coordinator-Timer und Tests aus 0.7.1 wieder entfernt.
- **Re-Enable (FLEET-95):** beim nächsten echten Docken Watt mitschneiden,
  `watt_threshold_on` in core_devices datenbasiert setzen, Switch hier wieder
  als Quelle aktivieren + Entity-Namen sauberziehen (Excel-Logik veraltet).

## 0.7.1 — switch_dock Anstiegs-Latch (Radio-Churn-Fix)

- **Bug:** Die Switch-Steckdose pulst im Standby periodisch kurz (≈3–5 W, bis
  ~71 s beobachtet). core_devices' `watt_primary` flippt `powered` sofort beim
  ersten Tick über Schwelle (kein Anstiegs-Filter), `switch_dock` wurde True →
  Kontext kippte auf `gaming` → media_apply stoppte/restartete den Radio-Stream.
- **Workaround:** Anstiegs-Latch auf `switch_dock` — der Plug muss
  `switch_latch_seconds` (Default **120 s**, deckt die 71-s-Pulse ab)
  DURCHGEHEND Last melden, bevor `switch_dock=True` durchgereicht wird. Fallende
  Flanke folgt sofort. Reine Mechanik in `logic.latch_rising_edge` (HA-frei,
  7 neue Tests); Coordinator hält nur Zustand + Timer (Re-Eval aufs Latch-Ende,
  da das Roh-Signal während eines Pulses kein Event liefert).
- **Option:** `switch_latch_seconds` (über Entry-Options/-Data überschreibbar).
- Cockpit-Matrix zeigt `dock_pending`/`dock_latched`.
- **Hinweis:** Eigentlicher Fix gehört nach core_devices (generischer
  min-on-Filter im `watt_primary`) — als FLEET-Ticket für den Rewrite erfasst.

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
