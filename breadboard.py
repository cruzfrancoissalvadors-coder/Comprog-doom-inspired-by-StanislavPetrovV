import math
import random
import pygame as pg
from settings import *
from quiz import QuizScreen, FONT_NAMES
from components import PART_NAMES, get_part_icon
from screens import Button, BG, LILAC, GOLD, INK, CONFIRM_KEYS

BOARD = pg.Rect(480, 170, 1020, 530)
BOARD_COLOR = (236, 229, 206)
COPPER, LIT = (190, 120, 60), (255, 215, 70)

# Four slots around a rectangular loop, numbered clockwise. 'flow' is the clockwise direction
# along the slot. A part with direction +1 points along the flow, -1 points against it.
CORNERS = [(640, 270), (1340, 270), (1340, 590), (640, 590)]
SLOT_CENTERS = [(990, 270), (1340, 430), (990, 590), (640, 430)]
FLOWS = [(1, 0), (0, 1), (-1, 0), (0, -1)]
SLOT_CLICK_RADIUS = 100
GREEN, RED = QuizScreen.GREEN, QuizScreen.RED


class BreadboardScreen:
    """Place the collected parts in the loop. A series circuit works in any order, but the battery
    and the LED have polarity: current has to leave the battery's + and enter the LED's + (anode)."""

    def __init__(self, game):
        self.game = game
        self.title_font = pg.font.SysFont(FONT_NAMES, 52, bold=True)
        self.body_font = pg.font.SysFont(FONT_NAMES, 30, bold=True)
        self.small_font = pg.font.SysFont(FONT_NAMES, 24, bold=True)
        self.label_font = pg.font.SysFont(FONT_NAMES, 34, bold=True)
        self.test_btn = Button((BOARD.x, 800, 300, 70), 'TEST CIRCUIT')
        self.clear_btn = Button((BOARD.x + 330, 800, 300, 70), 'CLEAR')
        self.continue_btn = Button((BOARD.x, 800, 300, 70), 'CONTINUE')
        self.start()

    def start(self):
        self.parts = list(self.game.circuit['parts'])
        self.tray = [pg.Rect(60, 190 + i * 130, 360, 110) for i in range(len(self.parts))]
        self.slots = [None] * len(SLOT_CENTERS)
        self.selected = None
        battery_dir = random.choice((1, -1))
        # starts wrong on purpose, so the player has to think about polarity
        self.dir = {'battery': battery_dir, 'led': -battery_dir}
        self.lit = False
        self.done = False
        self.message, self.message_color = 'Pick a part on the left, then click a slot on the board.', 'white'
        self.locked_until = pg.time.get_ticks() + 300

    # ----- input -----
    def handle_event(self, event):
        if pg.time.get_ticks() < self.locked_until:
            return
        if self.done:
            if self.continue_btn.hit(event) or (event.type == pg.KEYDOWN and event.key in CONFIRM_KEYS):
                self.game.finish_circuit()
            return
        if event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.left_click(event.pos)
            elif event.button == 3:
                self.flip(event.pos)
        elif event.type == pg.KEYDOWN:
            if event.key == pg.K_r:
                self.flip(pg.mouse.get_pos())
            elif event.key in (pg.K_RETURN, pg.K_KP_ENTER):
                self.test()

    def slot_at(self, pos):
        for i, (cx, cy) in enumerate(SLOT_CENTERS):
            if math.hypot(pos[0] - cx, pos[1] - cy) < SLOT_CLICK_RADIUS:
                return i
        return None

    def left_click(self, pos):
        if self.test_btn.rect.collidepoint(pos):
            self.test()
            return
        if self.clear_btn.rect.collidepoint(pos):
            self.slots = [None] * len(SLOT_CENTERS)
            self.selected = None
            self.say('Board cleared.')
            return
        for kind, rect in zip(self.parts, self.tray):
            if rect.collidepoint(pos):
                if kind in self.slots:
                    self.say(f'{PART_NAMES[kind]} is already on the board. Click it to pick it up.')
                else:
                    self.selected = None if self.selected == kind else kind
                return
        slot = self.slot_at(pos)
        if slot is None:
            return
        if self.selected:
            self.slots[slot], self.selected = self.selected, self.slots[slot]  # swap with what is there
        elif self.slots[slot]:
            self.selected, self.slots[slot] = self.slots[slot], None
        else:
            self.say('Select a part from the left first.')

    def flip(self, pos):
        slot = self.slot_at(pos)
        kind = self.slots[slot] if slot is not None and self.slots[slot] else self.selected
        if kind is None:
            self.say('Hover over a part (or select one) and press R to flip it.')
        elif kind in self.dir:
            self.dir[kind] *= -1
            self.say(f'Flipped the {PART_NAMES[kind]}.')
        else:
            self.say(f'The {PART_NAMES[kind]} has no polarity, so there is nothing to flip.')

    def say(self, text, color='white'):
        self.message, self.message_color = text, color

    def test(self):
        if None in self.slots:
            self.say('Fill all four slots before testing the circuit.', RED)
        elif self.dir['battery'] != self.dir['led']:
            self.say('No light. The LED is reverse-biased, so no current flows. '
                     'Check the battery and LED polarity.', RED)
        else:
            self.lit = self.done = True
            self.say('The LED lights up! Current flows from the battery + around the loop '
                     'and back to -. Press Enter.', GREEN)

    # ----- drawing -----
    def draw_symbol(self, kind, center, flow, direction):
        screen = self.game.screen
        fx, fy = flow
        px, py = -fy, fx

        def P(t, u=0):
            return center[0] + fx * t + px * u, center[1] + fy * t + py * u

        def label(text, t, u, color='black'):
            surf = self.label_font.render(text, True, color)
            x, y = P(t, u)
            screen.blit(surf, (x - surf.get_width() // 2, y - surf.get_height() // 2))

        ink, w = (40, 40, 40), 6
        if kind == 'wire':
            pg.draw.line(screen, (60, 120, 230), P(-100), P(100), 8)
        elif kind == 'resistor':
            ts = [-60 + 120 * k / 6 for k in range(7)]
            us = [0, 18, -18, 18, -18, 18, 0]
            pg.draw.line(screen, ink, P(-100), P(-60), w)
            pg.draw.lines(screen, ink, False, [P(t, u) for t, u in zip(ts, us)], w)
            pg.draw.line(screen, ink, P(60), P(100), w)
        elif kind == 'led':
            pg.draw.line(screen, ink, P(-100), P(-30), w)
            pg.draw.line(screen, ink, P(30), P(100), w)
            tri = [P(-30 * direction, -28), P(-30 * direction, 28), P(30 * direction, 0)]
            pg.draw.polygon(screen, (230, 60, 60), tri)
            pg.draw.polygon(screen, ink, tri, 4)
            pg.draw.line(screen, ink, P(30 * direction, -28), P(30 * direction, 28), w)
            for t in (-6, 16):  # little light rays
                pg.draw.line(screen, ink, P(t, -38), P(t + 18, -62), 3)
            label('+', -direction * 78, 32)  # anode side
            label('-', direction * 78, 32)   # cathode side
        elif kind == 'battery':
            pg.draw.line(screen, ink, P(-100), P(-14), w)
            pg.draw.line(screen, ink, P(14), P(100), w)
            plus, minus = direction * 14, -direction * 14
            pg.draw.line(screen, ink, P(plus, -38), P(plus, 38), 6)      # long plate = +
            pg.draw.line(screen, ink, P(minus, -20), P(minus, 20), 12)   # short plate = -
            label('+', direction * 78, 32)
            label('-', -direction * 78, 32)

    def draw_board(self, screen):
        pg.draw.rect(screen, BOARD_COLOR, BOARD, border_radius=16)
        pg.draw.rect(screen, (150, 140, 110), BOARD, 3, border_radius=16)
        for x in range(BOARD.left + 30, BOARD.right - 20, 28):
            for y in range(BOARD.top + 24, BOARD.bottom - 10, 28):
                pg.draw.circle(screen, (206, 199, 168), (x, y), 3)

        trace = LIT if self.lit else COPPER
        pg.draw.lines(screen, trace, True, CORNERS, 8)
        for c in CORNERS:
            pg.draw.circle(screen, trace, c, 12)

        for i, (center, flow) in enumerate(zip(SLOT_CENTERS, FLOWS)):
            size = (200, 96) if flow[0] else (96, 200)
            rect = pg.Rect(0, 0, *size)
            rect.center = center
            pg.draw.rect(screen, BOARD_COLOR, rect, border_radius=10)
            kind = self.slots[i]
            if kind is None:
                pg.draw.rect(screen, (170, 160, 130), rect, 3, border_radius=10)
                text = self.small_font.render(f'slot {i + 1}', True, (140, 130, 100))
                screen.blit(text, (rect.centerx - text.get_width() // 2, rect.centery - text.get_height() // 2))
            else:
                self.draw_symbol(kind, center, flow, self.dir.get(kind, 1))
                if kind == 'led' and self.lit:
                    glow = pg.Surface((240, 240), pg.SRCALPHA)
                    for r, a in ((110, 50), (80, 90), (52, 140)):
                        pg.draw.circle(glow, (255, 235, 110, a), (120, 120), r)
                    screen.blit(glow, (center[0] - 120, center[1] - 120))
                    pg.draw.circle(screen, (255, 250, 200), center, 14)

    def draw_tray(self, screen):
        screen.blit(self.small_font.render('PARTS', True, GOLD), (60, 164))
        for kind, rect in zip(self.parts, self.tray):
            placed = kind in self.slots
            border = GOLD if self.selected == kind else ((120, 100, 140) if placed else LILAC)
            pg.draw.rect(screen, (62, 18, 96), rect, border_radius=12)
            pg.draw.rect(screen, border, rect, 4 if self.selected == kind else 2, border_radius=12)
            screen.blit(get_part_icon(kind, 90, dim=placed), (rect.x + 10, rect.y + 10))
            name = self.small_font.render(PART_NAMES[kind], True, (150, 130, 170) if placed else 'white')
            screen.blit(name, (rect.x + 110, rect.centery - name.get_height() // 2))

    def draw(self):
        screen = self.game.screen
        screen.fill(BG)
        screen.blit(self.title_font.render('BREADBOARD', True, GOLD), (60, 18))
        screen.blit(self.small_font.render(self.game.circuit['goal'], True, 'white'), (60, 82))
        screen.blit(self.small_font.render(self.game.circuit['hint'], True, LILAC), (60, 110))
        screen.blit(self.small_font.render('Right-click or R flips a part.', True, LILAC), (60, 138))

        self.draw_tray(screen)
        self.draw_board(screen)

        y = 718
        for line in QuizScreen.wrap(self.message, self.body_font, BOARD.width)[:2]:
            screen.blit(self.body_font.render(line, True, self.message_color), (BOARD.x, y))
            y += 36

        if self.done:
            self.continue_btn.draw(screen, self.body_font)
        else:
            self.test_btn.draw(screen, self.body_font)
            self.clear_btn.draw(screen, self.body_font)
        screen.blit(self.small_font.render('Esc: back to the game', True, LILAC), (BOARD.right - 300, 825))

        if self.selected and not self.done:  # part following the cursor
            icon = get_part_icon(self.selected, 80)
            mx, my = pg.mouse.get_pos()
            screen.blit(icon, (mx - 40, my - 40))
