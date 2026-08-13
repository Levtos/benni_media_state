# Issue #21 — Medienquellen-Arbitration

## Entscheidung

- `Apple TV` wird ausschließlich aus dem gebundenen nativen LAN-Player für
  Power, Verfügbarkeit und Playback gelesen. Die MA-Entität bleibt auf Routing
  und Metadaten beschränkt. Ein gültiger nativer Zustand `playing`, `paused` oder
  `idle` darf Streaming-Kontext markieren; `off`, `unknown` und `unavailable`
  nicht. `idle` und `paused` sind dabei nur Kontext, niemals ein automatischer
  Musikstart.
- `PS5` gewinnt vor TV; echtes Apple-TV-`playing` folgt dem bestehenden G10-
  Sondervertrag und kann nur den PS5-`gaming_grind` verdrängen. Bei Apple-TV-
  `idle`/`paused` bleibt `gaming_grind` daher vorrangig.
- Ein TV-only-Kaltstart kann aus dem TV-Master den expliziten Rohstatus
  `tv_candidate` liefern. Dieser Status ist noch kein bestätigter TV-Kontext und
  setzt weder `is_powered` noch `media_context` auf aktiv. Der Media State hält
  ihn 20 Sekunden; bleibt frische Leistung bei mindestens 50 W und gewinnt keine
  externe Quelle, wird TV-Kontext bestätigt. Unter 50 W, stale oder fehlender
  Wattquelle verwirft der Kandidat.
- TV wird erst nach 20 Sekunden stabiler Aktivität als TV-Kontext bestätigt.
  Ein Off innerhalb dieses Fensters verwirft den Start; Apple TV oder PS5
  werden während des Fensters sofort ausgewertet.
- TV-Watt ist im Media-State nur der Fallback. Die gemeinsame On-Schwelle ist
  50 W; die eigentliche Quellen-Freshness und der WebOS/Watt-Konflikt gehören
  in den TV-Master von Core Devices.

## G10-Abgleich

Das reviewed Media-Lastenheft R7a/G10 formuliert enger, dass `idle`/`paused`
keinen Streaming-Kontext erzeugen. Der Review-Nachtrag zu Issue #21 präzisiert
dies in zwei Ebenen: `idle`/`paused` dürfen einen gültigen Apple-TV-Kontext
anzeigen, dürfen aber weiterhin niemals `gaming_grind` verdrängen und keine
Musik-Aktion starten. Diese Änderung bleibt auf Kontext-Erkennung begrenzt;
Policy-, Owner-, Resume- und Apply-Verträge werden nicht geändert.

## Bewusste Grenzen

`benni_media_policy` bleibt der Owner für Audio-Owner, Audio-Szenario,
Resume und Radio. `benni_media_apply` bleibt der Executor. Diese Issue-21-
Änderung enthält keine Policy-, Apply-, Audio- oder Resume-Entscheidung und
keine Live-/HA-Änderung.

## Referenzen

- `Levtos/benni_media_state#21`
- `Levtos/benni-core-devices#41`
- G10/R7a im Media-Lastenheft: tatsächliches Apple-TV-`playing` verdrängt den
  Gaming-Grind; `idle` und `paused` tun dies nicht. Die Kontext-Erweiterung und
  diese Prioritätsgrenze sind durch Regressionstests abgedeckt.
