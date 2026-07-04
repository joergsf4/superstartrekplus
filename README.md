# Super Star Trek Plus

Ein HTML5/JavaScript-Port des Klassikers **Super Star Trek** (Original: BASIC, 1978, Mike Mayfield / Dave Ahl).

## Spielen

**[▶ Jetzt spielen auf GitHub Pages](https://joergsf4.github.io/superstartrekplus/superstartrek.html)**

Oder `superstartrek.html` direkt im Browser öffnen – kein Server, kein Build-Schritt nötig.

Optional mit lokalem Dev-Server:
```bash
python -m http.server 8787
# → http://localhost:8787/superstartrek.html
```

## Über das Spiel

Als Kommandant der Enterprise übernimmst du das Kommando über die Galaxis und musst alle Klingonen vernichten, bevor deine Energie oder Zeit aufgebraucht ist. Getarnte romulanische Warbirds streifen als unsichtbare Gefahr durch die Quadranten — sie sind nicht Teil des Auftrags, aber wer ihnen begegnet, sollte kampfbereit sein. Das Spiel ist vollständig auf **Deutsch**.

### Features
- Klassisches Super-Star-Trek-Gameplay, modernisiert für den Browser
- Retro-Terminal-Optik im Browser

## Projektstruktur

| Datei | Beschreibung |
|-------|--------------|
| `superstartrek.html` | Das gesamte Spiel (HTML + CSS + JS, Single File) |
| `HANDBUCH.html` | Vollständige Spielanleitung auf Deutsch |
| `legacy/superstartrek.py` | Python-Vorgängerversion (Referenz) |
| `legacy/_test_events.py` | Python-Ereignistests (Referenz) |

## Abhängigkeiten

Keine. Reines Vanilla-JavaScript – läuft in jedem modernen Browser.

## Portierungshistorie

```
BASIC (1978, Mayfield/Ahl)
  └─→ Lua (Emanuele Bolognesi, 2020)
        └─→ Python
              └─→ HTML5/JS (2026) ← diese Version
```

## Handbuch

Eine ausführliche Spielanleitung mit allen Befehlen, Spielmechaniken und Tipps findest du in [HANDBUCH.html](HANDBUCH.html).