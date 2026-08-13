# Issue #21 — Medienquellen-Arbitration

## Entscheidung

- `Apple TV` wird ausschließlich aus dem gebundenen nativen LAN-Player für
  Power, Verfügbarkeit und Playback gelesen. Die MA-Entität bleibt auf Routing
  und Metadaten beschränkt; `idle`, `paused`, `unknown` und `unavailable` starten
  keinen Streaming-Kontext und keine Musik.
- `PS5` gewinnt vor TV; echtes Apple-TV-`playing` folgt dem bestehenden G10-
  Sondervertrag und kann nur den PS5-`gaming_grind` verdrängen.
- TV wird erst nach 20 Sekunden stabiler Aktivität als TV-Kontext bestätigt.
  Ein Off innerhalb dieses Fensters verwirft den Start; Apple TV oder PS5
  werden während des Fensters sofort ausgewertet.
- TV-Watt ist im Media-State nur der Fallback. Die gemeinsame On-Schwelle ist
  50 W; die eigentliche Quellen-Freshness und der WebOS/Watt-Konflikt gehören
  in den TV-Master von Core Devices.

## Bewusste Grenzen

`benni_media_policy` bleibt der Owner für Audio-Owner, Audio-Szenario,
Resume und Radio. `benni_media_apply` bleibt der Executor. Diese Issue-21-
Änderung enthält keine Policy-, Apply-, Audio- oder Resume-Entscheidung und
keine Live-/HA-Änderung.

## Referenzen

- `Levtos/benni_media_state#21`
- `Levtos/benni-core-devices#41`
- G10 im Media-Lastenheft: tatsächliches Apple-TV-`playing` verdrängt den
  Gaming-Grind; `idle` und `paused` tun dies nicht.
