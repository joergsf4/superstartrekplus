"""Quick automated test for the two random-event quadrants."""
import importlib.util, math, random, sys

random.seed(42)

spec = importlib.util.spec_from_file_location("sst", "superstartrek.py")
sst  = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sst)

# ──────────────────────────────────────────
# Partie 1: Harry Mudd klaut 10 % Energie
# ──────────────────────────────────────────
print("=== PARTIE 1: Harry Mudd ===")
g = sst.Game()
g.disable_teleprint = True
g._init_galaxy()

hm = g.harry_mudd_quadrant
print(f"Harry-Mudd-Quadrant : {hm}")
print(f"Energie vorher      : {g.energy_level}")

expected_stolen = max(1, math.floor(g.energy_level * 0.10))

# Schiff in Mudd-Quadrant teleportieren
g.q1, g.q2 = hm
g.quad_string = " " * 192
g.k3 = g.r3 = g.b3 = g.s3 = 0
g._add_element_in_quadrant_string("<*>", g.s1, g.s2)

g._check_special_events()

print(f"Gestohlene Energie  : {expected_stolen}")
print(f"Energie nachher     : {g.energy_level}")
assert g.harry_mudd_quadrant == (0, 0), "Event nicht konsumiert!"
assert g.energy_level == g.max_energy_level - expected_stolen, "Falscher Energiewert!"
print("OK – Harry Mudd hat Energie gestohlen; Event ist verbraucht.\n")

# Zweiter Besuch desselben Quadranten darf NICHTS auslösen
energy_before = g.energy_level
g._check_special_events()
assert g.energy_level == energy_before, "Event hat ein zweites Mal ausgeloest!"
print("OK – Zweiter Besuch: kein Event mehr.\n")

# ──────────────────────────────────────────
# Partie 2: Vulkanisches Schiff repariert + 500 Energie
# ──────────────────────────────────────────
print("=== PARTIE 2: Vulkanisches Schiff ===")
random.seed(99)
g2 = sst.Game()
g2.disable_teleprint = True
g2._init_galaxy()

vs = g2.vulcan_ship_quadrant
print(f"Vulkan-Quadrant     : {vs}")

# Alle 8 Systeme beschädigen und Energie senken
for i in range(1, 9):
    g2.damage_level[i] = -2.5
g2.energy_level = 800
print(f"Energie vorher      : {g2.energy_level}")
print(f"Schäden vorher      : {[round(g2.damage_level[i], 1) for i in range(1, 9)]}")

# Schiff in Vulkan-Quadrant teleportieren
g2.q1, g2.q2 = vs
g2.quad_string = " " * 192
g2.k3 = g2.r3 = g2.b3 = g2.s3 = 0
g2._add_element_in_quadrant_string("<*>", g2.s1, g2.s2)

g2._check_special_events()

print(f"Energie nachher     : {g2.energy_level}")
print(f"Schäden nachher     : {[round(g2.damage_level[i], 1) for i in range(1, 9)]}")
assert g2.vulcan_ship_quadrant == (0, 0), "Event nicht konsumiert!"
assert all(g2.damage_level[i] == 0 for i in range(1, 9)), "Nicht alle Schäden repariert!"
assert g2.energy_level == 1300, f"Energie falsch: {g2.energy_level} (erwartet 1300)"
print("OK – Alle Schäden repariert, 500 Energie gutgeschrieben; Event ist verbraucht.\n")

# Zweiter Besuch desselben Quadranten darf NICHTS auslösen
energy_before2 = g2.energy_level
g2._check_special_events()
assert g2.energy_level == energy_before2, "Event hat ein zweites Mal ausgeloest!"
print("OK – Zweiter Besuch: kein Event mehr.\n")

print("━" * 46)
print("ALLE TESTS BESTANDEN.")
