# Sonderereignisse (Special Events)

Dokumentation der Logik aller Sonderereignisse in `superstartrek.html`.

Alle Ereignisse werden zentral in der Methode **`_checkSpecialEvents()`** ausgewertet.
Diese wird bei **jedem Eintritt in einen neuen Quadranten** aufgerufen
(siehe `superstartrek.html:2041`, innerhalb der Hauptschleife nach einem Warp-/Quadrantenwechsel).

## Initialisierung

In `_initGalaxy()` (`superstartrek.html:560-567`) werden die vier ortsgebundenen
Ereignisse zu Spielbeginn auf je einen **zufälligen, eindeutigen** Quadranten gelegt.
Sie unterscheiden sich vom Startquadranten der Enterprise **und voneinander**
(`_randomUniqueQuadrant(taken)`).

| Variable | Standardwert | Zweck |
|----------|--------------|-------|
| `harryMuddQuadrant`  | `[0,0]` → zufällig | Ort des Harry-Mudd-Ereignisses |
| `vulcanShipQuadrant` | `[0,0]` → zufällig | Ort des Vulkanier-Ereignisses |
| `traderQuadrant`     | `[0,0]` → zufällig | Ort von Cyrano Jones |
| `ponFarrQuadrant`    | `[0,0]` → zufällig | Ort des Pon-Farr-Ereignisses |
| `tribblesInfested`   | `false` | Tribble-Zustand (Folge-Effekt) |
| `scottyCaptured`     | `false` | Scotty-Entführungs-Zustand |
| `scottyCapturedInQuadrant` | `[0,0]` | Entführungsort (für Befreiung) |

**Verbrauchsmuster:** Ein ortsgebundenes Ereignis feuert genau einmal. Sobald die
Enterprise den passenden Quadranten betritt, wird der Quadrant des Ereignisses auf
`[0,0]` zurückgesetzt – damit kann es nicht erneut auslösen.

---

## 1. Harry Mudd — Energiediebstahl

**Quelle:** `superstartrek.html:1767-1778`

| | |
|---|---|
| **Auslöser** | Enterprise betritt `harryMuddQuadrant` |
| **Typ** | Ortsgebunden, einmalig |
| **Effekt** | Stiehlt **10 % der aktuellen Energie** (mindestens 1 Einheit) |

**Logik:**
1. `harryMuddQuadrant` → `[0,0]` (verbraucht).
2. `stolen = max(1, floor(energyLevel * 0.10))`.
3. `energyLevel = max(0, energyLevel - stolen)`.
4. Meldung + Sound (`beep`).

Der berüchtigte Schwindler geht unbemerkt an Bord und zapft die Reserven an.
Rein negatives Ereignis, keine Gegenwehr möglich.

---

## 2. Vulkanisches Forschungsschiff — Reparatur & Auftanken

**Quelle:** `superstartrek.html:1781-1797`

| | |
|---|---|
| **Auslöser** | Enterprise betritt `vulcanShipQuadrant` |
| **Typ** | Ortsgebunden, einmalig |
| **Effekt** | Repariert **alle** Systeme, +500 Energie, beseitigt Tribbles |

**Logik:**
1. `vulcanShipQuadrant` → `[0,0]` (verbraucht).
2. Alle beschädigten Geräte reparieren: für `i = 1..8`, wenn `damageLevel[i] < 0` → `0`.
3. `energyLevel = min(maxEnergyLevel, energyLevel + 500)`.
4. Falls `tribblesInfested`: auf `false` setzen (Vulkanier helfen bei der Plage).

Rein positives Ereignis („Leben Sie lang und in Frieden"). Bietet u. a. eine
Möglichkeit, eine Tribble-Plage ohne Klingonen loszuwerden.

---

## 3. Cyrano Jones (Händler) — Torpedos & Tribble-Risiko

**Quelle:** `superstartrek.html:1800-1821`

| | |
|---|---|
| **Auslöser** | Enterprise betritt `traderQuadrant` |
| **Typ** | Ortsgebunden, einmalig |
| **Effekt** | Füllt Photonentorpedos voll auf; **50 % Chance** auf Tribble-Befall |

**Logik:**
1. `traderQuadrant` → `[0,0]` (verbraucht).
2. `added = maxTorpedoes - floor(photonTorpedoes)`; `photonTorpedoes = maxTorpedoes`.
3. Mit **50 % Wahrscheinlichkeit** (`Math.random() < 0.50`):
   - `tribblesInfested = true`
   - Warnung: Tribbles verbrauchen 200 Energie pro Warpsprung; Tipp `TRB` nutzen.
4. Sonst: freundlicher Abschied, kein Nachteil.

Gemischtes Ereignis: garantierter Nutzen (Torpedos), riskanter Nebeneffekt (Tribbles).

---

## 4. Pon Farr (Mr. Spock) — Bibliothekscomputer-Ausfall

**Quelle:** `superstartrek.html:1823-1839`

| | |
|---|---|
| **Auslöser** | Enterprise betritt `ponFarrQuadrant` |
| **Typ** | Ortsgebunden, einmalig |
| **Effekt** | Bibliothekscomputer (Gerät 8) für ~3 Sterndaten beschädigt |

**Logik:**
1. `ponFarrQuadrant` → `[0,0]` (verbraucht).
2. Wenn `damageLevel[8] < -3.0` (bereits stärker beschädigt):
   - Schaden **nicht** verschlimmern (Hinweismeldung).
3. Sonst: `damageLevel[8] = -3.0` (negativ = beschädigt; betragsmäßig ~3 Sterndaten).

Spock geht ins Pon Farr und stellt vorher den Bibliothekscomputer auf vulkanische
Lyrik um → temporärer Ausfall des Bibliothekscomputers.

---

## 5. Scotty-Entführung — zufällig bei Klingonen-Kontakt

**Quelle:** `superstartrek.html:1842-1873`

| | |
|---|---|
| **Auslöser** | Quadrant mit Klingonen (`k3 > 0`), Scotty noch frei, **15 % Chance** |
| **Typ** | Zufallsereignis (nicht ortsgebunden), einmalig pro Spiel |
| **Effekt** | Ein Klingonenschiff verschwindet **mit** Scotty als Geisel |

**Bedingung:** `k3 > 0 && !scottyCaptured && Math.random() < 0.15`.

**Logik:**
1. Ersten aktiven Klingonen finden (`k[i][2] > 0`).
2. `scottyCaptured = true`; `scottyCapturedInQuadrant = [q1, q2]` merken.
3. Das Klingonenschiff aus dem Quadranten-String entfernen, `k[i][2] = 0`,
   `k3--`, `totalKlingonShips--`.
4. `galaxy` und `exploredSpace` für den Quadranten neu kodieren; Schiffsstatus prüfen.
5. Warnmeldungen über die Folgen.

**Folge-Effekte solange `scottyCaptured`:**

| Bereich | Effekt | Quelle |
|---------|--------|--------|
| Basis-Reparatur | Dauert **30 % länger** (`timeToRepair * 1.3`) | `superstartrek.html:886-889` |
| Notfallreparatur (`REP`) | **Doppelte** Energiekosten (`costFactor = 2`) | `superstartrek.html:924-955` |

Das Klingonenschiff zählt als „besiegt" (Geisel statt Vernichtung) – es wird aus
Galaxis und Zähler entfernt, taucht aber nicht anderswo wieder auf.

---

## 6. Scotty-Befreiung

**Quelle:** `_checkScottyRescue()` — `superstartrek.html:1880-1894`

| | |
|---|---|
| **Auslöser** | Letztes Klingonenschiff in einem **anderen** Quadranten vernichtet |
| **Effekt** | Scotty kehrt zurück; Reparaturkosten wieder normal |

**Logik:**
1. Wenn `!scottyCaptured` → sofort beenden.
2. Wenn aktueller Quadrant == `scottyCapturedInQuadrant` → **nicht** befreien
   (muss ein anderer Quadrant sein).
3. Sonst: `scottyCaptured = false`, `scottyCapturedInQuadrant = [0,0]`, Erfolgsmeldung.

**Aufrufstellen** (immer nach Klingonen-Vernichtung, wenn `k3 === 0`):
- Nach Phaser-/Torpedotreffer (`superstartrek.html:1576`, `1657`)
- Nach Tribble-Transfer in `beamTribbles()` (`superstartrek.html:1757`)

---

## 7. Space Seed (Khan) — Teilübernahme des Schiffs

**Quelle:** `superstartrek.html:1766-1815` (innerhalb `_checkSpecialEvents()`)

| | |
|---|---|
| **Auslöser** | Enterprise betritt `khanQuadrant` |
| **Typ** | Ortsgebunden (Entdeckung), danach anhaltender Zustand `khanInControl` |
| **Effekt** | Khan sabotiert pro Quadrantenwechsel ein System + zapft Energie ab |

**Entdeckung (ortsgebunden, einmalig):**
1. `khanQuadrant` → `[0,0]` (verbraucht).
2. `khanInControl = true`.
3. `khanJumpsRemaining = 2 + floor(random*7)` → **zufällig 2–8** Quadrantenwechsel.
4. Narrativ: SS Botany Bay wird entdeckt, Khan Noonien Singh erwacht und übernimmt
   mit seinen Augments die Teilkontrolle.

**Anhaltender Effekt — pro folgendem Quadrantenwechsel** (Block läuft **vor** den
Auslöse-Blocks, damit der Entdeckungs-Sprung selbst keinen Countdown verbraucht):
1. `khanJumpsRemaining--`.
2. Falls noch `> 0`: **Sabotage**
   - Zufälliges Gerät aus `{1,2,3,4,5,7,8}` (Schadenskontrolle Nr. 6 **ausgenommen**,
     damit Reparaturen immer möglich bleiben). Wenn intakt → `damageLevel[dev] = -(2..4)`.
   - `energyLevel -= 150` (min. 0).
3. Falls `<= 0`: **Auflösung** (siehe unten).

**Auflösung (automatisch nach 2–8 Wechseln):**
- Es wird ein bewohnbarer Planet im **aktuellen** Quadranten gefunden.
- Planetenname = `_getQuadrantName(q1, q2, true)` (Regionsname, z. B. „ANTARES") + `' V'`
  → z. B. **„ANTARES V"** (analog zu „Ceti Alpha V").
- Khan und seine Crew werden mit der SS Botany Bay dort ausgesetzt, um eine eigene
  Gesellschaft zu gründen. `khanInControl = false`, Sabotage endet.

Hinweis: Die Auflösung erfordert, dass die Enterprise tatsächlich weiterspringt — bleibt
sie im selben Quadranten, hält Khans Kontrolle an (es erfolgt jedoch auch keine Sabotage,
da diese nur bei Quadrantenwechseln auslöst).

---

## Tribbles — Folge-Effekt (kein eigenständiges Ereignis)

Tribbles sind kein ortsgebundenes Ereignis, sondern ein **Zustand** (`tribblesInfested`),
ausgelöst durch Cyrano Jones (50 %).

**Effekt:** Bei jedem Quadrantenwechsel −200 Energie
(`_endOfMovementInQuadrant`, `superstartrek.html:1175-1179`).

**Beseitigung:**

| Weg | Quelle |
|-----|--------|
| Vulkanier-Ereignis | `superstartrek.html:1791-1794` |
| `TRB`-Befehl (`beamTribbles`) – auf Klingonenschiff beamen | `superstartrek.html:1734-1760` |

**`beamTribbles()` (`TRB`):** Voraussetzung `tribblesInfested` **und** `k3 > 0`.
Alle aktiven Klingonen im Quadranten werden „von Tribbles überwältigt" und vernichtet
(`k3 = 0`, `totalKlingonShips` reduziert), Galaxis neu kodiert, `tribblesInfested = false`.
Anschließend Prüfung auf Sieg bzw. Scotty-Befreiung.

---

## Zusammenfassung

| # | Ereignis | Typ | Auslöser | Effekt |
|---|----------|-----|----------|--------|
| 1 | Harry Mudd | ortsgebunden | Quadrant betreten | −10 % Energie |
| 2 | Vulkanier | ortsgebunden | Quadrant betreten | Volle Reparatur, +500 Energie, Tribbles weg |
| 3 | Cyrano Jones | ortsgebunden | Quadrant betreten | Torpedos voll; 50 % Tribbles |
| 4 | Pon Farr | ortsgebunden | Quadrant betreten | Bibliothekscomputer ~3 Sterndaten defekt |
| 5 | Scotty-Entführung | zufällig (15 %) | Klingonen + Scotty frei | Geisel; Reparaturen teurer/langsamer |
| 6 | Scotty-Befreiung | bedingt | Letzter Klingone in anderem Quadrant besiegt | Zustand normalisiert |
| 7 | Space Seed (Khan) | ortsgebunden → Zustand | Quadrant betreten | Sabotage + −150 Energie/Sprung; löst sich nach 2–8 Sprüngen (Crew ausgesetzt auf „<REGION> V") |
| – | Tribbles | Zustand | Folge von #3 | −200 Energie / Warpsprung |
