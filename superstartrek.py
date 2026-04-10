"""
SUPER STARTREK - MAY 16,1978
Python port of the Lua conversion by Emanuele Bolognesi (Oct 2020)
which was itself ported from the original BASIC by Mike Mayfield.

Original BASIC by Mike Mayfield.
Modified version published in DEC's "101 BASIC GAMES" by Dave Ahl.
Modifications by Bob Leedom (April & December 1974).
Converted to Microsoft 8K BASIC 3/16/78 by John Gorders.
Lua conversion by Emanuele Bolognesi - http://emabolo.com
Python port 2026.
"""

import math
import random
import sys
import time

try:
    from rich.console import Console as _RichConsole
    _RICH_AVAILABLE = True
except ImportError:
    _RICH_AVAILABLE = False

try:
    import winsound as _winsound
    _SOUND_AVAILABLE = True
except ImportError:
    _SOUND_AVAILABLE = False


class Game:
    """All game state and logic, ported 1:1 from superstartrek.lua."""

    DEVICE_NAMES = [
        "WARP ENGINES",
        "SHORT RANGE SENSORS",
        "LONG RANGE SENSORS",
        "PHASER CONTROL",
        "PHOTON TUBES",
        "DAMAGE CONTROL",
        "SHIELD CONTROL",
        "LIBRARY-COMPUTER",
    ]

    # CourseDelta: delta-row and delta-col for each of the 8 compass directions (1-based, index 9 == index 1)
    COURSE_DELTA = [
        None,        # index 0 unused (1-based)
        (0, 1),
        (-1, 1),
        (-1, 0),
        (-1, -1),
        (0, -1),
        (1, -1),
        (1, 0),
        (1, 1),
        (0, 1),      # index 9 == index 1
    ]

    def __init__(self):
        self.disable_teleprint = False
        self.game_over = False

        # Ship resources
        self.max_energy_level = 3000
        self.max_torpedoes = 10
        self.klingon_base_energy = 200

        self.energy_level = self.max_energy_level
        self.photon_torpedoes = self.max_torpedoes
        self.shield_level = 0
        self.ship_docked = False
        self.ship_condition = ""

        # Time
        self.stardate = 2000 + random.randint(0, 1900)
        self.t0 = self.stardate
        self.max_num_of_days = 25 + random.randint(0, 10)

        # Galaxy coordinates (1-based, use [1..8][1..8])
        # galaxy[i][j] encodes: klingons*1000 + romulans*100 + starbases*10 + stars
        self.galaxy = [[0] * 9 for _ in range(9)]          # [1..8][1..8]
        self.explored_space = [[0] * 9 for _ in range(9)]  # same

        # Klingons in quadrant: k[1..3] = [row, col, energy]
        self.k = [[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0]]  # index 1..3

        # Romulans in quadrant: r[1..2] = [row, col, energy, cloaked]
        self.r = [[0, 0, 0, False], [0, 0, 0, False], [0, 0, 0, False]]  # index 1..2
        self.r_just_decloaked = [False, False, False]  # index 1..2, Ambush-Flag

        # Damage levels for 8 devices (1-based)
        self.damage_level = [0.0] * 9  # index 1..8

        # Quadrant state
        self.k3 = 0   # klingons in current quadrant
        self.r3 = 0   # romulans in current quadrant
        self.b3 = 0   # starbases in current quadrant
        self.s3 = 0   # stars in current quadrant
        self.b4 = 1   # starbase row
        self.b5 = 1   # starbase col

        # Enterprise position
        self.q1 = self._fnr()   # quadrant row
        self.q2 = self._fnr()   # quadrant col
        self.s1 = self._fnr()   # sector row
        self.s2 = self._fnr()   # sector col

        # Previous quadrant (used during movement)
        self.q4 = 0
        self.q5 = 0

        # Movement state (set during CourseControl)
        self.no_of_steps = 0
        self.step_x1 = 0.0
        self.step_x2 = 0.0
        self.warp_factor = 0.0

        # Totals
        self.total_starbases = 0
        self.total_klingon_ships = 0
        self.initial_klingon_ships = 0
        self.total_romulan_ships = 0
        self.initial_romulan_ships = 0
        self.romulan_base_energy = 150

        # Special random-event quadrants (row, col); (0,0) means consumed/not yet set
        self.harry_mudd_quadrant = (0, 0)
        self.vulcan_ship_quadrant = (0, 0)
        self.trader_quadrant = (0, 0)

        # Tribble infestation (from trader event)
        self.tribbles_infested = False

        # Quadrant display string: 8x8 cells * 3 chars = 192 chars (1-based indexing emulated)
        self.quad_string = " " * 192

        # Rich console (None if library not installed)
        self.console = _RichConsole(highlight=False) if _RICH_AVAILABLE else None

    # ------------------------------------------------------------------
    # I/O  (single point of entry – swap these for GUI/TUI later)
    # ------------------------------------------------------------------

    def tele_print(self, text="", delay=0.10):
        if self.console:
            self.console.print(self._colorize(str(text)))
        else:
            print(text)
        self._small_delay(delay)

    def ask(self, prompt):
        """Prompt user and return stripped input string."""
        if self.console:
            self.console.print(self._colorize(str(prompt)), end="")
            return input().strip()
        return input(prompt).strip()

    @staticmethod
    def _colorize(text):
        """Apply rich markup to well-known game strings."""
        replacements = [
            ("*** KLINGON DESTROYED ***",          "[bold yellow]*** KLINGON DESTROYED ***[/bold yellow]"),
            ("*** ROMULAN DESTROYED ***",           "[bold magenta]*** ROMULAN DESTROYED ***[/bold magenta]"),
            ("*** STARBASE DESTROYED ***",         "[bold red]*** STARBASE DESTROYED ***[/bold red]"),
            ("THE ENTERPRISE HAS BEEN DESTROYED",  "[bold red]THE ENTERPRISE HAS BEEN DESTROYED[/bold red]"),
            ("CONGRATULATIONS, CAPTAIN",           "[bold green]CONGRATULATIONS, CAPTAIN[/bold green]"),
            ("COMBAT AREA      CONDITION RED",     "[bold red]COMBAT AREA      CONDITION RED[/bold red]"),
            ("KLINGON SHIPS ATTACK THE ENTERPRISE","[bold red]KLINGON SHIPS ATTACK THE ENTERPRISE[/bold red]"),
            ("ROMULAN WARBIRD DECLOAKS",            "[bold magenta]ROMULAN WARBIRD DECLOAKS[/bold magenta]"),
            ("ROMULAN WARBIRDS ATTACK",             "[bold magenta]ROMULAN WARBIRDS ATTACK[/bold magenta]"),
            ("TACHYON SCAN REVEALS",                "[bold cyan]TACHYON SCAN REVEALS[/bold cyan]"),
            ("** FATAL ERROR **",                  "[bold red]** FATAL ERROR **[/bold red]"),
            ("TORPEDO MISSED!",                    "[yellow]TORPEDO MISSED![/yellow]"),
            ("TOO LATE CAPTAIN",                   "[bold red]TOO LATE CAPTAIN[/bold red]"),
            ("CONDITION          *RED*",           "CONDITION          [bold red on white]*RED*[/bold red on white]"),
            ("CONDITION          GREEN",           "CONDITION          [bold green]GREEN[/bold green]"),
            ("CONDITION          YELLOW",          "CONDITION          [bold yellow]YELLOW[/bold yellow]"),
            ("CONDITION          DOCKED",          "CONDITION          [bold cyan]DOCKED[/bold cyan]"),
            ("*** HARRY MUDD APPEARS",              "[bold yellow]*** HARRY MUDD APPEARS[/bold yellow]"),
            ("*** A VULCAN SURVEY VESSEL",          "[bold cyan]*** A VULCAN SURVEY VESSEL[/bold cyan]"),
            ("*** CYRANO JONES HAILS",              "[bold yellow]*** CYRANO JONES HAILS[/bold yellow]"),
            ("*** TRIBBLES DETECTED",               "[bold yellow]*** TRIBBLES DETECTED[/bold yellow]"),
            ("OVERWHELMED BY TRIBBLES",             "[bold green]OVERWHELMED BY TRIBBLES[/bold green]"),
        ]
        for old, new in replacements:
            text = text.replace(old, new)
        return text

    def _beep(self, frequency=440, duration=200):
        """Play a beep on Windows; silently ignored on other platforms."""
        if _SOUND_AVAILABLE:
            try:
                _winsound.Beep(frequency, duration)
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def _fnr(self):
        """Return random integer 1..8 (equivalent to Lua FNR)."""
        return random.randint(1, 8)

    def _random_unique_quadrant(self, taken):
        """Return a random (row, col) quadrant not present in the *taken* set."""
        while True:
            q = (self._fnr(), self._fnr())
            if q not in taken:
                return q

    def _small_delay(self, sec=0.15):
        if self.disable_teleprint:
            return
        time.sleep(sec)

    def _die(self, msg="I died well"):
        sys.stderr.write(msg + "\n")
        sys.exit(1)

    def _round_to(self, val, precision):
        factor = 10 ** precision
        return math.floor(val * factor) / factor

    def _format_with_spaces(self, s, maxlength, centered=False):
        s = str(s)
        if centered:
            padding = maxlength - len(s)
            left = padding // 2
            right = padding - left
            result = " " * left + s + " " * right
        else:
            result = s + " " * (maxlength - len(s))
        return result

    # ------------------------------------------------------------------
    # Galaxy / Quadrant helpers
    # ------------------------------------------------------------------

    def _get_quadrant_name(self, z4, z5, region_name_only=False):
        if z5 <= 4:
            starnames = ["ANTARES", "RIGEL", "PROCYON", "VEGA",
                         "CANOPUS", "ALTAIR", "SAGITTARIUS", "POLLUX"]
        else:
            starnames = ["SIRIUS", "DENEB", "CAPELLA", "BETELGEUSE",
                         "ALDEBARAN", "REGULUS", "ARCTURUS", "SPICA"]

        name = starnames[z4 - 1]  # 1-based

        if not region_name_only:
            suffix = {1: " I", 2: " II", 3: " III", 4: " IV",
                      5: " I", 6: " II", 7: " III", 8: " IV"}
            name += suffix.get(z5, "")

        return name

    def _add_element_in_quadrant_string(self, elem, y, x):
        """Insert 3-char string at grid position (y, x) (1-based, float accepted)."""
        y = math.floor(y - 0.5)
        x = math.floor(x - 0.5)
        position = x * 3 + y * 24  # 0-based index

        if len(elem) != 3:
            self._die("wrong string passed to _add_element_in_quadrant_string")

        qs = self.quad_string
        self.quad_string = qs[:position] + elem + qs[position + 3:]
        return position

    def _search_string_in_quadrant(self, elem, y, x):
        y = math.floor(y - 0.5)
        x = math.floor(x - 0.5)
        position = x * 3 + y * 24  # 0-based
        return self.quad_string[position:position + 3] == elem

    def _find_empty_place_in_quadrant(self):
        while True:
            y = self._fnr()
            x = self._fnr()
            if self._search_string_in_quadrant("   ", y, x):
                return y, x

    # ------------------------------------------------------------------
    # Ship Status
    # ------------------------------------------------------------------

    def _check_ship_status(self):
        if self.ship_docked:
            return "DOCKED"
        # Only visible Romulans trigger red alert; cloaked ones are undetected
        visible_romulans = sum(1 for i in range(1, self.r3 + 1) if self.r[i][2] > 0 and not self.r[i][3])
        if self.k3 > 0 or visible_romulans > 0:
            return "*RED*"
        elif self.energy_level < self.max_energy_level / 10:
            return "YELLOW"
        else:
            return "GREEN"

    def _check_if_docked(self):
        self.ship_docked = False
        for i in range(int(self.s1) - 1, int(self.s1) + 2):
            for j in range(int(self.s2) - 1, int(self.s2) + 2):
                ii = math.floor(i + 0.5)
                jj = math.floor(j + 0.5)
                if 1 <= ii <= 8 and 1 <= jj <= 8:
                    if self._search_string_in_quadrant(">!<", i, j):
                        self.ship_docked = True
                        self.ship_condition = "DOCKED"
                        self.energy_level = self.max_energy_level
                        self.photon_torpedoes = self.max_torpedoes
                        self._beep(880, 100)
                        self._beep(1100, 150)
                        self.tele_print("SHIELDS DROPPED FOR DOCKING PURPOSES")
                        self.shield_level = 0
                        break
        self.ship_condition = self._check_ship_status()
        return self.ship_docked

    # ------------------------------------------------------------------
    # Math helpers
    # ------------------------------------------------------------------

    def _calc_distance(self, x1, y1, x2, y2):
        dx = x1 - x2
        dy = y1 - y2
        return math.sqrt(dx ** 2 + dy ** 2)

    def _calc_and_print_direction(self, m, n, starting_course):
        if abs(m) > abs(n):
            direction = starting_course + (abs(n) / abs(m))
        else:
            direction = starting_course + ((abs(n) - abs(m) + abs(n)) / abs(n))
        self.tele_print(f" DIRECTION = {self._round_to(direction, 2)}")
        return direction

    def _print_distance_and_direction(self, x1, y1, x2, y2):
        hd = y1 - y2
        vd = x2 - x1

        if hd < 0:
            if vd > 0:
                self._calc_and_print_direction(vd, hd, 3)
            elif hd != 0:
                self._calc_and_print_direction(hd, vd, 5)
        else:
            if vd < 0:
                self._calc_and_print_direction(vd, hd, 7)
            elif hd > 0:
                self._calc_and_print_direction(hd, vd, 1)
            elif vd == 0:
                self._calc_and_print_direction(hd, vd, 5)
            elif vd > 0:
                self._calc_and_print_direction(hd, vd, 1)

        distance = self._calc_distance(x1, y1, x2, y2)
        self.tele_print(f" DISTANCE = {self._round_to(distance, 2)}")
        return distance

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    def short_range_sensor_scan(self):
        if self.damage_level[2] < 0:
            self.tele_print("\n*** SHORT RANGE SENSORS ARE OUT ***\n")
            return False

        # --- 8 sector rows, each exactly 32 chars (8 cells x "XYZ ") ---
        # Cloaked Romulans are absent from quad_string ("   ") and never shown here.
        # Only a TAC scan can reveal them.
        display_quad = self.quad_string
        grid = []
        for i in range(8):
            b = i * 24
            grid.append("".join(
                display_quad[b + j * 3: b + j * 3 + 3] + " " for j in range(8)
            ))  # exactly 32 chars

        # --- status items ---
        cond = self.ship_condition
        st = [
            f"STARDATE  {self._round_to(self.stardate, 1)}",
            f"CONDITION {cond}",
            f"QUADRANT  {self.q1} , {self.q2}",
            f"SECTOR    {self.s1} , {self.s2}",
            f"TORPEDOES {math.floor(self.photon_torpedoes)}",
            f"ENERGY    {math.floor(self.energy_level + self.shield_level)}",
            f"SHIELDS   {math.floor(self.shield_level)}",
            f"KLINGONS  {math.floor(self.total_klingon_ships)}",
        ]

        # --- layout constants (outer box = 72 chars: ║ + 70 inner + ║) ---
        VS_W  = 33   # viewscreen inner width (═ count)
        ST_W  = 21   # status column width
        PAD_R = 70 - 2 - VS_W - 1 - 2 - ST_W   # = 11 padding chars on the right

        outer_top = "\u2554" + "\u2550" * 70 + "\u2557"
        outer_bot = "\u255a" + "\u2550" * 70 + "\u255d"
        vs_top    = " \u2554" + "\u2550" * VS_W + "\u2557" + " " * (70 - VS_W - 3)
        vs_bot    = " \u255a" + "\u2550" * VS_W + "\u255d" + " " * (70 - VS_W - 3)

        bridge_crew = [
            " " * 70,
            "   \u2554\u2550\u2550\u2550\u2557    \u2554\u2550\u2550\u2550\u2557    \u2554\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2557    \u2554\u2550\u2550\u2550\u2557    \u2554\u2550\u2550\u2550\u2557".ljust(70),
            "   \u2551CHK\u2551    \u2551SLU\u2551    \u2551   KIRK   \u2551    \u2551UHR\u2551    \u2551SPK\u2551".ljust(70),
            " \u2550\u2550\u2569\u2550\u2550\u2550\u2569\u2550\u2550\u2550\u2550\u2569\u2550\u2550\u2550\u2569\u2550\u2550\u2550\u2550\u2569\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2569\u2550\u2550\u2550\u2550\u2569\u2550\u2550\u2550\u2569\u2550\u2550\u2550\u2550\u2569\u2550\u2550\u2550\u2569\u2550\u2550".ljust(70),
        ]

        raw_lines = [outer_top, "\u2551" + vs_top + "\u2551"]
        for i in range(8):
            vs_content = " " + grid[i]                                    # 1+32 = 33 chars
            content    = f" \u2551{vs_content}\u2551  {st[i]:<{ST_W}}{' ' * PAD_R}"
            raw_lines.append(f"\u2551{content}\u2551")
        raw_lines.append("\u2551" + vs_bot + "\u2551")
        for b_line in bridge_crew:
            raw_lines.append(f"\u2551{b_line}\u2551")
        raw_lines.append(outer_bot)

        cond_colors = {
            "*RED*":  "[bold red on white]*RED*[/bold red on white]",
            "GREEN":  "[bold green]GREEN[/bold green]",
            "YELLOW": "[bold yellow]YELLOW[/bold yellow]",
            "DOCKED": "[bold cyan]DOCKED[/bold cyan]",
        }
        for raw in raw_lines:
            if self.console:
                c = (raw
                     .replace("+K+", "[bold red]+K+[/bold red]")
                     .replace(">!<", "[bold green]>!<[/bold green]")
                     .replace("<*>", "[bold cyan]<*>[/bold cyan]")
                     .replace("{R}", "[bold magenta]{R}[/bold magenta]")
                     .replace(" * ", "[yellow] * [/yellow]"))
                if cond in cond_colors:
                    c = c.replace(f"CONDITION {cond}",
                                  f"CONDITION {cond_colors[cond]}")
                self.console.print(c)
            else:
                print(raw)
            self._small_delay(0.03)

        print()
        return True

    def long_range_sensor_scan(self):
        if self.damage_level[3] < 0:
            self.tele_print("\n*** LONG RANGE SENSORS ARE INOPERABLE ***\n")
            return False

        # Cloaked Romulans intercept long-range sensor emissions
        if self._cloaked_romulans_intercept():
            return False

        self.tele_print(f"LONG RANGE SCAN FOR QUADRANT {self.q1},{self.q2}")
        header = "-----------------------"
        self.tele_print(header)

        for i in range(self.q1 - 1, self.q1 + 2):
            n = [-1, -2, -3]
            for j in range(self.q2 - 1, self.q2 + 2):
                idx = j - (self.q2 - 1)
                if 1 <= i <= 8 and 1 <= j <= 8:
                    n[idx] = self.galaxy[i][j]
                    self.explored_space[i][j] = self.galaxy[i][j]

            row_str = ""
            for val in n:
                row_str += ": "
                if val < 0:
                    row_str += "**** "
                else:
                    # Add sensor noise in quadrants with Romulans
                    r_count = (val // 100) % 10
                    display_val = val
                    if r_count > 0:
                        display_val = val + random.randint(-1, 1)
                        display_val = max(0, display_val)
                    s = str(display_val + 10000)  # pad to 5 digits
                    row_str += s[1:5] + " "
            self.tele_print(row_str + ":")
            self.tele_print(header)

        return True

    def shield_control(self):
        if self.damage_level[7] < 0:
            self.tele_print("SHIELD CONTROL INOPERABLE")
            return False

        self.tele_print(f"ENERGY AVAILABLE = {self.energy_level + self.shield_level}")
        units_str = self.ask("NUMBER OF UNITS TO SHIELDS? ")
        units = None
        try:
            units = float(units_str)
        except (ValueError, TypeError):
            pass

        if units is None:
            self.tele_print("WRONG VALUE")
        elif units < 0 or self.shield_level == units:
            self.tele_print("<SHIELDS UNCHANGED>")
        elif units > self.energy_level + self.shield_level:
            self.tele_print("SHIELD CONTROL REPORTS  'THIS IS NOT THE FEDERATION TREASURY.'")
            self.tele_print("<SHIELDS UNCHANGED>")
        else:
            self.energy_level = self.energy_level + self.shield_level - units
            self.shield_level = units
            self.tele_print("DEFLECTOR CONTROL ROOM REPORT:")
            self.tele_print(f"  'SHIELDS NOW AT {self.shield_level} UNITS PER YOUR COMMAND.'")

        return self.shield_level

    def damage_control(self):
        if self.damage_level[6] >= 0:
            self.tele_print("\nDEVICE             STATE OF REPAIR")
            for idx in range(1, 9):
                tabs = 27 if self.damage_level[idx] >= 0 else 26
                self.tele_print(
                    self._format_with_spaces(self.DEVICE_NAMES[idx - 1], tabs)
                    + str(self._round_to(self.damage_level[idx], 2))
                )
        else:
            self.tele_print("DAMAGE CONTROL REPORT NOT AVAILABLE")

        print("")

        if self.ship_docked:
            time_to_repair = 0.0
            for i in range(1, 9):
                if self.damage_level[i] < 0:
                    time_to_repair += 0.1

            if time_to_repair == 0.0:
                return 0

            print("")
            time_to_repair = self._round_to(time_to_repair + random.random() * 0.5, 2)
            if time_to_repair > 0.9:
                time_to_repair = 0.9

            self.tele_print("TECHNICIANS STANDING BY TO EFFECT REPAIRS TO YOUR SHIP;")
            self.tele_print(f"ESTIMATED TIME TO REPAIR: {time_to_repair} STARDATES")
            yes_no = self.ask("WILL YOU AUTHORIZE THE REPAIR ORDER (Y/N) ? ")
            if yes_no.upper() == "Y":
                for i in range(1, 9):
                    if self.damage_level[i] < 0:
                        self.damage_level[i] = 0
                self.stardate += time_to_repair + 0.1
                self.tele_print("REPAIR COMPLETED.")

        return True

    def _print_computer_record(self, galaxy_map_on):
        self.tele_print("       1     2     3     4     5     6     7     8")
        self.tele_print("     ----- ----- ----- ----- ----- ----- ----- -----")

        for i in range(1, 9):
            row = f"{i}  "
            if galaxy_map_on:
                name1 = self._get_quadrant_name(i, 1, region_name_only=True)
                name2 = self._get_quadrant_name(i, 5, region_name_only=True)
                row += "  " + self._format_with_spaces(name1, 23, centered=True)
                row += " " + self._format_with_spaces(name2, 23, centered=True)
            else:
                for j in range(1, 9):
                    row += "   "
                    if self.explored_space[i][j] == 0:
                        row += "****"
                    else:
                        s = str(self.explored_space[i][j] + 10000)
                        row += s[1:5]
            print(row)
            self.tele_print("     ----- ----- ----- ----- ----- ----- ----- -----")

        print("")
        return False

    def galaxy_map(self):
        self.tele_print("                        THE GALAXY")
        self._print_computer_record(galaxy_map_on=True)
        return True

    def cumulative_galactic_record(self):
        self.tele_print(f"       COMPUTER RECORD OF GALAXY FOR QUADRANT {self.q1},{self.q2}\n")
        self._print_computer_record(galaxy_map_on=False)
        return True

    def status_report(self):
        self.tele_print("   STATUS REPORT:")
        ss = "S" if self.total_klingon_ships > 1 else ""
        self.tele_print(f"KLINGON{ss} LEFT: {self.total_klingon_ships}")
        ss = "S" if self.total_romulan_ships > 1 else ""
        self.tele_print(f"ROMULAN{ss} LEFT: {self.total_romulan_ships}")
        self.tele_print(
            f"MISSION MUST BE COMPLETED IN "
            f"{self._round_to(self.t0 + self.max_num_of_days - self.stardate, 1)} STARDATES"
        )

        if self.total_starbases < 1:
            self.tele_print("YOUR STUPIDITY HAS LEFT YOU ON YOUR ON IN")
            self.tele_print("  THE GALAXY -- YOU HAVE NO STARBASES LEFT!")
        else:
            ss = "S" if self.total_starbases > 1 else ""
            self.tele_print(
                f"THE FEDERATION IS MAINTAINING {self.total_starbases} STARBASE{ss} IN THE GALAXY"
            )

        self.damage_control()
        return True

    def photon_torpedo_data(self):
        if self.k3 <= 0 and self.r3 <= 0:
            self.tele_print("SCIENCE OFFICER SPOCK REPORTS  'SENSORS SHOW NO ENEMY SHIPS")
            self.tele_print("                                IN THIS QUADRANT'")
            return True

        if self.k3 > 0:
            ss = "S" if self.k3 > 1 else ""
            self.tele_print(f"FROM ENTERPRISE TO KLINGON BATTLE CRUISER{ss}:")
            for i in range(1, 4):
                if self.k[i][2] > 0:
                    self._print_distance_and_direction(self.k[i][0], self.k[i][1], self.s1, self.s2)

        if self.r3 > 0:
            visible = [i for i in range(1, 3) if self.r[i][2] > 0 and not self.r[i][3]]
            cloaked = sum(1 for i in range(1, 3) if self.r[i][2] > 0 and self.r[i][3])
            if visible:
                ss = "S" if len(visible) > 1 else ""
                self.tele_print(f"FROM ENTERPRISE TO ROMULAN WARBIRD{ss}:")
                for i in visible:
                    self._print_distance_and_direction(self.r[i][0], self.r[i][1], self.s1, self.s2)
            if cloaked > 0:
                self.tele_print(f"SENSORS DETECT {cloaked} CLOAKED ROMULAN SIGNAL(S) -- POSITION UNCERTAIN")

        return True

    def distance_calculator(self):
        self.tele_print("DIRECTION/DISTANCE CALCULATOR:")
        self.tele_print(f"YOU ARE AT QUADRANT {self.q1},{self.q2} SECTOR {self.s1},{self.s2}")
        coord = self.ask("PLEASE ENTER INITIAL COORDINATES (row,col): ")

        import re
        match = re.match(r"(\d+)\s*,\s*(\d+)", coord)
        if not match:
            self.tele_print("WRONG COORDINATES")
            return False
        y1, x1 = int(match.group(1)), int(match.group(2))

        coord = self.ask("  FINAL COORDINATES (row,col): ")
        match = re.match(r"(\d+)\s*,\s*(\d+)", coord)
        if not match:
            self.tele_print("WRONG COORDINATES")
            return False
        y2, x2 = int(match.group(1)), int(match.group(2))

        self._print_distance_and_direction(y2, x2, y1, x1)
        return True

    def starbase_nav_data(self):
        if self.b3 > 0:
            self.tele_print("FROM ENTERPRISE TO STARBASE:")
            self._print_distance_and_direction(self.b4, self.b5, self.s1, self.s2)
        else:
            self.tele_print("MR. SPOCK REPORTS,  'SENSORS SHOW NO STARBASES IN THIS")
            self.tele_print(" QUADRANT.'")
        return True

    def library_computer(self):
        if self.damage_level[8] < 0:
            self.tele_print("COMPUTER DISABLED")
            return False

        computer_done = False
        while not computer_done:
            cmd_str = self.ask("COMPUTER ACTIVE AND AWAITING COMMAND? ")
            print("")
            try:
                cmd = int(cmd_str)
            except (ValueError, TypeError):
                cmd = -1

            if cmd == 0:
                computer_done = self.cumulative_galactic_record()
            elif cmd == 1:
                computer_done = self.status_report()
            elif cmd == 2:
                computer_done = self.photon_torpedo_data()
            elif cmd == 3:
                computer_done = self.starbase_nav_data()
            elif cmd == 4:
                computer_done = self.distance_calculator()
            elif cmd == 5:
                computer_done = self.galaxy_map()
            else:
                print("FUNCTIONS AVAILABLE FROM LIBRARY-COMPUTER:")
                print("   0 = CUMULATIVE GALACTIC RECORD")
                print("   1 = STATUS REPORT")
                print("   2 = PHOTON TORPEDO DATA")
                print("   3 = STARBASE NAV DATA")
                print("   4 = DIRECTION/DISTANCE CALCULATOR")
                print("   5 = GALAXY 'REGION NAME' MAP\n")

        return False

    # ------------------------------------------------------------------
    # End-of-game
    # ------------------------------------------------------------------

    def _enterprise_destroyed(self):
        self._beep(150, 200)
        self._beep(120, 200)
        self._beep(100, 800)
        self.tele_print("\nTHE ENTERPRISE HAS BEEN DESTROYED.  THE FEDERATION WILL BE CONQUERED.")
        self._small_delay(2)

    def _klingons_defeated(self):
        """Called when last Klingon is destroyed — check if Romulans also all gone."""
        self._check_all_enemies_defeated()

    def _all_enemies_defeated(self):
        self._beep(523, 150)
        self._beep(659, 150)
        self._beep(784, 150)
        self._beep(1047, 400)
        self.tele_print("\nCONGRATULATIONS, CAPTAIN! ALL ENEMY FORCES HAVE BEEN ELIMINATED.")
        self.tele_print(f"THE LAST THREAT TO THE FEDERATION WAS DESTROYED IN STARDATE {self._round_to(self.stardate, 1)}")
        total_enemies = self.initial_klingon_ships + self.initial_romulan_ships
        if total_enemies > 0 and (self.stardate - self.t0) > 0:
            self.tele_print(
                f"\nYOUR EFFICIENCY RATING IS "
                f"{math.floor(1000 * (total_enemies / (self.stardate - self.t0)) ** 2)}"
            )

    def _time_expired(self):
        self.tele_print("\nTOO LATE CAPTAIN!  THE FEDERATION HAS BEEN CONQUERED.")

    # ------------------------------------------------------------------
    # Combat
    # ------------------------------------------------------------------

    def _klingons_attack(self):
        if self.k3 <= 0:
            return False

        self.tele_print("KLINGON SHIPS ATTACK THE ENTERPRISE", 1)

        if self.ship_docked:
            self.tele_print("STARBASE SHIELDS PROTECT THE ENTERPRISE.")
            return False

        for i in range(1, 4):
            klingon_energy = self.k[i][2]
            if klingon_energy > 0:
                distance = self._calc_distance(self.k[i][0], self.k[i][1], self.s1, self.s2)
                hits = math.floor((klingon_energy / distance) * (2 + random.random())) + 1
                self.shield_level -= hits
                self.k[i][2] = klingon_energy / (3 + random.random())
                self._beep(220, 150)
                self.tele_print(f"{hits} UNIT HIT ON ENTERPRISE FROM SECTOR {self.k[i][0]},{self.k[i][1]}")

                if self.shield_level < 0:
                    self._enterprise_destroyed()
                    self.game_over = True
                    return True

                self.tele_print(f"      <SHIELDS DOWN TO {self.shield_level} UNITS>", 1)

                if hits > 19 and (
                    self.shield_level == 0
                    or (random.random() < 0.6 and self.shield_level > 0 and (hits / self.shield_level) > 0.02)
                ):
                    sys_damaged = self._fnr()
                    self.damage_level[sys_damaged] -= (
                        (hits / max(self.shield_level, 1)) + 0.5 * random.random()
                    )
                    self.tele_print(
                        f"DAMAGE CONTROL REPORTS '{self.DEVICE_NAMES[sys_damaged - 1]} DAMAGED BY THE HIT'"
                    )

        return False

    def _romulans_cloak_cycle(self):
        """Process Romulan cloaking logic each turn: drain energy for cloaked ships,
        random decloaking flicker, and re-cloaking after exposure."""
        for i in range(1, self.r3 + 1):
            if self.r[i][2] <= 0:
                continue
            if self.r[i][3]:  # currently cloaked
                self.r[i][2] -= 15  # energy drain per turn
                if self.r[i][2] <= 0:
                    # Romulan runs out of cloak energy — destroyed
                    self.r[i][2] = 0
                    self.r3 -= 1
                    self.total_romulan_ships -= 1
                    self.galaxy[self.q1][self.q2] -= 100
                    self.explored_space[self.q1][self.q2] = self.galaxy[self.q1][self.q2]
                    self.tele_print("SENSORS DETECT A ROMULAN WARBIRD — CLOAK FIELD COLLAPSED!")
                    self.tele_print("*** ROMULAN DESTROYED ***", 1)
                    self._check_all_enemies_defeated()
                elif random.random() < 0.10:
                    # 10% chance of cloak flicker — involuntary decloaking
                    self.r[i][3] = False
                    self.r_just_decloaked[i] = True
                    self._add_element_in_quadrant_string("{R}", self.r[i][0], self.r[i][1])
                    self.tele_print("ROMULAN WARBIRD DECLOAKS — CLOAK FIELD MALFUNCTION!", 1)
            else:  # currently visible
                # 40% chance to re-cloak (unless just decloaked this turn)
                if not self.r_just_decloaked[i] and random.random() < 0.40:
                    self.r[i][3] = True
                    self._add_element_in_quadrant_string("   ", self.r[i][0], self.r[i][1])

    def _romulans_reposition(self):
        """Reposition Romulans in quadrant when Enterprise warps.
        Romulans move more tactically than Klingons (60% base, 80% if Enterprise is weak)."""
        shields_low = self.shield_level < 200
        for i in range(1, self.r3 + 1):
            if self.r[i][2] <= 0:
                continue
            move_chance = 0.80 if shields_low else 0.60
            if random.random() < move_chance:
                # Remove from quad_string only if visible
                if not self.r[i][3]:
                    self._add_element_in_quadrant_string("   ", self.r[i][0], self.r[i][1])
                r1, r2 = self._find_empty_place_in_quadrant()
                self.r[i][0] = r1
                self.r[i][1] = r2
                # Re-add to quad_string only if visible
                if not self.r[i][3]:
                    self._add_element_in_quadrant_string("{R}", r1, r2)

            # Low-energy Romulans may flee the quadrant
            if self.r[i][2] < 30 and random.random() < 0.25:
                if not self.r[i][3]:
                    self._add_element_in_quadrant_string("   ", self.r[i][0], self.r[i][1])
                self.r[i][2] = 0
                self.r3 -= 1
                self.total_romulan_ships -= 1
                self.galaxy[self.q1][self.q2] -= 100
                self.explored_space[self.q1][self.q2] = self.galaxy[self.q1][self.q2]
                self.tele_print("A ROMULAN WARBIRD BREAKS OFF AND RETREATS TO ANOTHER QUADRANT.")

    def _romulans_attack(self):
        """Only uncloaked Romulans attack. First attack after decloaking deals double damage."""
        if self.r3 <= 0:
            return False

        any_attack = any(
            self.r[i][2] > 0 and not self.r[i][3] for i in range(1, self.r3 + 1)
        )
        if not any_attack:
            return False

        self.tele_print("ROMULAN WARBIRDS ATTACK THE ENTERPRISE", 1)

        if self.ship_docked:
            self.tele_print("STARBASE SHIELDS PROTECT THE ENTERPRISE.")
            return False

        for i in range(1, 3):
            if self.r[i][2] <= 0 or self.r[i][3]:
                continue
            distance = self._calc_distance(self.r[i][0], self.r[i][1], self.s1, self.s2)
            hits = math.floor((self.r[i][2] / distance) * (2 + random.random())) + 1

            # Ambush bonus: double damage on first strike after decloaking
            if self.r_just_decloaked[i]:
                hits = hits * 2
                self.r_just_decloaked[i] = False
                self.tele_print(f"AMBUSH! ROMULAN WARBIRD AT SECTOR {self.r[i][0]},{self.r[i][1]} FIRES FULL POWER!")

            self.shield_level -= hits
            self.r[i][2] = self.r[i][2] / (3 + random.random())  # energy drain after firing
            self._beep(180, 150)
            self.tele_print(f"{hits} UNIT HIT ON ENTERPRISE FROM SECTOR {self.r[i][0]},{self.r[i][1]}")

            if self.shield_level < 0:
                self._enterprise_destroyed()
                self.game_over = True
                return True

            self.tele_print(f"      <SHIELDS DOWN TO {self.shield_level} UNITS>", 1)

            if hits > 19 and (
                self.shield_level == 0
                or (random.random() < 0.6 and self.shield_level > 0 and (hits / self.shield_level) > 0.02)
            ):
                sys_damaged = self._fnr()
                self.damage_level[sys_damaged] -= (
                    (hits / max(self.shield_level, 1)) + 0.5 * random.random()
                )
                self.tele_print(
                    f"DAMAGE CONTROL REPORTS '{self.DEVICE_NAMES[sys_damaged - 1]} DAMAGED BY THE HIT'"
                )

            # 70% chance to re-cloak immediately after attack
            if random.random() < 0.70:
                self.r[i][3] = True
                self._add_element_in_quadrant_string("   ", self.r[i][0], self.r[i][1])

        return False

    def _check_all_enemies_defeated(self):
        """Check if both Klingons and Romulans are eliminated. Triggers victory if so."""
        if self.total_klingon_ships <= 0 and self.total_romulan_ships <= 0:
            self._all_enemies_defeated()
            self.game_over = True
            return True
        return False

    def _check_special_events(self):
        """Trigger one-shot random events when the Enterprise enters the right quadrant."""
        if self.harry_mudd_quadrant == (self.q1, self.q2):
            self.harry_mudd_quadrant = (0, 0)  # consumed
            stolen = max(1, math.floor(self.energy_level * 0.10))
            self._beep(350, 150)
            self._beep(280, 200)
            self.tele_print("\n*** HARRY MUDD APPEARS ON THE VIEWSCREEN! ***")
            self.tele_print("THE NOTORIOUS CON MAN HAS BEAMED ABOARD UNDETECTED AND ACCESSED")
            self.tele_print(f"THE SHIP'S ENERGY RESERVES -- {stolen} UNITS STOLEN!")
            self.energy_level = max(0, self.energy_level - stolen)
            self.tele_print(f"ENERGY NOW AT {math.floor(self.energy_level)} UNITS.\n")
            self._small_delay(1.5)

        if self.vulcan_ship_quadrant == (self.q1, self.q2):
            self.vulcan_ship_quadrant = (0, 0)  # consumed
            self._beep(880, 100)
            self._beep(1100, 150)
            self._beep(1320, 200)
            self.tele_print("\n*** A VULCAN SURVEY VESSEL HAILS THE ENTERPRISE ***")
            self.tele_print("'LIVE LONG AND PROSPER, CAPTAIN. OUR SENSORS DETECT")
            self.tele_print(" DAMAGE ABOARD YOUR VESSEL. WE OFFER ASSISTANCE.'")
            for i in range(1, 9):
                if self.damage_level[i] < 0:
                    self.damage_level[i] = 0
            self.energy_level = min(self.max_energy_level, self.energy_level + 500)
            self.tele_print("ALL DAMAGED SYSTEMS HAVE BEEN REPAIRED.")
            self.tele_print(f"500 ENERGY UNITS TRANSFERRED. ENERGY NOW AT {math.floor(self.energy_level)} UNITS.")
            if self.tribbles_infested:
                self.tribbles_infested = False
                self.tele_print("VULCAN CREW ASSISTS IN REMOVING THE TRIBBLE INFESTATION.")
            self.tele_print("")
            self._small_delay(1.5)

        if self.trader_quadrant == (self.q1, self.q2):
            self.trader_quadrant = (0, 0)  # consumed
            self._beep(440, 100)
            self._beep(550, 120)
            self.tele_print("\n*** CYRANO JONES HAILS THE ENTERPRISE ***")
            self.tele_print("'I HAVE GOODS TO TRADE, CAPTAIN — INCLUDING TORPEDO SUPPLIES.'")
            added = self.max_torpedoes - math.floor(self.photon_torpedoes)
            self.photon_torpedoes = self.max_torpedoes
            if added > 0:
                self.tele_print(f"{added} TORPEDOES RESTOCKED. TUBES NOW FULL ({self.max_torpedoes} TOTAL).")
            else:
                self.tele_print("TORPEDO TUBES ALREADY FULL.")
            if random.random() < 0.50:
                self.tribbles_infested = True
                self._beep(300, 200)
                self.tele_print("*** TRIBBLES DETECTED ABOARD THE ENTERPRISE! ***")
                self.tele_print("THE LITTLE CREATURES HAVE SPREAD EVERYWHERE.")
                self.tele_print("ENGINEERING: THEY DRAIN 200 ENERGY PER WARP JUMP.")
                self.tele_print("TIP: USE 'TRB' WHEN KLINGONS ARE PRESENT TO BEAM THEM OVER!")
            else:
                self.tele_print("'A PLEASURE DOING BUSINESS, CAPTAIN.'")
            self.tele_print("")
            self._small_delay(1.5)

    def fire_photon_torpedoes(self):
        if self.photon_torpedoes <= 0:
            self.tele_print("ALL PHOTON TORPEDOES EXPENDED.", 2)
            return False
        if self.damage_level[5] < 0:
            self.tele_print("PHOTON TUBES ARE NOT OPERATIONAL.", 2)
            return False

        course_str = self.ask("PHOTON TORPEDO COURSE (1-9)? ")
        try:
            course = float(course_str)
        except (ValueError, TypeError):
            return False

        if course is None:
            return False
        if course == 9:
            course = 1.0
        if course < 0.1 or course > 9:
            self.tele_print("ENSIGN CHEKOV REPORTS,  'INCORRECT COURSE DATA, SIR!'")
            return False

        self.energy_level -= 2
        self.photon_torpedoes -= 1

        cindex = int(math.floor(course))
        c_curr = self.COURSE_DELTA[cindex]
        c_next = self.COURSE_DELTA[cindex + 1]
        frac = course - cindex
        step_x1 = c_curr[0] + (c_next[0] - c_curr[0]) * frac
        step_x2 = c_curr[1] + (c_next[1] - c_curr[1]) * frac

        x = float(self.s1)
        y = float(self.s2)
        self.tele_print("TORPEDO TRACK:")

        while True:
            x += step_x1
            y += step_x2
            x3 = math.floor(x + 0.5)
            y3 = math.floor(y + 0.5)

            if x3 < 1 or x3 > 8 or y3 < 1 or y3 > 8:
                self.tele_print("TORPEDO MISSED!")
                self._small_delay(2)
                break

            self.tele_print(f"               {x3} , {y3}", 0.5)

            if self._search_string_in_quadrant("   ", x, y):
                pass  # empty space, continue

            elif self._search_string_in_quadrant("+K+", x, y):
                self._beep(660, 120)
                self._beep(880, 200)
                self.tele_print("*** KLINGON DESTROYED ***", 1)
                self.k3 -= 1
                self.ship_condition = self._check_ship_status()
                self.total_klingon_ships -= 1

                if self._check_all_enemies_defeated():
                    return True

                for i in range(1, 4):
                    if x3 == self.k[i][0] and y3 == self.k[i][1]:
                        self.k[i][2] = 0

                self._add_element_in_quadrant_string("   ", x, y)
                self.galaxy[self.q1][self.q2] = self.k3 * 1000 + self.r3 * 100 + self.b3 * 10 + self.s3
                self.explored_space[self.q1][self.q2] = self.galaxy[self.q1][self.q2]
                break

            elif self._search_string_in_quadrant("{R}", x, y):
                self._beep(660, 120)
                self._beep(880, 200)
                self.tele_print("*** ROMULAN DESTROYED ***", 1)
                self.r3 -= 1
                self.ship_condition = self._check_ship_status()
                self.total_romulan_ships -= 1

                if self._check_all_enemies_defeated():
                    return True

                for i in range(1, 3):
                    if x3 == self.r[i][0] and y3 == self.r[i][1]:
                        self.r[i][2] = 0

                self._add_element_in_quadrant_string("   ", x, y)
                self.galaxy[self.q1][self.q2] = self.k3 * 1000 + self.r3 * 100 + self.b3 * 10 + self.s3
                self.explored_space[self.q1][self.q2] = self.galaxy[self.q1][self.q2]
                break

            elif self._search_string_in_quadrant(" * ", x, y):
                self.tele_print(f"STAR AT {x3},{y3} ABSORBED TORPEDO ENERGY.", 1)
                break

            elif self._search_string_in_quadrant(">!<", x, y):
                self.tele_print("*** STARBASE DESTROYED ***", 1)
                self.b3 -= 1
                self.total_starbases -= 1

                if self.total_starbases > 0 or self.total_klingon_ships > self.stardate - self.t0 - self.max_num_of_days:
                    self.tele_print("STARFLEET COMMAND REVIEWING YOUR RECORD TO CONSIDER")
                    self.tele_print("COURT MARTIAL!")
                    self._small_delay(2)
                    self.ship_docked = False
                    self._add_element_in_quadrant_string("   ", x, y)
                    self.galaxy[self.q1][self.q2] = self.k3 * 1000 + self.r3 * 100 + self.b3 * 10 + self.s3
                    self.explored_space[self.q1][self.q2] = self.galaxy[self.q1][self.q2]
                    break
                else:
                    self.tele_print("THAT DOES IT, CAPTAIN!!  YOU ARE HEREBY RELIEVED OF COMMAND")
                    self.tele_print("AND SENTENCED TO 99 STARDATES AT HARD LABOR ON CYGNUS 12!!")
                    self._small_delay(2)
                    self.game_over = True
                    return True
            else:
                self.tele_print("An unknown object has been hit")
                break

        self._klingons_attack()
        self._romulans_attack()
        return True

    def fire_phasers(self):
        if self.damage_level[4] < 0:
            self.tele_print("PHASERS INOPERATIVE")
            return False
        if self.k3 < 1 and self.r3 < 1:
            self.tele_print("SCIENCE OFFICER SPOCK REPORTS  'SENSORS SHOW NO ENEMY SHIPS")
            self.tele_print("                                IN THIS QUADRANT'")
            return False
        if self.damage_level[8] < 0:
            self.tele_print("COMPUTER FAILURE HAMPERS ACCURACY")

        self.tele_print("PHASERS LOCKED ON TARGET;  ")
        units = None
        while units is None or units > self.energy_level or units < 0:
            self.tele_print(f"ENERGY AVAILABLE = {self.energy_level} UNITS")
            try:
                units = float(self.ask("NUMBER OF UNITS TO FIRE? "))
            except (ValueError, TypeError):
                units = None
                continue
            if units == 0:
                return False

        self.energy_level -= units
        if self.damage_level[8] < 0:
            units = units * random.random()

        # Count visible targets: Klingons + uncloaked Romulans
        visible_romulans = sum(1 for i in range(1, 3) if self.r[i][2] > 0 and not self.r[i][3])
        total_targets = self.k3 + visible_romulans
        h1 = math.floor(units / max(total_targets, 1))

        for i in range(1, 4):
            klingon_energy = self.k[i][2]
            if klingon_energy > 0:
                distance = self._calc_distance(self.k[i][0], self.k[i][1], self.s1, self.s2)
                distance_ratio = h1 / distance
                rand_numb = random.random() + 2
                hit_points = math.floor(distance_ratio * rand_numb)

                if hit_points <= 0.15 * klingon_energy:
                    self.tele_print(f"SENSORS SHOW NO DAMAGE TO ENEMY AT {self.k[i][0]},{self.k[i][1]}", 0.5)
                    hit_points = 0
                else:
                    self.k[i][2] -= hit_points
                    self.tele_print(f"{hit_points} UNITS HIT ON KLINGON AT SECTOR {self.k[i][0]},{self.k[i][1]}")

                if self.k[i][2] > 0:
                    self.tele_print(f"   (SENSORS SHOW {math.floor(self.k[i][2])} UNITS REMAINING)", 1)
                else:
                    self._beep(660, 120)
                    self._beep(880, 200)
                    self.tele_print("*** KLINGON DESTROYED ***", 1)
                    self.k3 -= 1
                    self.ship_condition = self._check_ship_status()
                    self.total_klingon_ships -= 1

                    if self._check_all_enemies_defeated():
                        return True

                    self._add_element_in_quadrant_string("   ", self.k[i][0], self.k[i][1])
                    self.k[i][2] = 0
                    self.galaxy[self.q1][self.q2] = self.k3 * 1000 + self.r3 * 100 + self.b3 * 10 + self.s3
                    self.explored_space[self.q1][self.q2] = self.galaxy[self.q1][self.q2]

        # Fire phasers at uncloaked Romulans (cloaked ones cannot be targeted)
        for i in range(1, 3):
            romulan_energy = self.r[i][2]
            if romulan_energy <= 0:
                continue
            if self.r[i][3]:
                # Cloaked — phasers cannot lock on
                continue
            distance = self._calc_distance(self.r[i][0], self.r[i][1], self.s1, self.s2)
            hit_points = math.floor((h1 / distance) * (random.random() + 2))

            if hit_points <= 0.15 * romulan_energy:
                self.tele_print(f"SENSORS SHOW NO DAMAGE TO ROMULAN AT {self.r[i][0]},{self.r[i][1]}", 0.5)
            else:
                self.r[i][2] -= hit_points
                self.tele_print(f"{hit_points} UNITS HIT ON ROMULAN AT SECTOR {self.r[i][0]},{self.r[i][1]}")

            if self.r[i][2] > 0:
                self.tele_print(f"   (SENSORS SHOW {math.floor(self.r[i][2])} UNITS REMAINING)", 1)
            else:
                self._beep(660, 120)
                self._beep(880, 200)
                self.tele_print("*** ROMULAN DESTROYED ***", 1)
                self.r3 -= 1
                self.ship_condition = self._check_ship_status()
                self.total_romulan_ships -= 1

                if self._check_all_enemies_defeated():
                    return True

                self._add_element_in_quadrant_string("   ", self.r[i][0], self.r[i][1])
                self.r[i][2] = 0
                self.galaxy[self.q1][self.q2] = self.k3 * 1000 + self.r3 * 100 + self.b3 * 10 + self.s3
                self.explored_space[self.q1][self.q2] = self.galaxy[self.q1][self.q2]

        self._klingons_attack()
        self._romulans_attack()
        return False

    # ------------------------------------------------------------------
    # Movement
    # ------------------------------------------------------------------

    def _show_directions(self):
        print("""
      4  3  2   
       \\ | /    
        \\|/     
    5 ---*--- 1 
        /|\\     
       / | \\    
      6  7  8
""")

    def _consume_energy(self):
        self.energy_level -= self.no_of_steps + 10
        if self.energy_level >= 0:
            return self.energy_level
        self.tele_print("SHIELD CONTROL SUPPLIES ENERGY TO COMPLETE THE MANEUVER.")
        self.shield_level += self.energy_level
        self.energy_level = 0
        if self.shield_level <= 0:
            self.shield_level = 0
        return self.energy_level

    def _end_of_movement_in_quadrant(self):
        self._add_element_in_quadrant_string("<*>", math.floor(self.s1), math.floor(self.s2))
        self._consume_energy()

        if self.tribbles_infested:
            drain = 200
            self.energy_level = max(0, self.energy_level - drain)
            self.tele_print(f"TRIBBLES CONSUME {drain} ENERGY UNITS. ENERGY NOW AT {math.floor(self.energy_level)}.")

        day_increment = 1
        if self.warp_factor < 1:
            day_increment = self._round_to(self.warp_factor, 1)

        self.stardate += day_increment
        if self.stardate > self.t0 + self.max_num_of_days:
            self._time_expired()
            self.game_over = True
            return True

        self._check_if_docked()
        self.short_range_sensor_scan()
        return False

    def _exceeded_quadrant_limits(self, x, y):
        """Move enterprise beyond quadrant boundary. Returns True if quadrant changed."""
        x_new = 8 * self.q1 + x + self.no_of_steps * self.step_x1
        y_new = 8 * self.q2 + y + self.no_of_steps * self.step_x2
        self.q1 = math.floor(x_new / 8)
        self.q2 = math.floor(y_new / 8)
        self.s1 = math.floor(x_new - self.q1 * 8)
        self.s2 = math.floor(y_new - self.q2 * 8)

        if self.s1 == 0:
            self.q1 -= 1
            self.s1 = 8
        if self.s2 == 0:
            self.q2 -= 1
            self.s2 = 8

        crossing_perimeter = False
        if self.q1 < 1:
            crossing_perimeter = True
            self.q1 = 1
            self.s1 = 1
        if self.q1 > 8:
            crossing_perimeter = True
            self.q1 = 8
            self.s1 = 8
        if self.q2 < 1:
            crossing_perimeter = True
            self.q2 = 1
            self.s2 = 1
        if self.q2 > 8:
            crossing_perimeter = True
            self.q2 = 8
            self.s2 = 8

        if crossing_perimeter:
            self.tele_print("LT. UHURA REPORTS MESSAGE FROM STARFLEET COMMAND:")
            self.tele_print("  'PERMISSION TO ATTEMPT CROSSING OF GALACTIC PERIMETER")
            self.tele_print("  IS HEREBY *DENIED*.  SHUT DOWN YOUR ENGINES.'")
            self.tele_print("CHIEF ENGINEER SCOTT REPORTS  'WARP ENGINES SHUT DOWN")
            self.tele_print(f"  AT SECTOR {self.s1} , {self.s2} OF QUADRANT {self.q1} , {self.q2}'")

        if self.q1 * 8 + self.q2 == self.q4 * 8 + self.q5:
            return False  # quadrant unchanged

        self.stardate += 1
        if self.stardate > self.t0 + self.max_num_of_days:
            self._time_expired()
            self.game_over = True
            return True

        self._consume_energy()
        return True

    def tachyon_scan(self):
        """TAC command: spend 50 energy to detect and decloak all Romulans in quadrant."""
        if self.r3 <= 0:
            self.tele_print("MR. SPOCK REPORTS, 'TACHYON SCAN DETECTS NO ROMULAN SIGNATURES")
            self.tele_print("                    IN THIS QUADRANT.'")
            return False

        tac_cost = 50
        if self.energy_level < tac_cost:
            self.tele_print(f"INSUFFICIENT ENERGY FOR TACHYON SCAN ({tac_cost} UNITS REQUIRED).")
            return False

        self.energy_level -= tac_cost
        self.tele_print("TACHYON PULSE INITIATED . . .", 1)
        self._beep(600, 80)
        self._beep(700, 80)
        self._beep(800, 80)

        revealed = 0
        for i in range(1, self.r3 + 1):
            if self.r[i][2] > 0 and self.r[i][3]:
                self.r[i][3] = False
                self.r_just_decloaked[i] = False  # no Ambush bonus when forcibly scanned
                self._add_element_in_quadrant_string("{R}", self.r[i][0], self.r[i][1])
                revealed += 1

        if revealed > 0:
            ss2 = "S" if revealed > 1 else ""
            self.tele_print(f"TACHYON SCAN REVEALS {revealed} CLOAKED ROMULAN WARBIRD{ss2} — NOW EXPOSED")
            remaining = self.r3 - revealed
            if remaining > 0:
                ss3 = "S" if remaining > 1 else ""
                self.tele_print(f"   ({remaining} FURTHER WARBIRD{ss3} ALREADY VISIBLE)")
        else:
            ss = "S" if self.r3 > 1 else ""
            self.tele_print(f"TACHYON SCAN DETECTS {self.r3} ROMULAN WARBIRD{ss} — ALL ALREADY VISIBLE")
        self.short_range_sensor_scan()
        return False

    def _cloaked_romulans_intercept(self):
        """Called at the start of LRS and NAV.
        Any cloaked Romulan in the current quadrant detects the sensor/engine activity,
        decloaks and fires with 50% reduced damage. Returns True if the ship is destroyed."""
        cloaked = [i for i in range(1, self.r3 + 1) if self.r[i][2] > 0 and self.r[i][3]]
        if not cloaked:
            return False

        self.tele_print("MR. SPOCK: 'CAPTAIN — ROMULAN ENERGY SIGNATURES RESPONDING TO OUR EMISSIONS!'", 1)
        self._beep(180, 150)

        for i in cloaked:
            self.r[i][3] = False
            self.r_just_decloaked[i] = False  # no double-damage bonus here
            self._add_element_in_quadrant_string("{R}", self.r[i][0], self.r[i][1])
            self.tele_print(f"ROMULAN WARBIRD DECLOAKS AT SECTOR {self.r[i][0]},{self.r[i][1]}!", 0.5)

        self.ship_condition = self._check_ship_status()
        self.tele_print("ROMULAN WARBIRDS ATTACK THE ENTERPRISE", 1)

        if self.ship_docked:
            self.tele_print("STARBASE SHIELDS PROTECT THE ENTERPRISE.")
            return False

        for i in cloaked:
            if self.r[i][2] <= 0:
                continue
            distance = self._calc_distance(self.r[i][0], self.r[i][1], self.s1, self.s2)
            hits = math.floor((self.r[i][2] / distance) * (2 + random.random()) * 0.50) + 1
            self.shield_level -= hits
            self.r[i][2] = self.r[i][2] / (3 + random.random())
            self._beep(180, 150)
            self.tele_print(f"{hits} UNIT HIT ON ENTERPRISE FROM SECTOR {self.r[i][0]},{self.r[i][1]}")

            if self.shield_level < 0:
                self._enterprise_destroyed()
                self.game_over = True
                return True

            self.tele_print(f"      <SHIELDS DOWN TO {self.shield_level} UNITS>", 1)

            if hits > 19 and (
                self.shield_level == 0
                or (random.random() < 0.6 and self.shield_level > 0 and (hits / self.shield_level) > 0.02)
            ):
                sys_damaged = self._fnr()
                self.damage_level[sys_damaged] -= (
                    (hits / max(self.shield_level, 1)) + 0.5 * random.random()
                )
                self.tele_print(
                    f"DAMAGE CONTROL REPORTS '{self.DEVICE_NAMES[sys_damaged - 1]} DAMAGED BY THE HIT'"
                )

        self.tele_print("ACTION INTERRUPTED — ROMULANS HAVE ENGAGED THE ENTERPRISE.", 1)
        self.short_range_sensor_scan()
        return True   # interrupts LRS / NAV

    def beam_tribbles(self):
        """TRB command: beam tribbles onto Klingon ships to destroy them."""
        if not self.tribbles_infested:
            self.tele_print("MR. SCOTT REPORTS: 'THERE ARE NO TRIBBLES ABOARD, CAPTAIN.'")
            return False
        if self.k3 <= 0:
            self.tele_print("MR. SCOTT REPORTS: 'NO KLINGON SHIPS IN RANGE TO BEAM TO, CAPTAIN!'")
            return False

        self._beep(440, 80)
        self._beep(330, 80)
        self._beep(220, 200)
        self.tele_print("TRANSPORTER ROOM: BEAMING TRIBBLES TO KLINGON VESSEL . . .", 1)

        destroyed = 0
        for i in range(1, 4):
            if self.k[i][2] > 0:
                self._beep(660, 120)
                self._beep(880, 200)
                self.tele_print(
                    f"*** KLINGON AT SECTOR {self.k[i][0]},{self.k[i][1]} "
                    f"OVERWHELMED BY TRIBBLES — DESTROYED ***", 1
                )
                self._add_element_in_quadrant_string("   ", self.k[i][0], self.k[i][1])
                self.k[i][2] = 0
                destroyed += 1

        self.k3 = 0
        self.total_klingon_ships -= destroyed
        self.galaxy[self.q1][self.q2] = self.k3 * 1000 + self.r3 * 100 + self.b3 * 10 + self.s3
        self.explored_space[self.q1][self.q2] = self.galaxy[self.q1][self.q2]
        self.ship_condition = self._check_ship_status()

        self.tribbles_infested = False
        self.tele_print("ENTERPRISE IS NOW TRIBBLE-FREE!")

        if self._check_all_enemies_defeated():
            return True
        self.short_range_sensor_scan()
        return True

    def course_control(self):
        self._show_directions()

        course_str = self.ask("COURSE (0-9) :")
        try:
            course = float(course_str)
        except (ValueError, TypeError):
            course = None

        if course is None or course < 1 or course > 9:
            self.tele_print("   LT. SULU REPORTS, 'INCORRECT COURSE DATA, SIR!'")
            return False

        max_warp = "8"
        if self.damage_level[1] < 0:
            max_warp = "0.2"

        warp_factor = None
        while warp_factor is None:
            warp_str = self.ask(f"WARP FACTOR (0-{max_warp})? ")
            try:
                warp_factor = float(warp_str)
            except (ValueError, TypeError):
                self.tele_print(f"PLEASE ENTER A NUMBER BETWEEN 0 AND {max_warp}")
                continue

            if warp_factor == 0:
                return False

            if self.damage_level[1] < 0 and warp_factor > 0.2:
                self.tele_print("WARP ENGINES ARE DAMAGED.  MAXIMUM SPEED = WARP 0.2")
                warp_factor = None
            elif warp_factor < 0 or warp_factor > 8:
                self.tele_print(f"   CHIEF ENGINEER SCOTT REPORTS 'THE ENGINES WON'T TAKE WARP {warp_factor} !")
                warp_factor = None

        self.warp_factor = warp_factor
        self.no_of_steps = math.floor(warp_factor * 8 + 0.5)

        if self.energy_level < self.no_of_steps:
            self.tele_print("ENGINEERING REPORTS   'INSUFFICIENT ENERGY AVAILABLE")
            self.tele_print(f"                       FOR MANEUVERING AT WARP {warp_factor} !'")
            if (self.shield_level >= (self.no_of_steps - self.energy_level)
                    and self.damage_level[7] >= 0):
                self.tele_print("DEFLECTOR CONTROL ROOM ACKNOWLEDGES SHIELD ENERGY")
                self.tele_print("                         PRESENTLY DEPLOYED TO SHIELDS.")
            return False

        # Cloaked Romulans detect warp engine startup and intercept
        if self._cloaked_romulans_intercept():
            return False

        # Klingons reposition
        for i in range(1, self.k3 + 1):
            if self.k[i][2] > 0:
                self._add_element_in_quadrant_string("   ", self.k[i][0], self.k[i][1])
                r1, r2 = self._find_empty_place_in_quadrant()
                self.k[i][0] = r1
                self.k[i][1] = r2
                self._add_element_in_quadrant_string("+K+", r1, r2)

        # Romulans reposition and process cloak cycle
        self._romulans_reposition()
        self._romulans_cloak_cycle()

        # Klingons fire before Enterprise moves
        if self._klingons_attack():
            return False

        # Romulans attack
        if self._romulans_attack():
            return False

        # Repair factor
        repair_factor = warp_factor if warp_factor < 1 else 1.0

        for i in range(1, 9):
            if self.damage_level[i] < 0:
                self.damage_level[i] += repair_factor
                if -0.1 < self.damage_level[i] < 0:
                    self.damage_level[i] = -0.1
                elif self.damage_level[i] >= 0:
                    self.tele_print(f"DAMAGE CONTROL REPORT: '{self.DEVICE_NAMES[i - 1]} REPAIR COMPLETED.'")

        # Random damage/repair event
        if random.random() <= 0.2:
            dev_index = self._fnr()
            if random.random() >= 0.6:
                self.damage_level[dev_index] += random.random() * 3 + 1
                self.tele_print(f"DAMAGE CONTROL REPORT: '{self.DEVICE_NAMES[dev_index - 1]} STATE OF REPAIR IMPROVED.'")
            else:
                self.damage_level[dev_index] -= random.random() * 5 + 1
                self.tele_print(f"DAMAGE CONTROL REPORT: '{self.DEVICE_NAMES[dev_index - 1]} DAMAGED.'")

        # Remove Enterprise from current position
        self._add_element_in_quadrant_string("   ", math.floor(self.s1), math.floor(self.s2))

        cindex = int(math.floor(course))
        c_curr = self.COURSE_DELTA[cindex]
        c_next = self.COURSE_DELTA[cindex + 1]
        frac = course - cindex
        self.step_x1 = c_curr[0] + (c_next[0] - c_curr[0]) * frac
        self.step_x2 = c_curr[1] + (c_next[1] - c_curr[1]) * frac

        x = float(self.s1)
        y = float(self.s2)
        self.q4 = self.q1
        self.q5 = self.q2

        for _ in range(self.no_of_steps):
            self.s1 += self.step_x1
            self.s2 += self.step_x2

            if self.s1 < 1 or self.s1 > 8 or self.s2 < 1 or self.s2 > 8:
                if self._exceeded_quadrant_limits(x, y):
                    return True
                else:
                    break

            if self._search_string_in_quadrant("   ", self.s1, self.s2):
                x = self.s1
                y = self.s2
            else:
                self.s1 = math.floor(self.s1 - self.step_x1)
                self.s2 = math.floor(self.s2 - self.step_x2)
                self.tele_print("WARP ENGINES SHUT DOWN AT")
                self.tele_print("SECTOR S1 , S2 DUE TO BAD NAVIGATION.")
                break

        self.s1 = math.floor(self.s1)
        self.s2 = math.floor(self.s2)

        self._end_of_movement_in_quadrant()
        return False

    # ------------------------------------------------------------------
    # Instructions
    # ------------------------------------------------------------------

    def _print_instructions(self):
        text = r"""
          *************************************
          *                                   *
          *                                   *
          *      * * SUPER STAR TREK * *      *
          *                                   *
          *                                   *
          *************************************

      INSTRUCTIONS FOR 'SUPER STAR TREK'

1. WHEN YOU SEE \COMMAND ?\ PRINTED, ENTER ONE OF THE LEGAL
     COMMANDS (NAV,SRS,LRS,PHA,TOR,SHE,DAM,COM,TAC, OR XXX).
2. IF YOU SHOULD TYPE IN AN ILLEGAL COMMAND, YOU'LL GET A SHORT
     LIST OF THE LEGAL COMMANDS PRINTED OUT.
3. SOME COMMANDS REQUIRE YOU TO ENTER DATA (FOR EXAMPLE, THE
     'NAV' COMMAND COMES BACK WITH 'COURSE (1-9) ?'.)  IF YOU
     TYPE IN ILLEGAL DATA (LIKE NEGATIVE NUMBERS), THAN COMMAND
     WILL BE ABORTED

     THE GALAXY IS DIVIDED INTO AN 8 X 8 QUADRANT GRID,
AND EACH QUADRANT IS FURTHER DIVIDED INTO AN 8 X 8 SECTOR GRID.

     YOU WILL BE ASSIGNED A STARTING POINT SOMEWHERE IN THE
GALAXY TO BEGIN A TOUR OF DUTY AS COMMANDER OF THE STARSHIP
\ENTERPRISE\; YOUR MISSION: TO SEEK AND DESTROY THE FLEET OF
KLINGON WARSHIPS AND ROMULAN WARBIRDS MENACING THE FEDERATION.

     KLINGONS ARE DIRECT AND AGGRESSIVE -- THEY ATTACK ON SIGHT
AND STAY IN THEIR SECTOR.  ROMULANS ARE CUNNING: THEY USE
CLOAKING DEVICES ({R} ON SENSORS) AND MAY VANISH AFTER ATTACKING.

     USE 'TAC' (TACHYON SCAN, COSTS 50 ENERGY) TO DETECT CLOAKED
ROMULANS.  NOTE: PHASERS AND TORPEDOES CANNOT HIT A CLOAKED SHIP.
LONG RANGE SENSORS MAY SHOW INACCURATE DATA NEAR ROMULAN FORCES.
"""
        print(text)
        self.ask("-- HIT RETURN TO CONTINUE ")

    def _ask_for_instructions(self):
        ans = self.ask("DO YOU NEED INSTRUCTIONS (Y/N) ? ").upper()
        if ans in ("Y", "YES"):
            self._print_instructions()

    # ------------------------------------------------------------------
    # Galaxy initialisation
    # ------------------------------------------------------------------

    def _init_galaxy(self):
        for i in range(1, 9):
            for j in range(1, 9):
                k3 = 0
                r3_loc = 0
                self.explored_space[i][j] = 0
                r1 = random.random()
                if r1 > 0.98:
                    k3 = 3
                    self.total_klingon_ships += 3
                elif r1 > 0.95:
                    k3 = 2
                    self.total_klingon_ships += 2
                elif r1 > 0.83:
                    k3 = 1
                    self.total_klingon_ships += 1

                # Romulans: 3% chance for 2, 12% chance for 1
                r2 = random.random()
                if r2 > 0.97:
                    r3_loc = 2
                    self.total_romulan_ships += 2
                elif r2 > 0.85:
                    r3_loc = 1
                    self.total_romulan_ships += 1

                b3 = 0
                if random.random() > 0.96:
                    b3 = 1
                    self.total_starbases += 1

                self.galaxy[i][j] = k3 * 1000 + r3_loc * 100 + b3 * 10 + self._fnr()

        if self.total_klingon_ships > self.max_num_of_days:
            self.max_num_of_days = self.total_klingon_ships + 1

        if self.total_starbases == 0:
            self.total_starbases = 1
            self.galaxy[self.q1][self.q2] += 10
            self.q1 = self._fnr()
            self.q2 = self._fnr()

        self.initial_klingon_ships = self.total_klingon_ships
        self.initial_romulan_ships = self.total_romulan_ships

        # Assign special event quadrants (must differ from Enterprise start and each other)
        taken = {(self.q1, self.q2)}
        hm_q = self._random_unique_quadrant(taken)
        self.harry_mudd_quadrant = hm_q
        taken.add(hm_q)
        vs_q = self._random_unique_quadrant(taken)
        self.vulcan_ship_quadrant = vs_q
        taken.add(vs_q)
        tr_q = self._random_unique_quadrant(taken)
        self.trader_quadrant = tr_q

    # ------------------------------------------------------------------
    # Main game loop
    # ------------------------------------------------------------------

    def run(self):
        random.seed()

        if self.console:
            self.console.print("\n\n")
            self.console.print("[cyan]                                    ,------*------,[/cyan]")
            self.console.print("[cyan]                ,-------------   '---  ------'[/cyan]")
            self.console.print("[cyan]                 '-------- --'      / /[/cyan]")
            self.console.print("[cyan]                     ,---' '-------/ /--,[/cyan]")
            self.console.print("[cyan]                      '----------------'[/cyan]")
            self.console.print("[bold cyan]                THE USS ENTERPRISE --- NCC-1701[/bold cyan]")
            self.console.print("\n\n")
        else:
            print("""



                                    ,------*------,
                    ,-------------   '---  ------'
                     '-------- --'      / /
                         ,---' '-------/ /--,
                          '----------------'
                    THE USS ENTERPRISE --- NCC-1701


""")

        self._ask_for_instructions()
        self._init_galaxy()

        ss = "S" if self.total_starbases > 1 else ""
        ss0 = " ARE" if self.total_starbases > 1 else " IS"

        self.tele_print("YOUR ORDERS ARE AS FOLLOWS:")
        self.tele_print(f" DESTROY THE {self.total_klingon_ships} KLINGON WARSHIPS AND {self.total_romulan_ships} ROMULAN WARBIRDS")
        self.tele_print(" WHICH HAVE INVADED THE GALAXY BEFORE THEY CAN ATTACK FEDERATION HQ")
        self.tele_print(f" ON STARDATE {self.t0 + self.max_num_of_days}. THIS GIVES YOU {self.max_num_of_days} DAYS.")
        self.tele_print(" BEWARE: ROMULANS USE CLOAKING DEVICES. USE 'TAC' FOR TACHYON SCAN.")
        self.tele_print(f" THERE{ss0} {self.total_starbases} STARBASE{ss} IN THE GALAXY FOR RESUPPLYING YOUR SHIP.")
        self.tele_print("\n\n\n")
        self._small_delay(1)

        self.q4 = 0
        self.q5 = 0

        while not self.game_over:
            self.k3 = 0
            self.r3 = 0
            self.b3 = 0
            self.s3 = 0

            self.explored_space[self.q1][self.q2] = self.galaxy[self.q1][self.q2]

            if not (1 <= self.q1 <= 8 and 1 <= self.q2 <= 8):
                self._die("Should not happen that we are outside borders")

            quadrant_name = self._get_quadrant_name(self.q1, self.q2)
            self.tele_print()

            if self.t0 == self.stardate:
                self.tele_print("YOUR MISSION BEGINS WITH YOUR STARSHIP LOCATED")
                self.tele_print(f"IN THE GALACTIC QUADRANT {quadrant_name}")
            else:
                self.tele_print(f"NOW ENTERING '{quadrant_name}' QUADRANT . . .")

            self.tele_print()

            self.k3 = math.floor(self.galaxy[self.q1][self.q2] * 0.001)
            self.r3 = math.floor(self.galaxy[self.q1][self.q2] * 0.01) - 10 * self.k3
            self.b3 = math.floor(self.galaxy[self.q1][self.q2] * 0.1) - 100 * self.k3 - 10 * self.r3
            self.s3 = self.galaxy[self.q1][self.q2] - 1000 * self.k3 - 100 * self.r3 - 10 * self.b3

            if self.k3 > 0:
                self.tele_print("COMBAT AREA      CONDITION RED")
                if self.shield_level <= 200:
                    self.tele_print("   SHIELDS DANGEROUSLY LOW")
                self._small_delay(1)

            # Reset klingon data
            for i in range(1, 4):
                self.k[i] = [0, 0, 0]

            # Reset romulan data
            for i in range(1, 3):
                self.r[i] = [0, 0, 0, False]
                self.r_just_decloaked[i] = False

            self.quad_string = " " * 192

            # Place Enterprise
            self._add_element_in_quadrant_string("<*>", self.s1, self.s2)

            # Place Klingons
            if self.k3 > 0:
                for i in range(1, self.k3 + 1):
                    r1, r2 = self._find_empty_place_in_quadrant()
                    self._add_element_in_quadrant_string("+K+", r1, r2)
                    self.k[i][0] = r1
                    self.k[i][1] = r2
                    self.k[i][2] = self.klingon_base_energy * (0.5 + random.random())

            # Place Romulans (50% start cloaked, cloaked ships not in quad_string)
            # We always temporarily reserve the sector to prevent overlap, then clear if cloaked.
            if self.r3 > 0:
                for i in range(1, self.r3 + 1):
                    r1, r2 = self._find_empty_place_in_quadrant()
                    cloaked_start = random.random() < 0.5
                    self.r[i][0] = r1
                    self.r[i][1] = r2
                    self.r[i][2] = self.romulan_base_energy * (0.5 + random.random())
                    self.r[i][3] = cloaked_start
                    # Always claim the sector in quad_string to prevent placement overlaps;
                    # clear it again afterwards if the Romulan starts cloaked.
                    self._add_element_in_quadrant_string("{R}", r1, r2)
                    if cloaked_start:
                        self._add_element_in_quadrant_string("   ", r1, r2)

            # After placement: red alert only if visible Romulans are present
            visible_romulans = sum(1 for i in range(1, self.r3 + 1) if self.r[i][2] > 0 and not self.r[i][3])
            if self.k3 == 0 and visible_romulans > 0:
                self.tele_print("COMBAT AREA      CONDITION RED")
                if self.shield_level <= 200:
                    self.tele_print("   SHIELDS DANGEROUSLY LOW")
                self._small_delay(1)

            # Place Starbase
            if self.b3 > 0:
                r1, r2 = self._find_empty_place_in_quadrant()
                self.b4 = r1
                self.b5 = r2
                self._add_element_in_quadrant_string(">!<", r1, r2)

            # Place Stars
            for _ in range(self.s3):
                r1, r2 = self._find_empty_place_in_quadrant()
                self._add_element_in_quadrant_string(" * ", r1, r2)

            self._check_special_events()
            self._check_if_docked()

            # 50% chance: subspace interference hint when cloaked Romulans are present
            cloaked_present = any(self.r[i][2] > 0 and self.r[i][3] for i in range(1, self.r3 + 1))
            if cloaked_present and random.random() < 0.50:
                self.tele_print("LT. UHURA REPORTS: 'CAPTAIN, SUBSPACE INTERFERENCE DETECTED.")
                self.tele_print("                    ORIGIN UNKNOWN — COULD BE A CLOAKING FIELD.'")

            self.short_range_sensor_scan()

            # Inner command loop
            reached_new_quadrant = False
            while not reached_new_quadrant and not self.game_over:
                if (self.energy_level + self.shield_level <= 10
                        or (self.energy_level <= 10 and self.damage_level[7] < 0)):
                    self.tele_print("\n** FATAL ERROR **   YOU'VE JUST STRANDED YOUR SHIP IN SPACE")
                    self.tele_print("YOU HAVE INSUFFICIENT MANEUVERING ENERGY, AND SHIELD CONTROL")
                    self.tele_print("IS PRESENTLY INCAPABLE OF CROSS-CIRCUITING TO ENGINE ROOM!!")
                    self._small_delay(2)
                    self.game_over = True
                    break

                command = self.ask("COMMAND? ").upper()

                if command == "NAV":
                    reached_new_quadrant = self.course_control()
                elif command == "SRS":
                    self.short_range_sensor_scan()
                elif command == "LRS":
                    self.long_range_sensor_scan()
                elif command == "PHA":
                    self.fire_phasers()
                elif command == "TOR":
                    self.fire_photon_torpedoes()
                elif command == "SHE":
                    self.shield_control()
                elif command == "DAM":
                    self.damage_control()
                elif command == "COM":
                    self.library_computer()
                elif command == "TAC":
                    self.tachyon_scan()
                elif command == "TRB":
                    self.beam_tribbles()
                elif command in ("XXX", "EXIT"):
                    self.game_over = True
                else:
                    print("ENTER ONE OF THE FOLLOWING:")
                    print("  NAV  (TO SET COURSE)")
                    print("  SRS  (FOR SHORT RANGE SENSOR SCAN)")
                    print("  LRS  (FOR LONG RANGE SENSOR SCAN)")
                    print("  PHA  (TO FIRE PHASERS)")
                    print("  TOR  (TO FIRE PHOTON TORPEDOES)")
                    print("  SHE  (TO RAISE OR LOWER SHIELDS)")
                    print("  DAM  (FOR DAMAGE CONTROL REPORTS)")
                    print("  COM  (TO CALL ON LIBRARY-COMPUTER)")
                    print("  TAC  (TACHYON SCAN FOR CLOAKED SHIPS)")
                    print("  TRB  (BEAM TRIBBLES TO KLINGON SHIP)")
                    print("  XXX  (TO RESIGN YOUR COMMAND)\n")

        # End of game
        self.tele_print()
        if self.total_klingon_ships > 0:
            self.tele_print(f"THERE WERE {self.total_klingon_ships} KLINGON BATTLE CRUISERS LEFT AT")
            self.tele_print(f"THE END OF YOUR MISSION, IN STARDATE {self._round_to(self.stardate, 1)}")
        if self.total_romulan_ships > 0:
            self.tele_print(f"THERE WERE {self.total_romulan_ships} ROMULAN WARBIRDS LEFT AT")
            self.tele_print(f"THE END OF YOUR MISSION, IN STARDATE {self._round_to(self.stardate, 1)}")

        self.tele_print("\n\nThank you for playing this game!")
        self.tele_print("\nPython port 2026 — original Lua conversion by Emanuele Bolognesi\n")


if __name__ == "__main__":
    game = Game()
    game.run()
