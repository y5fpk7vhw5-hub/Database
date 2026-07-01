# Construction Site Database

Professionelles MVP einer webbasierten Construction-Datenbank gemaess Lastenheft fuer Baustellen im Prozessanlagenbau.

## Start lokal

```bash
python3 seed.py
python3 app.py 8080
```

Dann im Browser oeffnen:

```text
http://127.0.0.1:8080
```

## Module

- Dashboard mit KPIs fuer Progress, Punch, SEWO, Permits, Actions und Mannstunden
- Vertragsdatenbank fuer Kunden- und Nachunternehmervertraege
- Dokumenten- und Zeichnungsregister
- Meeting Management mit Action Tracking
- Progress Tracking mit Baseline, Gewichtung und Daily Input
- SEWO-Register fuer Site Extra Works pro Nachunternehmer
- HSE: Permit-to-Work, Mannstunden, Beobachtungen und Unfallberichte
- Quality: ITP-Register
- Mechanical Completion und Punch Items
- Fotodokumentation als Metadatenregister
- Globale Suche
- CSV-Export und druckbarer Wochenreport

## Enthaltene Demo-Struktur

Nachunternehmer und Gewerke sind gemaess Lastenheft vorbelegt:

- Bilfinger Insulation
- MKL Stahlbau
- ERS Refractory
- JWW Mechanical Erection
- Goodmont Auxiliary Piping
- SpecTech FRP Piping
- Powerspex Electrical & Instrumentation

## Datenhaltung

Die Anwendung nutzt SQLite. Die Datei `data/construction.db` wird aus `schema.sql` und `seed.py` erzeugt und wird nicht versioniert.

## Naechste produktive Ausbaustufe

- Benutzerlogin und echte rollenbasierte Berechtigungen
- PostgreSQL fuer Mehrbenutzerbetrieb
- Dateiuploads mit DMS-/SharePoint-Anbindung
- serverseitige PDF-Erzeugung und unveraenderbares Reportarchiv
- Import aus Terminplan, BOQ und MTO
- Freigabe-Workflow fuer Baseline- und Gewichtsaenderungen
