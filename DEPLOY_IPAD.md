# iPad Start per Web-Link

Die App kann auf dem iPad nicht ueber `127.0.0.1` aus der Codex-Umgebung geoeffnet werden. Dafuer muss sie online gehostet werden.

## Schnellster Weg mit Render

1. Auf dem iPad Safari oeffnen.
2. `https://render.com` oeffnen.
3. Mit GitHub anmelden.
4. `New` -> `Web Service` auswaehlen.
5. Repository `y5fpk7vhw5-hub/Database` verbinden.
6. Render erkennt `render.yaml` automatisch.
7. Deploy starten.
8. Nach dem Deploy bekommst du eine URL wie:

```text
https://construction-site-db.onrender.com
```

Diese URL kannst du direkt auf dem iPad oeffnen.

## Hinweise

- Der erste Start auf Render Free kann etwas dauern.
- SQLite ist fuer Demo/MVP okay, aber fuer echte Mehrbenutzer-Nutzung sollte PostgreSQL genutzt werden.
- Dein Repository ist aktuell public. Fuer Projektdaten sollte es private sein.
