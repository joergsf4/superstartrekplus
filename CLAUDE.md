# Super Star Trek – Projektübersicht für Claude

## Was ist das?

Python-Port von **Super Star Trek** (Original BASIC 1978, Mike Mayfield / Dave Ahl).
Portierungskette: BASIC → Lua (Emanuele Bolognesi, 2020) → Python (2026).

Einzige Klasse: `Game` in `superstartrek.py` (~1600 Zeilen).

## Starten & Testen

```bash
python superstartrek.py      # Spiel starten
run.bat                      # Windows-Doppelklick-Starter

python _test_events.py       # Automatisierte Ereignistests (kein pytest nötig)
```

## Abhängigkeiten

- `rich` (optional, für farbige Ausgabe) – `pip install rich`
- `winsound` (optional, Windows-Sounds) – in stdlib enthalten
- Python ≥ 3.8

## Projektstruktur

| Datei | Zweck |
|-------|-------|
| `superstartrek.py` | Gesamtes Spiel (Klasse `Game`) |
| `superstartrek.lua` | Lua-Vorlage (Referenz) |
| `_test_events.py` | Schnelltests für Sonderereignisse |
| `HANDBUCH.md` | Spielanleitung auf Deutsch |
| `run.bat` | Windows-Starter |
| `requirements.txt` | `rich` |

## Architektur

- **Eine Klasse `Game`** enthält den gesamten Zustand und alle Logik.
- **1-basierte Koordinaten** durchgehend (Arrays mit Dummy-Index 0).
- Quadranten-String: `quad_string` = 192 Zeichen (8×8 Sektoren × 3 Zeichen).
- `galaxy[i][j]` kodiert: `klingons*1000 + romulans*100 + starbases*10 + stars`.
- I/O über `tele_print()` und `ask()` – einfach austauschbar für GUI/TUI.
- `disable_teleprint = True` schaltet Tipp-Effekt in Tests ab.

## Wichtige Methoden (Auswahl)

| Methode | Bedeutung |
|---------|-----------|
| `_init_galaxy()` | Galaxis zufällig befüllen |
| `_check_special_events()` | Harry Mudd, Vulkan-Schiff, Händler, Tribbles |
| `_klingons_attack()` / `_romulans_attack()` | Angriffe der Gegner |
| `short_range_sensor_scan()` | SRS anzeigen |
| `fire_phasers()` / `fire_photon_torpedoes()` | Waffen |
| `navigation()` / `impulse_engines()` | Bewegung |
| `tachyon_scan()` | Getarnte Romulaner aufspüren |
| `beam_tribbles()` | Tribbles auf Klingonenschiff beamen |

## Konventionen

- Koordinaten: `q1/q2` = Quadrant (row/col), `s1/s2` = Sektor (row/col), 1-basiert.
- Geräteschäden: `damage_level[1..8]` – positiv = beschädigt, negativ = repariert.
- Sonderereignis-Quadranten (`harry_mudd_quadrant` etc.) werden auf `(0,0)` gesetzt wenn verbraucht.
- Klingonen: `k[1..3]`, Romulaner: `r[1..2]` jeweils `[row, col, energy, ...]`.
