# Super Star Trek – Handbuch

> Du übernimmst das Kommando über die USS Enterprise NCC-1701. Irgendwo da draußen lauern Klingonen. Viel Glück, Captain.

---

## Starten

```
python superstartrek.py
```
oder Doppelklick auf `run.bat`.

---

## Das Universum

Die Galaxis ist ein **8×8-Raster aus Quadranten**. Jeder Quadrant ist nochmal in **8×8 Sektoren** unterteilt – dort bewegt sich die Enterprise auf Impulsantrieb.

Was du im Sektor siehst:

| Symbol | Bedeutung |
|--------|-----------|
| `<*>` | Enterprise (du) |
| `+K+` | Klingonen-Kampfkreuzer |
| `{R}` | Romulanischer Warbird (sichtbar) |
| `>!<` | Sternenflottenbasis |
| ` * ` | Stern (unbeweglich, blockiert Torpedos) |

**Ziel:** Alle Klingonen **und** romulanischen Warbirds vernichten, bevor die Zeit abläuft.

---

## Befehle

Eingabe immer GROSS. Nach `COMMAND?` tippen.

### `NAV` – Kurs und Warp

Bewegt die Enterprise. Kurs 1–8 (oder 9 = 1), Warp 0.1–8.
Warp 1 = eine Quadrantenlänge. Je schneller, desto mehr Energie.

```
Kurssystem:
  4  3  2
   \ | /
    \|/
5 ---*--- 1
    /|\
   / | \
  6  7  8
```

Beispiel – eine Quadrantenlänge nach rechts (Kurs 1, Warp 1):

```
COMMAND? NAV
COURSE (0-9) :1
WARP FACTOR (0-8)? 1

NOW ENTERING 'RIGEL II' QUADRANT . . .

---------------------------------
    +K+      *           *          STARDATE           2143.0
                   <*>              CONDITION          *RED*
                                    QUADRANT           3 , 5
         *                          SECTOR             4 , 6
                                    PHOTON TORPEDOES   10
                                    TOTAL ENERGY       2972
                                    SHIELDS            500
                                    KLINGONS REMAINING 11
---------------------------------
```

> **Tipp:** Warp 0.2–0.9 spart Energie, braucht aber mehrere NAV-Befehle bis zum Ziel.

### `SRS` – Kurzstrecken-Scan

Zeigt den aktuellen Quadranten + Statusleiste: Energie, Schilde, Torpedos, Stardate, Zustand des Schiffes.

**Condition:**
- `GREEN` – alles normal
- `YELLOW` – Energie unter 10 %
- `*RED*` – Klingonen im Quadrant
- `DOCKED` – angedockt an Basis (Schiff wird vollständig aufgefüllt)

Beispiel:

```
COMMAND? SRS

---------------------------------
         *        +K+             STARDATE           2131.0
                                  CONDITION          *RED*
   <*>             *              QUADRANT           2 , 4
                                  SECTOR             3 , 1
      *                           PHOTON TORPEDOES   10
                                  TOTAL ENERGY       2840
            *                     SHIELDS            300
                                  KLINGONS REMAINING 12
---------------------------------
```

### `LRS` – Langstrecken-Scan

Zeigt die 3×3 Quadranten um die Enterprise herum. Format: `KBS` (K = Klingonen, B = Basen, S = Sterne).
`207` bedeutet 2 Klingonen, keine Basis, 7 Sterne.

Beispiel:

```
COMMAND? LRS

LONG RANGE SCAN FOR QUADRANT 2,4
-------------------
: *** : 003 : 104 :
-------------------
: 002 : 006 : 207 :
-------------------
: *** : 011 : 001 :
-------------------
```

Die Enterprise steht in der Mitte (`006` = kein Klingone, keine Basis, 6 Sterne).
Rechts oben (`104`) lauern 1 Klingone und eine Basis – lohnt sich.

### `PHA` – Phaser

Feuert Phaserenergie auf alle Klingonen im Quadrant. Du gibst die Energiemenge an – die wird gleichmäßig aufgeteilt. Entfernung spielt eine Rolle: je näher der Feind, desto mehr Schaden.

Beispiel – 800 Einheiten auf zwei Klingonen:

```
COMMAND? PHA
PHASERS LOCKED ON TARGET;
ENERGY AVAILABLE = 2340 UNITS
NUMBER OF UNITS TO FIRE? 800

412 UNITS HIT ON KLINGON AT SECTOR 2,6
   (SENSORS SHOW 87 UNITS REMAINING)
388 UNITS HIT ON KLINGON AT SECTOR 6,3
*** KLINGON DESTROYED ***

KLINGON SHIPS ATTACK THE ENTERPRISE
143 UNIT HIT ON ENTERPRISE FROM SECTOR 2,6
      <SHIELDS DOWN TO 157 UNITS>
```

### `TOR` – Photonentorpedo

Feuert einen Torpedo in eine Richtung (Kurs 1–9). Trifft er einen Klingonen, ist der sofort zerstört. Trifft er einen Stern, wird er absorbiert. Eine Basis zu treffen ist sehr, sehr unklug.

Beispiel – Torpedo Kurs 2 (oben rechts):

```
COMMAND? TOR
PHOTON TORPEDO COURSE (1-9)? 2
TORPEDO TRACK:
               3 , 6
               2 , 7
               2 , 8
*** KLINGON DESTROYED ***

KLINGON SHIPS ATTACK THE ENTERPRISE
... (keine weiteren Klingonen im Quadrant)
```

Beispiel – Torpedo verfehlt:

```
PHOTON TORPEDO COURSE (1-9)? 3
TORPEDO TRACK:
               3 , 4
               2 , 4
               1 , 4
TORPEDO MISSED!
```

> Torpedos kosten keine Energie, aber du hast nur 10 Stück. Nachfüllen nur an einer Basis.

### `SHE` – Schilde

Legt Energie in die Schilde. Schildenergie und Schiffsenergie teilen sich denselben Pool.
Ohne Schilde wird jeder Treffer direkt deinen Energievorrat verringern – und dich töten.

Beispiel – Schilde auf 500 setzen:

```
COMMAND? SHE
ENERGY AVAILABLE = 2840
NUMBER OF UNITS TO SHIELDS? 500
DEFLECTOR CONTROL ROOM REPORT:
  'SHIELDS NOW AT 500.0 UNITS PER YOUR COMMAND.'
```

Beispiel – Schilde bereits auf diesem Wert:

```
NUMBER OF UNITS TO SHIELDS? 500
<SHIELDS UNCHANGED>
```

### `DAM` – Schadenskontrolle

Zeigt den Zustand aller 8 Bordsysteme. Negative Werte = beschädigt.
Wenn du an einer Basis andockst, kannst du reparieren lassen (kostet Stardates).

Beispiel – kein Schaden:

```
COMMAND? DAM

DEVICE             STATE OF REPAIR
WARP ENGINES               0.0
SHORT RANGE SENSORS        0.0
LONG RANGE SENSORS         0.0
PHASER CONTROL             0.0
PHOTON TUBES              -2.4
DAMAGE CONTROL             0.0
SHIELD CONTROL             0.0
LIBRARY-COMPUTER           0.0
```

Beispiel – an Basis angedockt, Reparatur angeboten:

```
TECHNICIANS STANDING BY TO EFFECT REPAIRS TO YOUR SHIP;
ESTIMATED TIME TO REPAIR: 0.3 STARDATES
WILL YOU AUTHORIZE THE REPAIR ORDER (Y/N) ? Y
REPAIR COMPLETED.
```

### `COM` – Bordcomputer

Sechs Unteroptionen (Eingabe: `0`–`5`):

| Option | Funktion |
|--------|----------|
| `0` | Kumulative Galaktische Karte (alle gescannten Quadranten) |
| `1` | Statusbericht (Klingonen, Basen, Stardates) |
| `2` | Torpedodaten (Kurs und Entfernung zu Klingonen) |
| `3` | Basiskurs (Richtung zur nächsten Basis) |
| `4` | Kurs-/Entfernungsrechner |
| `5` | Galaktische Regionskarte |

Beispiel – Statusbericht (Option 1):

```
COMMAND? COM
COMPUTER ACTIVE AND AWAITING COMMAND? 1

   STATUS REPORT:
KLINGONS LEFT: 9
MISSION MUST BE COMPLETED IN 18.0 STARDATES
THE FEDERATION IS MAINTAINING 2 STARBASES IN THE GALAXY
```

Beispiel – Torpedodaten (Option 2), Enterprise bei Sektor 3,1:

```
COMPUTER ACTIVE AND AWAITING COMMAND? 2

FROM ENTERPRISE TO KLINGON BATTLE CRUISERS:
 DIRECTION = 1.74
 DISTANCE = 4.47
 DIRECTION = 6.12
 DISTANCE = 2.83
```

Beispiel – Kurs-/Entfernungsrechner (Option 4):

```
COMPUTER ACTIVE AND AWAITING COMMAND? 4

DIRECTION/DISTANCE CALCULATOR:
YOU ARE AT QUADRANT 2,4 SECTOR 3,1
PLEASE ENTER INITIAL COORDINATES (row,col): 3,1
  FINAL COORDINATES (row,col): 6,5
 DIRECTION = 1.63
 DISTANCE = 5.0
```

### `TAC` – Tachyon-Scan

Kostet **50 Energie**. Enttarnt alle getarnten Romulaner im aktuellen Quadrant dauerhaft für diese Runde.

- Nur sinnvoll wenn der LRS Romulaner im Quadrant anzeigt, aber `SRS` keinen `{R}` zeigt
- Nach dem Scan werden enttarnte Romulaner als `{R}` angezeigt und können normal bekämpft werden

```
COMMAND? TAC
TACHYON PULSE INITIATED . . .
TACHYON SCAN REVEALS 1 CLOAKED ROMULAN WARBIRD — NOW EXPOSED
   (1 FURTHER WARBIRD ALREADY VISIBLE)
```

---

### `TRB` – Tribbles beamen

Überträgt die Tribble-Plage aufs Klingonenschiff. **Zerstört alle Klingonen** im aktuellen Quadrant auf einen Schlag und befreit die Enterprise von den Tribbles.

- Nur verfügbar wenn Tribbles an Bord **und** mindestens ein Klingone im Quadrant
- Funktioniert nicht gegen Romulaner

```
COMMAND? TRB
TRANSPORTER ROOM: BEAMING TRIBBLES TO KLINGON VESSEL . . .
*** KLINGON AT SECTOR 3,5 OVERWHELMED BY TRIBBLES — DESTROYED ***
ENTERPRISE IS NOW TRIBBLE-FREE!
```

---

### `XXX` – Aufgeben

Beendet das Spiel. Kein Urteil.

```
COMMAND? XXX

THERE WERE 7 KLINGON BATTLE CRUISERS LEFT AT
THE END OF YOUR MISSION, IN STARDATE 2149.0

Thank you for playing this game!
```

---

## Romulaner

Romulaner sind listig und gefährlich. Im Gegensatz zu Klingonen verfügen sie über **Tarnvorrichtungen**.

### Tarnmechanik

- **Beim Einflug** startet jeder Romulaner mit 50 % Wahrscheinlichkeit getarnt (unsichtbar, nicht treffbar)
- Getarnte Romulaner verbrauchen pro Runde **15 Energie**; läuft ihre Energie aus, werden sie zerstört
- **10 % Chance** pro Runde: Tarnfeld bricht unfreiwillig zusammen – Romulaner wird sichtbar mit Meldung
- Sichtbare Romulaner tarnen sich nach dem Angriff mit **70 % Wahrscheinlichkeit** sofort wieder
- Phasern und Torpedos können **nicht** auf getarnte Romulaner abgefeuert werden
- Nutze `TAC` (Tachyon-Scan, 50 Energie) um alle Getarnten im Quadrant aufzudecken

### LRS-Hinweis

Der Langstrecken-Scan zeigt Romulaner mit leichten Anzeigefehlern (±1) – eine Täuschungsmaßnahme.

### Hinterhalt

Wenn ein Romulaner in dieser Runde enttarnt wird (Malfunction, TAC oder natürlich sichtbar beginnend) und **sofort danach** angreift, kann er Doppelschaden verursachen. Schilde hochhalten!

---

## Zufallsereignisse

Beim Spielstart werden **drei Quadranten** zufällig mit Sonderereignissen belegt. Du weißt nicht welche – du fliegst hinein und das Ereignis löst sich aus.

### Harry Mudd

Der berüchtigte Schwindler beamt sich unentdeckt an Bord und stiehlt **10 % deiner aktuellen Energie**.

```
*** HARRY MUDD APPEARS ON THE VIEWSCREEN! ***
THE NOTORIOUS CON MAN HAS BEAMED ABOARD UNDETECTED AND ACCESSED
THE SHIP'S ENERGY RESERVES -- 300 UNITS STOLEN!
ENERGY NOW AT 2700 UNITS.
```

### Vulkanisches Forschungsschiff

Ein vulkanischer Kreuzer bietet Hilfe an:
- **Alle beschädigten Systeme** werden sofort repariert
- **+500 Energie** (bis zum Maximum)
- Falls Tribbles an Bord: werden ebenfalls entfernt

```
*** A VULCAN SURVEY VESSEL HAILS THE ENTERPRISE ***
'LIVE LONG AND PROSPER, CAPTAIN. OUR SENSORS DETECT
 DAMAGE ABOARD YOUR VESSEL. WE OFFER ASSISTANCE.'
ALL DAMAGED SYSTEMS HAVE BEEN REPAIRED.
500 ENERGY UNITS TRANSFERRED. ENERGY NOW AT 1300 UNITS.
```

### Cyrano Jones – Händler

Der Hausierer füllt deine **Torpedovorräte auf Maximum** auf. Klingt gut – aber:

- **50 % Chance:** Tribbles haben sich unter seiner Ware versteckt und befallen das Schiff
- Bei Tribble-Befall: jeder Warp-Sprung kostet **zusätzlich 200 Energie**
- Nutze `TRB` wenn Klingonen im Quadrant sind, um die Tribbles loszuwerden (und die Klingonen gleich mit)
- Das Vulkanische Schiff entfernt Tribbles ebenfalls

```
*** CYRANO JONES HAILS THE ENTERPRISE ***
'I HAVE GOODS TO TRADE, CAPTAIN — INCLUDING TORPEDO SUPPLIES.'
5 TORPEDOES RESTOCKED. TUBES NOW FULL (10 TOTAL).
*** TRIBBLES DETECTED ABOARD THE ENTERPRISE! ***
THE LITTLE CREATURES HAVE SPREAD EVERYWHERE.
ENGINEERING: THEY DRAIN 200 ENERGY PER WARP JUMP.
TIP: USE 'TRB' WHEN KLINGONS ARE PRESENT TO BEAM THEM OVER!
```

---

## Energie & Überleben

Die Enterprise startet mit **3000 Energieeinheiten** (Schilde + Antrieb + Waffen teilen sich diesen Pool).

- Bewegen kostet: `Warp × 8 + 10` Einheiten pro NAV-Befehl
- Phasern kostet: so viel wie du angibst
- Torpedos kosten: 2 Einheiten pro Schuss
- Tachyon-Scan (`TAC`): 50 Einheiten
- Tribble-Befall: zusätzlich 200 Einheiten pro Warp-Sprung
- Andocken an einer `>!<`-Basis füllt alles wieder auf

> Wenn Energie + Schilde ≤ 10, ist das Spiel verloren – die Enterprise treibt dann antriebslos.

---

## Schaden

Systeme können durch Klingonen-Treffer beschädigt werden (negativer Repair-Wert).
Beschädigte Systeme:

- **Warpantrieb** – Maximalwarp: 0.2
- **Kurzstreckensensoren** – SRS zeigt nichts
- **Langstreckensensoren** – LRS nicht nutzbar
- **Phaser** – nicht feuerfähig
- **Torpedorohre** – keine Torpedos
- **Schadenskontrolle** – DAM-Report nicht verfügbar
- **Schildsteuerung** – keine Schilde einstellbar
- **Computer** – PHA ungenauer, COM deaktiviert

Reparatur passiert **automatisch beim Reisen** (Warp 1 = 1 Reparaturpunkt pro System und Tag).

---

## Zeitlimit

Die Uhr tickt. Jede NAV-Bewegung kostet mindestens 1 Stardate. Reparaturen kosten ebenfalls Zeit.  
Läuft die Zeit ab, hat die Föderation verloren.

---

## Schnellstart-Strategie

1. `SRS` – orientieren, Klingonen und Romulaner suchen
2. `LRS` – Nachbarquadranten erkunden, Feinde markieren
3. `NAV` – in einen Quadrant mit Feinden fliegen
4. `SHE` – Schilde auf mindestens 300–500 setzen
5. `TAC` – falls Romulaner im LRS aber nicht auf SRS sichtbar
6. `COM 2` – Torpedokurs berechnen lassen
7. `TOR` / `PHA` – Feinde eliminieren
8. `TRB` – bei Tribble-Befall + Klingonen im Quadrant ausnutzen
9. **Basis aufsuchen** wenn Energie < 1000

---

*Basiert auf dem BASIC-Original von Mike Mayfield (1978). Python-Port 2026 bzw. dem LUA Port von Emanuele Bolognesi, 2020.
