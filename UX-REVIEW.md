# UX-Review: Super Star Trek (LCARS-GUI)

*Rolle: UX-Spezialist für Computerspiele · Stand: Juli 2026 · Basis: Playtest im Browser (Chromium, Desktop)*

## Methodik

Heuristische Evaluation (Nielsen) + Cognitive Walkthrough der Kernflows:
Spielstart → Navigation → Kampf (Phaser/Torpedo) → Schilde/Reparatur →
Computer → Spielende. Bewertet nach **Schweregrad**:
🔴 kritisch (blockiert/frustriert) · 🟡 mittel (bremst/verwirrt) · 🟢 niedrig (Politur).

## Was bereits gut funktioniert

- Klare Dauer-Sichtbarkeit des Spielzustands (Karte, Energie, Schilde, Torpedos, System-LEDs).
- Direktmanipulation bei Kurs (Kompassrose) und Warp (Messsäule) mit AUSFÜHREN direkt am Panel.
- Situativer TRB-Button (nur bei laufendem Event, pulsiert bei Einsatzbereitschaft).
- Zustands-Feedback: Roter-Alarm-Rahmen, Screen-Shake, Waffen-FX, Condition-Chip.
- Befehls-Buttons ersetzen Auswendiglernen der Drei-Buchstaben-Codes.

---

## Befunde

### 🔴 K1 — „XXX / Aufgeben" beendet das Spiel ohne Rückfrage

**Problem:** Ein einziger Fehlklick auf XXX beendet die Mission sofort und unwiderruflich.
**Heuristik:** Fehlerprävention; destruktive Aktionen brauchen eine Hürde.
**Empfehlung:** Bestätigungsdialog im LCARS-Stil („MISSION WIRKLICH ABBRECHEN? – JA / NEIN"),
alternativ Zwei-Stufen-Button (erster Klick „scharf", zweiter bestätigt, Timeout 3 s).

### 🔴 K2 — Computer-Menü (COM) ist eine Sackgasse

**Problem:** `COM` fragt endlos „COMPUTER AKTIV UND WARTET AUF BEFEHL?". Es gibt **keine
Exit-Option** – wer nur schauen wollte, muss zwangsweise eine Funktion ausführen.
Die Funktionen (0–5) sind zudem nur als Textliste nach Fehleingabe sichtbar.
**Empfehlung:** Beim COM-Aufruf die 6 Funktionen als **klickbare LCARS-Buttons**
einblenden (Overlay oder Sidebar-Submenü) + expliziter „ZURÜCK"-Button.
Menüliste sofort zeigen, nicht erst nach Fehleingabe.

### 🔴 K3 — Dialoge lassen sich nicht erkennbar abbrechen

**Problem:** In Sub-Prompts (KURS?, WARPFAKTOR?, EINHEITEN?) gibt es keinen sichtbaren
Ausstieg. Abbruch funktioniert nur über verstecktes Wissen (leere/ungültige Eingabe,
Warp 0) – das entdeckt niemand von selbst; Fehleingaben wirken wie Versagen des Spiels.
**Empfehlung:** Bei jedem Sub-Prompt einen **ABBRECHEN-Button** neben AUSFÜHREN anzeigen
(löst die bereits vorhandene Abbruch-Semantik aus). ESC-Taste als Shortcut.

### 🔴 K4 — Phaser-Energieeingabe ohne visuelle Unterstützung

**Problem:** „ANZAHL DER EINHEITEN ZUM FEUERN?" verlangt eine nackte Zahl. Inkonsistent:
Für Warp gibt es eine Säule, für die (wichtigere) Kampfentscheidung nichts.
Spieler kennen weder sinnvolle Größenordnungen noch die Konsequenz für die Restenergie.
**Empfehlung:** **Energie-Säule** analog zur Warp-Säule: Maximum = verfügbare Energie,
Marker für Restenergie-Vorschau, Schnellwahl-Pills (10 % / 25 % / 50 % / ALLES).
Faustregel-Hinweis („~200 pro Ziel bei mittlerer Distanz") als Subtext.

### 🔴 K5 — Schildsteuerung (SHE) ebenso blind

**Problem:** Gleiches Muster: Zahleneingabe ohne Kontext. Dass Schilde von der
Hauptenergie abgezweigt werden, ist nicht erkennbar – zentrale Spielmechanik!
**Empfehlung:** **Transfer-Anzeige**: eine Säule/Slider mit zwei Zonen
(Energie ↔ Schilde), die die Umverteilung live visualisiert; Warnschwelle
(< 200 Schilde = „GEFÄHRLICH NIEDRIG") farblich markieren.

---

### 🟡 M1 — J/N-Fragen als Freitexteingabe

„BENÖTIGEN SIE ANLEITUNG (J/N)?", „REPARATURAUFTRAG (J/N)?" – Tippen statt Klicken.
**Empfehlung:** Generisches Choice-UI: bei J/N-Prompts zwei LCARS-Buttons
(JA/NEIN) neben der Eingabezeile einblenden (Erkennung per `(J/N)` im Prompt).

### 🟡 M2 — Kein Hilfe-Zugriff nach Spielstart

Die Anleitung gibt es genau einmal – vor dem Start, als Textwand. Wer im Spiel
etwas nachschlagen will, hat keine Chance.
**Empfehlung:** Dauerhafter **HILFE-Button** (Sidebar unten oder `?`-Chip in der
Kopfzeile) mit Overlay: Befehlsreferenz, Kurssystem, Legende. Textwand in
Abschnitte mit Zwischenüberschriften gliedern.

### 🟡 M3 — Sektorkarte ist nicht interaktiv

Gegner sind sichtbar, aber nicht anklickbar. Für einen Torpedo muss der Spieler
den Kurs im Kopf (oder via COM-Rechner) ermitteln – die Maschine könnte das.
**Empfehlung:** **Click-to-Target**: Klick auf einen Gegner während der
Torpedo-/Kurs-Abfrage berechnet den Kurs automatisch (Rechenlogik existiert in
`_calcAndPrintDirection`). Hover zeigt Sektor-Koordinaten + Distanz als Tooltip.

### 🟡 M4 — Log wird bei jedem Befehl gelöscht

`clearScreen()` leert das Terminal vor jedem Befehl. Wer eine Meldung verpasst
(z. B. „GERÄT BESCHÄDIGT" während einer Angriffsserie), kann nicht zurückscrollen.
**Empfehlung:** Scrollback behalten (Log anhängen statt löschen, optisch per
Trennlinie gruppieren) **oder** wichtige Ereignisse zusätzlich persistent
anzeigen (M5).

### 🟡 M5 — Kritische Ereignisse gehen im Log unter

„KLINGONE VERNICHTET", Geräteausfälle und Treffer erscheinen nur als Logzeile
gleichberechtigt neben Smalltalk.
**Empfehlung:** Kurzzeit-**Banner auf dem Hauptschirm** (Toast, 2–3 s) für:
Abschüsse, eigene Treffer, Geräteausfall, Sternenbasis-Ereignisse. Das Log
bleibt als Protokoll erhalten.

### 🟡 M6 — Warp ohne Kosten-/Folgen-Vorschau

Warp kostet Energie und Zeit (Sterndaten) – beides erfährt der Spieler erst
hinterher. Bei knapper Energie ist das spielentscheidend.
**Empfehlung:** Im Warp-Panel live anzeigen: „KOSTET ~N ENERGIE · +0.X STERNZEIT",
Restenergie-Vorschau im Energie-Balken (Geisterbalken).

### 🟡 M7 — Legenden fehlen (Galaxiskarte, HP-Balken, Kürzel)

Rote/rosa Ziffern und blaue Punkte in der Mini-Galaxiskarte, HP-Balken unter
Gegnern, „GEGNER 8 K · 9 R" – alles unbeschriftet.
**Empfehlung:** Mini-Legende unter der Galaxiskarte (K = Klingonen, R = Romulaner,
● = Sternenbasis); Tooltips auf Kartenzellen sind vorhanden, aber unentdeckbar →
Hinweis in der Hilfe. „GEGNER"-Zeile ausschreiben oder Tooltip.

### 🟡 M8 — Deaktivierte Befehls-Buttons ohne Begründung

Während Sub-Prompts sind alle Befehle ausgegraut – warum, sieht man nicht.
**Empfehlung:** Tooltip/Hinweiszeile („Erst aktuelle Eingabe abschließen oder
abbrechen"); zusammen mit K3 (ABBRECHEN) verliert das Problem seinen Schrecken.

### 🟡 M9 — Schadensdetails nur auf Umwegen

Die System-LEDs zeigen rot/grün, aber nicht *wie schwer* der Schaden ist oder
wie lange die Reparatur dauert – dafür muss man DAM ausführen (kostet einen Zug?).
**Empfehlung:** Tooltip auf jeder LED mit Schadenswert/Restdauer; LED-Klick
öffnet den Schadensbericht.

---

### 🟢 N1 — Kein Mute / keine Lautstärke

Beeps sind nett, aber nicht abschaltbar. → Sound-Toggle in der Kopfzeile.

### 🟢 N2 — Barrierefreiheit

Status nur über Farbe (LEDs, Condition), teils niedrige Kontraste (gedimmte
Buttons), Fokus liegt immer im Eingabefeld – Buttons sind per Tastatur schwer
erreichbar. → Zusätzliche Symbole/Text zu Farben, `aria-live` für Banner,
Tab-Reihenfolge prüfen, Kontrast der Disabled-States anheben.

### 🟢 N3 — Kleine Viewports

Unter ~1000 px wird es eng, unter ~800 px unbenutzbar; Touch-Ziele in der
Sidebar sind grenzwertig klein. → Responsives Stacking (Status unter die Karte),
Mindesthöhe 44 px für Touch-Buttons.

### 🟢 N4 — Spielende ohne Bilanz

Sieg/Niederlage endet mit zwei Textzeilen. → Endscreen-Overlay mit Statistik
(Abschüsse, verbrauchte Sterndaten, Effizienz-Rating wie im BASIC-Original,
„Neues Spiel"-Button prominent).

### 🟢 N5 — TRB erscheint unkommentiert

Der Button taucht beim Tribble-Event plötzlich auf; wer das Event-Log verpasst
hat, kennt seine Funktion nicht. → Einmaliger Hinweis-Toast beim ersten
Erscheinen („NEU: TRB – Tribbles auf Klingonenschiff beamen").

### 🟢 N6 — Distanz-/Treffer-Info im Kampf

Phaser-Wirkung hängt stark von der Distanz ab – nirgends sichtbar.
→ Beim Hover über Gegner Distanz anzeigen; optional grobe Wirksamkeit
(„nah/mittel/fern").

---

## Priorisierte Todo-Liste

### P1 – Quick Wins & Kritisches (zuerst)

- [x] **XXX-Bestätigung**: Confirm-Dialog vor Missionsabbruch (K1) ✅ *umgesetzt*
- [x] **ABBRECHEN-Button** bei allen Sub-Prompts + ESC-Shortcut (K3) ✅ *umgesetzt*
- [x] **COM-Menü als Buttons** mit ZURÜCK-Option, Menü sofort zeigen (K2) ✅ *umgesetzt*
- [x] **JA/NEIN-Buttons** bei `(J/N)`-Prompts (M1) ✅ *umgesetzt (im Zuge von K1)*
- [ ] **Legende** für Galaxiskarte + Gegner-Kürzel (M7)

### P2 – Konsistenz & Kampf-UX

- [x] **Energie-Säule für Phaser** mit Presets und Restenergie-Vorschau (K4) ✅ *umgesetzt*
- [x] **Transfer-Anzeige für Schilde** (K5) ✅ *umgesetzt*
- [ ] **Click-to-Target** auf der Sektorkarte für Torpedo/Kurs (M3)
- [ ] **Warp-Kostenvorschau** im Warp-Panel (M6)
- [ ] **Ereignis-Banner** auf dem Hauptschirm für Abschüsse/Ausfälle (M5)
- [ ] **Log-Scrollback** statt Löschen pro Befehl (M4)

### P3 – Komfort & Politur

- [ ] **HILFE-Overlay** dauerhaft erreichbar (M2)
- [ ] **LED-Tooltips** mit Schadensdetails, Klick → DAM (M9)
- [ ] **Hinweis bei ausgegrauten Buttons** (M8)
- [ ] **Sound-Toggle** (N1)
- [ ] **A11y-Pass**: Farbe+Symbol, Kontraste, Tastatur, aria-live (N2)
- [ ] **Responsive-Pass** für kleine Viewports/Touch (N3)
- [ ] **Endscreen mit Statistik** und Effizienz-Rating (N4)
- [ ] **Erst-Hinweis für TRB**-Button (N5)
- [ ] **Distanzanzeige** beim Hover über Gegner (N6)

---

*Empfohlene Reihenfolge: P1 komplett (geringer Aufwand, hoher Frust-Abbau),
dann K4/K5/M3 als zusammenhängendes „Kampf-UX-Paket", Rest nach Gelegenheit.*
