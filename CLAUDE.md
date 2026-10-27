# Talk like a Caveman beim denken.

# Super Star Trek – Projektübersicht für Claude

## Was ist das?

HTML5/JavaScript-Port von **Super Star Trek** (Original BASIC 1978, Mike Mayfield / Dave Ahl).
Portierungskette: BASIC → Lua (Emanuele Bolognesi, 2020) → Python → **HTML5/JS (2026, führend)**.

Einzige Klasse: `Game` in `superstartrek.html` (~2350 Zeilen, Inline-JS).
GUI: klassische **ASCII-Brücke** im grünen Terminal-Look. Die frühere LCARS-GUI liegt im Branch `lcars-legacy`.

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
| `HANDBUCH.html` | Spielanleitung auf Deutsch |
| `EVENTS.md` | Konzept der Sonderereignisse |
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
- Layout: feste ASCII-Brücke `#bridge` (oben) + scrollendes `#terminal` + Eingabezeile `#input-row`.
  `shortRangeSensorScan()` rendert die Brücke neu: Sektorkarte, Statuswerte, `_enterpriseSchematic()`
  (Schilde + Geräteschäden) und Crew-Leiste. Reine Tastatureingabe.
- Sound: `beep()` (Rechteckton) und `SFX.phaser()/torpedo()/boom()/warp()` (Web Audio, ohne Samples).
- Rundenmodell: `_passTime(days)` lässt Zeit vergehen (Sterndatum, Selbstreparatur, Zeitablauf); `_enemyTurn()` = Tarnzyklus + Gegnerfeuer; `_tacticalTurn()` = Gegnerzug + 0,1 Sterndatum für SHE/PHA/TOR/TAC/TRB/REP. NAV: Gegnerzug vor der Bewegung, Flugzeit `_travelDays()`. Informationsbefehle sind frei.
- Sonderereignisse zeigen ASCII-Grafiken aus `EVENT_ART` über `printArt()`; `«klasse|text»` in einer Zeile färbt einen Abschnitt (CSS-Klasse).
- Farben: `safeHtml()` (Token → PUA-Escaping → `<span>`) + `colorMsg()` (Nachrichtenklassen) im Terminal-Log.

## Wichtige Methoden (Auswahl)

| Methode | Bedeutung |
|---------|-----------|
| `_initGalaxy()` | Galaxis zufällig befüllen |
| `_checkSpecialEvents()` | Harry Mudd, Vulkan-Schiff, Händler, Tribbles |
| `_klingonsAttack()` / `_romulansAttack()` | Angriffe der Gegner (gemeinsamer Treffer: `_takeHit()`) |
| `shortRangeSensorScan()` | SRS → zeichnet die ASCII-Brücke `#bridge` |
| `firePhasers()` / `firePhotonTorpedoes()` | Waffen |
| `courseControl()` | Bewegung (NAV) |
| `tachyonScan()` | Getarnte Romulaner aufspüren |
| `beamTribbles()` | Tribbles auf Klingonenschiff beamen |

## Konventionen

- Koordinaten: `q1/q2` = Quadrant (row/col), `s1/s2` = Sektor (row/col), 1-basiert.
- Geräteschäden: `damageLevel[1..8]` – negativ = beschädigt, ≥ 0 = funktionsfähig.
- Sonderereignis-Quadranten (`harryMuddQuadrant` etc.) werden auf `[0,0]` gesetzt wenn verbraucht.
- Klingonen: `k[1..3]`, Romulaner: `r[1..2]` jeweils `[row, col, energy, ...]`.
- Nach Änderungen an `k3/r3/b3/s3` den Galaxis-Eintrag mit `_updateQuadrantRecord()` nachziehen.
- Sprache: gesamte UI auf **Deutsch** (Befehle, Meldungen, Status).
