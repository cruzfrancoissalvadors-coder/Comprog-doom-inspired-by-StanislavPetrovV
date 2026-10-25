import math
import pygame as pg
from settings import *
from sprite_object import SpriteObject

# One circuit per stage (the list repeats if there are more stages than circuits).
# 'parts' are dropped by enemies and must be placed on the breadboard (the breadboard has 4 slots).
CIRCUITS = [
    {
        'goal': 'Build a circuit that lights up an LED.',
        'hint': "Current leaves the battery's + terminal and enters the LED's + (anode) leg.",
        'parts': ['battery', 'resistor', 'led', 'wire'],
    },
]

PART_NAMES = {
    'battery': 'Battery (9 V)',
    'resistor': 'Resistor (330 ohm)',
    'led': 'LED (red)',
    'wire': 'Jumper wire',
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
    elif kind == 'resistor':
        pg.draw.line(s, metal, (8, 62), (120, 62), 5)
        pg.draw.rect(s, (222, 190, 140), (28, 42, 72, 40), border_radius=16)
        for x, color in ((42, (120, 60, 20)), (54, (20, 20, 20)), (66, (200, 40, 30)), (84, (220, 180, 40))):
            pg.draw.rect(s, color, (x, 47, 7, 30))
        pg.draw.rect(s, dark, (28, 42, 72, 40), 3, border_radius=16)
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
            self.game.inventory.add(self.kind)
            self.game.toast(f'Collected: {PART_NAMES[self.kind]}')


class TableSprite(SpriteObject):
    """The table with the breadboard, where the circuit gets built."""
    SCALE = 0.65

    def __init__(self, game, pos=TABLE_POS):
        super().__init__(game, pos=pos, scale=self.SCALE, shift=0.5 / self.SCALE - 0.5,
                         image=make_table_surface())

    def near(self):
        return self.dist < INTERACT_DIST
