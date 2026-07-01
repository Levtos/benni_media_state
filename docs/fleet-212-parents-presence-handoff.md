# FLEET-212 Follow-up: `bei_eltern` Is Not Media Away

Datum: 2026-07-01

Owner laut Fleet-Matrix: Claude Code (`media_state`, `media_policy`, `media_apply`, `benni_media`).
Codex hat diesen Hotfix nach Benni-Live-Beobachtung als Folgekorrektur zu FLEET-212 umgesetzt.

## Befund

Nach dem Away-Gate-Release ging Musik aus, wenn Bennis Presence-Rohzustand
`bei_eltern` war. Das war nicht aus dem Lastenheft ableitbar und widerspricht
mehreren vorhandenen Kontext-/Steckdosen-Notizen:

- `bei_eltern` ist home-equivalent.
- `bei_eltern` erzeugt kein externes Coming-Home und kein Auto-Unlock.
- `bei_eltern` ist aber kein Away-Cut-/Abschalt-Trigger.

Die Ursache lag in `benni_media_state v0.9.0`: `bei_eltern` war in
`PRESENCE_AWAY_STATES` enthalten und wurde dadurch zu:

```text
presence_state=abwesend
away_gate=True
```

Das zwang Media State auf `idle`, Policy auf `off`/Volume-Block und Apply zum
Stoppen der Musik.

## Fix

Release: `benni_media_state v0.9.1`

- `bei_eltern` ist jetzt in `PRESENCE_HOME_STATES`.
- `bei_eltern` normalisiert fuer Media zu `presence_state=zuhause`.
- `presence_source` bleibt `bei_eltern` sichtbar, damit Diagnose und Claude den
  Rohzustand nachvollziehen koennen.
- `away_gate=False`; laufende Musik/Media wird dadurch nicht gestoppt.
- Echte Away-Werte (`abwesend`, `not_home`, `away`, `off`, ...) bleiben harte
  Away-Gate-Ausloeser.

Simulation nach Fix:

```text
presence=bei_eltern
presence_state=zuhause
presence_source=bei_eltern
away_gate=False
context=tv   # Beispiel mit tv_active=True
entertainment_active=True
```

## PR / Release

- PR: https://github.com/Levtos/benni_media_state/pull/8
- Release: https://github.com/Levtos/benni_media_state/releases/tag/v0.9.1
- Fix commit: `b86ded058edb8f82c2c5f22b6c7c0f7cd431d463`
- Merge: `24a899ffe200188f175667f08e72aa9a8ec4330a`

## Gates

- `python -m pytest`: 51 passed.
- `python -m compileall -q custom_components tests`: green.
- Ruff still reports the existing repository-wide `UP045` Optional-modernization backlog.

## Deploy / Reload

Benni macht Pull/Deploy/Reload/Restart selbst.

Recommended order for this follow-up:

1. `benni_media_state`
2. `benni_media_policy`
3. `benni_media_apply`
4. `benni_media`

`benni_media_policy` and `benni_media_apply` did not need code changes for this
part. They already allow non-`abwesend` presence as long as State does not assert
`away_gate`.

## Live Verification For Claude

On Einhornzentrale (`192.168.178.106:8123`), after deploy:

- Set or observe raw personal presence as `bei_eltern`.
- Verify `sensor.system_benni_media_state_presence_state` / corresponding profile
  entity reports state `zuhause` with `presence_source=bei_eltern`.
- Verify `binary_sensor.system_benni_media_state_away_gate=off`.
- Verify Media Policy no longer reports Away/Presence block solely because of
  `bei_eltern`.
- Verify music is not stopped merely by the parents state.

## Plane / Fleet Board Status

Codex attempted Plane updates earlier on 2026-07-01, but the Plane MCP returned
HTTP 404 for `list_projects` and `list_work_items`. When Plane access is restored,
update or create the FLEET card with:

- Title suggestion: `Media presence: bei_eltern must not trigger Away-Gate`
- Owner: Claude Code
- State: `Testing` until live-verified, then `Live`.
- Summary: `benni_media_state v0.9.1` maps `bei_eltern` to Media home-equivalent
  while preserving `presence_source=bei_eltern`; Away-Gate remains for true absence.

