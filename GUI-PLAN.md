# GUI-Plan: Grafische LCARS-Brücke für Super Star Trek

## Ziel

Aus dem reinen Text-Terminal wird eine **grafische Brückenansicht** im
**LCARS-Stil** (Library Computer Access/Retrieval System – die
Computeroberfläche aus Star Trek TNG): schwarzer Hintergrund, orange/lila/blaue
Panels mit abgerundeten „Pill"-Formen, kondensierte Großbuchstaben-Typografie.

**Randbedingungen (bleiben erhalten):**

- Single-File-Architektur: alles in `superstartrek.html`, kein Build-Schritt.
- Keine Abhängigkeiten, keine Bilddateien – alle Grafik ist **Inline-SVG + CSS**.
- Die Spiellogik (Klasse `Game`) bleibt unangetastet – nur die
  **Präsentationsschicht** wird ausgetauscht.
- UI-Sprache bleibt Deutsch.

## Warum dieser Ansatz?

| Option | Bewertung |
|--------|-----------|
| Canvas-Spiel komplett neu | ❌ Zu viel Umbau, Logik müsste umgeschrieben werden |
| Bilddateien / Sprites | ❌ Externe Assets, Datei nicht mehr self-contained |
| **CSS-Layout + Inline-SVG** | ✅ Hübsch, skalierbar, null Abhängigkeiten, Logik bleibt |

Die Spielschleife arbeitet weiter über `ask()`/`telePrint()` – das Terminal
bleibt als „Kommunikationskonsole" unten erhalten (Retro-Charme + alle
Meldungen/Events funktionieren unverändert). Die Grafik ist eine **reine
Ansicht auf den Spielzustand** (`quadString`, `energyLevel`, `damageLevel`, …).

## Layout

```
┌──────────────────────────────────────────────────────────────┐
│ ██ LCARS-Kopfzeile  USS ENTERPRISE NCC-1701   Sternzeit/Zustand │
├────────┬────────────────────────────────┬────────────────────┤
│ BEFEHLE│                                │  STATUS            │
│ ┌────┐ │        HAUPTSCHIRM             │  Energie   ▓▓▓▓░░  │
│ │NAV │ │   SVG 8×8-Sektorkarte          │  Schilde   ▓▓░░░░  │
│ │SRS │ │   Sternenfeld-Hintergrund      │  Torpedos  ●●●●●○  │
│ │LRS │ │   Sprites: Enterprise,         │  Systeme (8 LEDs)  │
│ │PHA │ │   Klingonen, Romulaner,        │  ┌───────────────┐ │
│ │TOR │ │   Sternenbasis, Sterne         │  │ Galaxiskarte  │ │
│ │... │ │   + Waffen-Effekte             │  │ 8×8 erkundet  │ │
│ └────┘ │                                │  └───────────────┘ │
├────────┴────────────────────────────────┴────────────────────┤
│  KOMMUNIKATIONSKONSOLE (Terminal-Log, grün, scrollbar)        │
│  BEFEHL? _                                                    │
└──────────────────────────────────────────────────────────────┘
```

## Komponenten

### 1. Hauptschirm (SVG-Sektorkarte)

- `viewBox 0 0 480 480`, 8×8-Zellen à 60px, dezentes Gitternetz.
- Sternenfeld: zufällige kleine Punkte mit Funkel-Animation (CSS).
- **Sprites als `<symbol>`/`<use>`**, von Hand gezeichnete SVG-Pfade:
  - `<*>` Enterprise (Untertasse + Gondeln, cyan; Schild-Glow wenn Schilde aktiv)
  - `+K+` Klingonischer D7-Kreuzer (rot) mit Mini-HP-Balken
  - `{R}` Romulanischer Warbird (magenta, Flacker-Effekt) mit Mini-HP-Balken
  - `>!<` Sternenbasis (grün, rotierender Ring)
  - ` * ` Stern (gelb-glühend)
- Datenquelle: `quadString` (192 Zeichen, unverändert) + `k[]`/`r[]` für HP.
- SRS beschädigt → Rausch-Overlay „SENSOREN AUSGEFALLEN" statt Karte.

### 2. Statuspanel (rechts)

- Sternzeit, Zustand (GRÜN/GELB/**ROT** blinkend/ANGEDOCKT), Quadrant+Name, Sektor.
- **Energie- und Schild-Balken** (Farbe kippt bei niedrigem Stand).
- **Torpedo-Pips** (10 Punkte, gefüllt/leer).
- **8 System-LEDs** (Warp, SRS, LRS, Phaser, Torpedo, Rep, Schild, Computer)
  – grün = ok, rot pulsierend = beschädigt. Ersetzt die ASCII-Schemazeichnung.
- **Mini-Galaxiskarte** 8×8 aus `exploredSpace`: aktueller Quadrant markiert,
  Klingonenzahl rot, Basis blau, unerkundet dunkel.

### 3. Befehls-Buttons (links)

- LCARS-Pills für NAV, SRS, LRS, PHA, TOR, SHE, DAM, REP, COM, TAC, TRB, XXX.
- Klick = Text ins Eingabefeld + programmatisches Enter → läuft durch das
  vorhandene `ask()`-Promise, **null Änderung an der Befehlslogik**.
- Buttons sind nur bei der `BEFEHL?`-Eingabe aktiv, sonst gedimmt
  (Zwischenfragen wie Kurs/Warpfaktor kommen weiter über die Tastatur).

### 4. Effekt-Layer (FX)

Kleine Promise-basierte Animationen direkt auf der SVG-Karte:

- `FX.phaser(von, nach, farbe)` – Strahl mit Glow, blitzt auf und verblasst.
- `FX.torpedoAt(zelle)` – leuchtender Punkt folgt der Torpedospur.
- `FX.boom(zelle)` – expandierender Explosionsring.
- Roter Alarm: pulsierender roter Rahmen um den Hauptschirm.

Eingriffe in die `Game`-Klasse sind minimal: je ein `FX.…()`-Aufruf in
`firePhasers`, `firePhotonTorpedoes`, `_klingonsAttack`, `_romulansAttack`.

### 5. Kommunikationskonsole (unten)

- Bestehendes `#terminal` + `#input-row`, eingebettet in ein LCARS-Panel.
- Grüne Monospace-Schrift bleibt (Retro-Kontrast zur LCARS-Optik).
- Alle Meldungs-Farbklassen (`m-kill`, `c-red`, …) bleiben erhalten.

## Technische Umsetzung

| Schritt | Was passiert |
|---------|--------------|
| 1 | `<style>` neu: LCARS-Farbpalette, Grid-Layout, Pills, Animationen |
| 2 | `<body>` neu: Kopfzeile, Sidebar, SVG-Viewscreen (+`<defs>`), Statuspanel, Terminal |
| 3 | Neue Funktion `renderBridge(game)`: liest Zustand, rendert Karte + Status |
| 4 | `shortRangeSensorScan()` ruft nur noch `renderBridge(this)` auf (Rückgabewert/`_srsShown`-Verhalten identisch) |
| 5 | `_enterpriseSchematic()` entfällt (ersetzt durch System-LEDs) |
| 6 | `FX`-Objekt + Hooks in den 4 Waffen-/Angriffsmethoden |
| 7 | Button-Verdrahtung über das bestehende Eingabe-Handling |

**Schriftart:** `Bahnschrift` (Windows-Systemschrift, kondensiert – sehr nah
am LCARS-Original), Fallback `Arial Narrow` / `sans-serif`.

**Farbpalette (klassisch LCARS):**
`#ff9900` Orange · `#ffcc66` Gold · `#cc99cc` Flieder · `#9999ff` Blauviolett ·
`#cc4444` Alarmrot · `#000` Hintergrund.

## Iteration 2 (nach LCARS-Referenzbild)

- **Palette** auf gedeckte TNG-Töne umgestellt (Terracotta `#cd7a5c`,
  Gold `#e9a262`, Blassblau `#a3bee3`, Mauve `#a5769d`, Pink `#d683b2`).
- **Elbow-Ecke** oben links: verbindet Kopfzeile und Sidebar (LCARS-Signaturform,
  innere Rundung per `::after`-Ausschnitt).
- **Befehle geclustert** in Funktionsgruppen mit beschrifteten Trennbalken,
  eine Farbe pro Gruppe: STEUERUNG (NAV) · SENSOREN (SRS/LRS/TAC) ·
  TAKTIK (PHA/TOR/TRB) · SCHIFF (SHE/DAM/REP/COM) · XXX separat in Rot.
- **Vertikale Warp-Messsäule** (`#warp-panel`): erscheint bei der
  `WARPFAKTOR`-Abfrage rechts im Hauptschirm. Lineal-Optik mit Skalenstrichen
  von beiden Rändern, nummerierten Hauptmarken, orangem Füllstand und
  Zieh-Daumen (Pointer-Events, touch-tauglich). Maximum wird aus dem Prompt
  geparst (0–8, bei Warpschaden 0–0.2), Wert synchron mit dem Eingabefeld.
- **Eingabezeile im LCARS-Stil**: Kontext-Pill (BEFEHL/EINGABE), Prompt in
  Gold, Eingabefeld als abgerundete Kapsel mit Orange-Rahmen und Glow,
  AUSFÜHREN-Button rechts.

## Iteration 3

- **Terminal in LCARS-Typografie**: Standardausgabe jetzt in Bahnschrift/Gold
  statt grünem Courier. `telePrint()` erkennt Tabellen/Diagramme automatisch
  (mehrfache Innenabstände, `:`-Spalten, Trennlinien) und setzt nur diese in
  Festbreitenschrift (`.line.mono`). Eingabe-Echos mit ▸-Marker,
  Meldungsfarben an die LCARS-Palette angepasst.
- **Grafische Kompassrose** (`#course-panel`): erscheint bei Kurs-Abfragen
  (NAV und Torpedo). SVG-Rose mit den 8 Kursrichtungen (1 = Ost, gegen den
  Uhrzeigersinn), leuchtendem Zeiger, per Klick/Ziehen einstellbar in halben
  Kursschritten, synchron mit dem Eingabefeld. Die ASCII-Kompass-Ausgabe
  (`_showDirections`) ist entfernt.
- **TRB-Button situativ**: nur sichtbar, solange das Tribble-Event läuft
  (`tribblesInfested`); pulsiert pink, wenn der Einsatz möglich ist
  (Klingonen im Quadranten).

## Was sich NICHT ändert

- Spielregeln, Zufallslogik, Ereignisse (Khan, Tribbles, Harry Mudd, …)
- Befehlssatz und alle Terminal-Dialoge
- `quadString`-/`galaxy`-Datenmodell, 1-basierte Koordinaten
- Start per Doppelklick, kein Server nötig
