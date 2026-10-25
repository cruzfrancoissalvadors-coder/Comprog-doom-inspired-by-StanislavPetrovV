import math
import pygame as pg
from settings import *
from sprite_object import SpriteObject

# One circuit per stage, in increasing difficulty (the list repeats if there are more stages).
# 'parts' are dropped by enemies and must be placed on the breadboard. Some parts are decoys.
# 'layout' is ('series', number_of_slots) or ('parallel', [slots in each branch]).
# Electronics used by the breadboard checker: 9 V battery, LED drops 2 V and needs 10-25 mA.
CIRCUITS = [
    {   # Stage 1: polarity only
        'title': 'LED + resistor',
        'goal': 'Build a series circuit that lights up an LED.',
        'hint': "Current leaves the battery's + terminal and enters the LED's + (anode) leg.",
        'parts': ['battery', 'r330', 'led', 'wire'],
        'layout': ('series', 4),
    },
    {   # Stage 2: add a switch and choose the right resistor
        'title': 'Switch + choosing a resistor',
        'goal': 'Build a switched LED circuit. Pick the correct resistor (about 15 mA).',
        'hint': 'R = (9 V - 2 V) / 15 mA. R or right-click closes the switch. Some resistors are decoys.',
        'parts': ['battery', 'led', 'switch', 'r470', 'r100', 'r1k'],
        'layout': ('series', 4),
    },
    {   # Stage 3: two LEDs share the current, so the voltage left for the resistor changes
        'title': 'Two LEDs in series',
        'goal': 'Light TWO LEDs in series with one switch and the correct resistor.',
        'hint': 'Two LEDs drop 4 V: R = (9 V - 4 V) / 15 mA. Both LEDs must face the way the current flows.',
        'parts': ['battery', 'switch', 'led', 'led', 'r220', 'r100', 'r1k'],
        'layout': ('series', 5),
    },
    {   # Stage 4: parallel branches
        'title': 'Parallel branches',
        'goal': 'Light two LEDs in PARALLEL. Each branch needs its own resistor.',
        'hint': 'Battery, switch and jumper go in the main loop. Each branch: one resistor + one LED.',
        'parts': ['battery', 'switch', 'wire', 'led', 'led', 'r470', 'r470', 'r100'],
        'layout': ('parallel', [2, 2]),
    },
    {   # Stage 5: parallel and series mixed
        'title': 'Mixed network',
        'goal': 'Three parallel branches: two with one LED each, one with two LEDs in series.',
        'hint': 'One LED: 470 ohm. Two LEDs in series: 220 ohm. A wrong value burns or dims the LEDs.',
        'parts': ['battery', 'switch', 'wire', 'led', 'led', 'led', 'led', 'r470', 'r470', 'r220', 'r100'],
        'layout': ('parallel', [2, 2, 3]),
    },
]

RESISTANCE = {'r100': 100, 'r220': 220, 'r330': 330, 'r470': 470, 'r1k': 1000, 'r10k': 10000}
_BR, _BK, _RD, _OR, _YE, _VI = (120, 60, 20), (20, 20, 20), (200, 40, 30), (235, 130, 30), (230, 200, 40), (130, 60, 170)
BANDS = {'r100': (_BR, _BK, _BR), 'r220': (_RD, _RD, _BR), 'r330': (_OR, _OR, _BR),
         'r470': (_YE, _VI, _BR), 'r1k': (_BR, _BK, _RD), 'r10k': (_BR, _BK, _OR)}

PART_NAMES = {
    'battery': 'Battery (9 V)',
    'led': 'LED (red)',
    'wire': 'Jumper wire',
    'switch': 'Switch',
    'r100': 'Resistor (100 ohm)',
    'r220': 'Resistor (220 ohm)',
    'r330': 'Resistor (330 ohm)',
    'r470': 'Resistor (470 ohm)',
    'r1k': 'Resistor (1 k ohm)',
    'r10k': 'Resistor (10 k ohm)',
}


def make_part_surface(kind, size=128, glow=False):
    """Draw a part icon with pygame shapes, so no image files are needed."""
    s = pg.Surface((128, 128), pg.SRCALPHA)
    if glow:  # soft puddle of light under a part lying on the floor
        pg.draw.ellipse(s, (255, 220, 90, 70), (6, 86, 116, 34))
        pg.draw.ellipse(s, (255, 235, 140, 120), (24, 92, 80, 20))
    dark, metal = (30, 30, 36), (190, 190, 200)

    if kind == 'battery':
        pg.draw.rect(s, (200, 200, 210), (56, 14, 16, 12), border_radius=3)  # + nub
        pg.draw.rect(s, (45, 45, 55), (42, 24, 44, 76), border_radius=7)
        pg.draw.rect(s, (60, 180, 90), (42, 44, 44, 34))
        pg.draw.line(s, 'white', (54, 61), (74, 61), 5)  # + sign
        pg.draw.line(s, 'white', (64, 51), (64, 71), 5)
        pg.draw.rect(s, dark, (42, 24, 44, 76), 3, border_radius=7)
    elif kind in RESISTANCE:
        pg.draw.line(s, metal, (8, 62), (120, 62), 5)
        pg.draw.rect(s, (222, 190, 140), (28, 42, 72, 40), border_radius=16)
        for x, color in zip((42, 54, 66, 84), BANDS[kind] + ((220, 180, 40),)):
            pg.draw.rect(s, color, (x, 47, 7, 30))
        pg.draw.rect(s, dark, (28, 42, 72, 40), 3, border_radius=16)
    elif kind == 'switch':
        pg.draw.rect(s, (70, 70, 80), (14, 78, 100, 24), border_radius=5)
        pg.draw.rect(s, dark, (14, 78, 100, 24), 3, border_radius=5)
        pg.draw.circle(s, metal, (32, 78), 7)
        pg.draw.circle(s, metal, (96, 78), 7)
        pg.draw.line(s, (220, 60, 60), (32, 78), (88, 38), 8)
        pg.draw.circle(s, (250, 110, 110), (88, 38), 8)
    elif kind == 'led':
        pg.draw.line(s, metal, (54, 70), (54, 114), 4)
        pg.draw.line(s, metal, (74, 70), (74, 104), 4)
        pg.draw.circle(s, (240, 60, 60), (64, 46), 26)
        pg.draw.rect(s, (240, 60, 60), (38, 46, 52, 20))
        pg.draw.rect(s, (170, 30, 30), (34, 64, 60, 8), border_radius=3)
        pg.draw.circle(s, (255, 175, 175), (53, 38), 7)
    elif kind == 'wire':
        pts = [(16 + 96 * t / 20, 92 - 62 * math.sin(math.pi * t / 20)) for t in range(21)]
        pg.draw.lines(s, (60, 120, 230), False, pts, 9)
        pg.draw.lines(s, (130, 175, 255), False, [(x, y - 2) for x, y in pts], 2)
        pg.draw.rect(s, metal, (6, 86, 18, 16), border_radius=3)
        pg.draw.rect(s, metal, (104, 86, 18, 16), border_radius=3)

    if size != 128:
        s = pg.transform.smoothscale(s, (size, size))
    return s


def make_table_surface():
    """A wooden table with a breadboard on top."""
    s = pg.Surface((280, 200), pg.SRCALPHA)
    wood, wood_dark = (150, 100, 60), (105, 68, 38)
    pg.draw.rect(s, wood_dark, (28, 110, 18, 88))
    pg.draw.rect(s, wood_dark, (234, 110, 18, 88))
    pg.draw.rect(s, wood, (8, 92, 264, 26), border_radius=4)
    pg.draw.rect(s, wood_dark, (8, 110, 264, 8), border_radius=4)
    # breadboard
    pg.draw.rect(s, (236, 229, 206), (48, 36, 184, 58), border_radius=6)
    pg.draw.rect(s, (150, 140, 110), (48, 36, 184, 58), 2, border_radius=6)
    pg.draw.line(s, (200, 50, 50), (56, 43), (224, 43), 2)  # power rails
    pg.draw.line(s, (50, 90, 200), (56, 87), (224, 87), 2)
    for y in (52, 59, 71, 78):
        for x in range(58, 226, 10):
            pg.draw.circle(s, (95, 95, 85), (x, y), 2)
    pg.draw.line(s, (170, 160, 130), (54, 65), (226, 65), 2)  # center gap
    return s


_icon_cache = {}


def get_part_icon(kind, size, dim=False):
    key = (kind, size, dim)
    if key not in _icon_cache:
        icon = make_part_surface(kind, size)
        if dim:
            icon.set_alpha(70)
        _icon_cache[key] = icon
    return _icon_cache[key]


class PickupSprite(SpriteObject):
    """A part dropped by an enemy. Walk over it to collect it."""
    SCALE = 0.28

    def __init__(self, game, kind, pos):
        self.base_shift = 0.5 / self.SCALE - 0.5 - 0.1  # keeps the part just above the floor
        super().__init__(game, pos=pos, scale=self.SCALE, shift=self.base_shift,
                         image=make_part_surface(kind, glow=True))
        self.kind = kind
        self.collected = False

    def update(self):
        if self.collected:
            return
        bob = 0.5 + 0.5 * math.sin(pg.time.get_ticks() / 1000 * 3)
        self.SPRITE_HEIGHT_SHIFT = self.base_shift - 0.12 * bob
        self.get_sprite()
        if self.dist < PICKUP_RADIUS:
            self.collected = True
            self.game.inventory[self.kind] += 1
            self.game.toast(f'Collected: {PART_NAMES[self.kind]}')


class TableSprite(SpriteObject):
    """The table with the breadboard, where the circuit gets built."""
    SCALE = 0.65

    def __init__(self, game, pos=TABLE_POS):
        super().__init__(game, pos=pos, scale=self.SCALE, shift=0.5 / self.SCALE - 0.5,
                         image=make_table_surface())

    def near(self):
        return self.dist < INTERACT_DIST
