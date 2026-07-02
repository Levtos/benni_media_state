# Changelog

## 0.11.0 — Nativer Private-Time-Schalter (kein input_boolean/YAML mehr)

- **`switch.<profil>_media_state_private_time_manual`** neu: integration-eigene
  Schalt-Entität für den manuellen private_time-Trigger (Dating/Besuch,
  FLEET-44). Ersetzt den externen `input_boolean.media_private_time_manual`
  (verschwunden seit gestern) — nativ, kein YAML-Helfer, kein externes Binding.
  Zustand coordinator-backed + über RestoreEntity persistent.
- **Auto-Löschung** (FLEET-98) von media_apply hierher gezogen: der Latch räumt
  sich beim Einschlafen (bio_state-Flanke) und nach Timeout (4 h) selbst.
- Externes `private_manual_entity`-Binding entfernt (WATCH-Keys + Prefill) → die
  `[missing]`-Bindungsprobleme im Diagnostics-Tab verschwinden.
- NB: unberührt von der Nintendo Switch (`sensor.benni_master_switch`).

## 0.10.1 — Away aus presence_personal ableiten (stabile Entity-ID)

- **Hotfix zu 0.10.0.** Der in 0.10.0 eingeführte Slot `away_source_entity` zeigte
  auf `binary_sensor.benni_core_state_away` — der reale Entity-Slug ist aber
  geräteabhängig (die core_state-Devices sind zu „System …" umbenannt → neue
  Entitäten erben `system_`-Präfix, z.B. `binary_sensor.system_benni_core_state_presence_away`).
  Damit war die Bindung `[missing]` → `presence_state=unknown` → Policy blockte
  die Musik-Baseline (Musik blieb aus).
- Fix: `away_source_entity` **entfernt**. media_state leitet den Away-Gate jetzt
  strikt aus core_states `presence_personal`-Enum ab (`abwesend` → away;
  `zuhause`/`bei_eltern` → home; sonst kein Gate) — stabile, saubere Entity-ID
  (`sensor.benni_core_state_presence_personal`), retained seit core_state v0.6.0.
  Immer noch EIN Presence-Owner (core_state), nur an der robusteren Quelle.
- ON-Debounce (`gate_away`, 25 s) unverändert. Output-Contract unverändert.

## 0.10.0 — Echo core_state presence (one owner) + Away-Debounce

- **Keine eigene home/away-Klassifikation mehr.** `PRESENCE_HOME_STATES`/
  `PRESENCE_AWAY_STATES` und `classify_presence` entfernt. media_state
  konsumiert stattdessen die kanonische Fleet-Entscheidung
  `binary_sensor.benni_core_state_away` (core_state ≥ v0.6.0) über den neuen
  Slot `away_source_entity`. Damit gibt es genau EINEN Owner der
  Presence-Semantik — das behebt die `bei_eltern`-Fehlklassifikations-Klasse an
  der Wurzel (core_state kodiert bei_eltern bereits als home/off).
- **ON-Debounce** (`AWAY_DEBOUNCE_SECONDS`, 25 s): Away muss stabil anliegen,
  bevor das Media-Gate greift — ein transienter Away-Dip reißt die Audio-Kette
  nicht mehr ab (Defense-in-Depth; die HA-Restart-Flap-Wurzel ist in
  core_state v0.6.0 behoben). Rückkehr (→home) wirkt sofort.
- Contract der Ausgabe-Entities (`presence_state`, `presence_source`,
  `away_gate`) unverändert → policy/apply-Bindings brauchen keine Änderung.
  `presence_entity` (presence_personal) bleibt gebunden, dient jetzt nur noch
  der Roh-Quellen-Anzeige (`presence_source`).

## 0.9.1 — bei_eltern is Media Home-Equivalent

- Treat raw presence `bei_eltern` as media home-equivalent instead of away.
- Keep Away-Gate behavior for real absence (`abwesend`/`not_home`/generic away
  values), but do not stop music just because Benni is at the parents.
- Align Media State with the context/plug Lastenheft direction: `bei_eltern`
  is not an Away-Cut trigger.

## 0.9.0 — FLEET-212: Presence-Away-Gate + Config-Domain-Split

- **Presence-Gate:** `logic.decide` konsumiert jetzt core_state
  `presence_personal` als harten Gate mit höchster Priorität. Bei Abwesenheit
  (`abwesend`/`bei_eltern`/`not_home`/…) → Szenario auf `idle`,
  `entertainment_active=False`, Gaming-Felder geräumt → der Apply-Layer stoppt
  laufende Musik/Entertainment, statt weiterzufahren. `bei_eltern` zählt als
  away (physisch nicht am Wohnzimmer-Media). `unknown`/nicht gebunden greift
  NICHT (kein Fehl-Stop bei Sensor-Aussetzern).
- **Neue sichtbare Entitäten:** `sensor.<profil>_media_state_presence_state`
  (`zuhause`/`abwesend`/`unknown`, mit `presence_source`- und
  `away_gate`-Attribut) + `binary_sensor.<profil>_media_state_away_gate`. Der
  Haupt-`Media Context`-Sensor spiegelt `presence_state`/`presence_source`/
  `away_gate` zusätzlich als Attribut (Diagnose).
- **Config-Domain-Fix:** Apple TV sauber in zwei Slots getrennt — nativer
  `appletv_player_entity` (media_player) + `appletv_master_entity` (sensor,
  core_devices-Master). Vorher trug EIN media_player-gefiltertes Feld den
  Master-Sensor `sensor.benni_master_appletv` → Options-Flow lehnte ihn als
  falsche Domain ab. Selektor-Domains laufen jetzt über den HA-freien Contract
  `source_domain_filter` (Player→`media_player`, Master→`sensor`/
  `binary_sensor`), pure testbar.
- **Coordinator:** Apple-TV-Aktiv-Wahrheit primär aus dem Master (`is_active` +
  `app_id`/`player_state`), nativer Player nur Fallback (spiegelt `_tv_active`).
  Legacy-Repoint `media_player.living_appletv → master` entfernt (der Player ist
  jetzt ein eigener Slot).
- Tests: `test_presence.py` (Gate/Klassifikation) + `test_flow_domains.py`
  (Selektor-Domain-Contract); `test_rebind.py` an den ATV-Split angepasst.
  51 Tests grün.

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
