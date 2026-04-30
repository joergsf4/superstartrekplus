# Talk like a Caveman beim denken.

# Super Star Trek – Projektübersicht für Claude

## Was ist das?

HTML5/JavaScript-Port von **Super Star Trek** (Original BASIC 1978, Mike Mayfield / Dave Ahl).
Portierungskette: BASIC → Lua (Emanuele Bolognesi, 2020) → Python → **HTML5/JS (2026, führend)**.

Einzige Klasse: `Game` in `superstartrek.html` (~1800 Zeilen Inline-JS).

## Starten

`superstartrek.html` im Browser öffnen (Doppelklick). Kein Server, kein Build-Schritt.

Für lokalen Dev-Server (optional):
```bash
python -m http.server 8787
# → http://localhost:8787/superstartrek.html
```

## Abhängigkeiten

Keine. Reines Vanilla-JS, läuft in jedem modernen Browser.

## Projektstruktur

| Datei | Zweck |
|-------|-------|
| `superstartrek.html` | **Gesamtes Spiel** (HTML + CSS + JS, Single File) |
| `HANDBUCH.md` | Spielanleitung auf Deutsch |
| `CLAUDE.md` | Diese Datei |
| `legacy/superstartrek.py` | Python-Vorgängerversion (Referenz) |
| `legacy/_test_events.py` | Python-Ereignistests (Referenz) |
| `legacy/run.bat` | Alter Windows-Starter (Referenz) |
| `legacy/requirements.txt` | Python-Abhängigkeiten (Referenz) |

## Architektur

- **Eine Klasse `Game`** enthält den gesamten Zustand und alle Logik.
- **1-basierte Koordinaten** durchgehend (Arrays mit Dummy-Index 0).
- Quadranten-String: `quadString` = 192 Zeichen (8×8 Sektoren × 3 Zeichen).
- `galaxy[i][j]` kodiert: `klingons*1000 + romulans*100 + starbases*10 + stars`.
- I/O über `telePrint()` (schreibt in `#terminal`) und `ask()` (Promise-basiert).
- Layout: `#bridge` (persistentes HUD, SRS-Karte + Status) + `#terminal` (scrollbares Log) + `#input-row`.
- Farben: `safeHtml()` (Token → PUA-Escaping → `<span>`) + `colorMsg()` (Nachrichtenklassen).

## Wichtige Methoden (Auswahl)

| Methode | Bedeutung |
|---------|-----------|
| `_initGalaxy()` | Galaxis zufällig befüllen |
| `_checkSpecialEvents()` | Harry Mudd, Vulkan-Schiff, Händler, Tribbles |
| `_klingonsAttack()` / `_romulansAttack()` | Angriffe der Gegner |
| `shortRangeSensorScan()` | SRS → rendert in `#bridge` HUD |
| `firePhasers()` / `firePhotonTorpedoes()` | Waffen |
| `courseControl()` / `impulseEngines()` | Bewegung |
| `tachyonScan()` | Getarnte Romulaner aufspüren |
| `beamTribbles()` | Tribbles auf Klingonenschiff beamen |

## Konventionen

- Koordinaten: `q1/q2` = Quadrant (row/col), `s1/s2` = Sektor (row/col), 1-basiert.
- Geräteschäden: `damageLevel[1..8]` – positiv = beschädigt, negativ = repariert.
- Sonderereignis-Quadranten (`harryMuddQuadrant` etc.) werden auf `[0,0]` gesetzt wenn verbraucht.
- Klingonen: `k[1..3]`, Romulaner: `r[1..2]` jeweils `[row, col, energy, ...]`.
- Sprache: gesamte UI auf **Deutsch** (Befehle, Meldungen, Status).
