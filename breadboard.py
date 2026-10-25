import math
import random
import pygame as pg
from settings import *
from quiz import QuizScreen, FONT_NAMES
from components import PART_NAMES, RESISTANCE, get_part_icon
from screens import Button, BG, LILAC, GOLD, INK, CONFIRM_KEYS

BOARD = pg.Rect(480, 170, 1020, 530)
BOARD_COLOR = (236, 229, 206)
COPPER, LIT = (190, 120, 60), (255, 215, 70)
GREEN, RED = QuizScreen.GREEN, QuizScreen.RED

SUPPLY_V, LED_DROP = 9.0, 2.0          # 9 V battery, red LED drops 2 V
LED_MIN_MA, LED_MAX_MA = 10.0, 25.0    # below: too dim, above: the LED burns out
POLAR = ('battery', 'led', 'switch')   # parts that can be flipped (the switch opens/closes)


def series_layout(n):
    """One rectangular loop with n slots, numbered clockwise."""
    top, right, bottom, left = {4: (1, 1, 1, 1), 5: (2, 1, 1, 1)}[n]
    slots = []
    slots += [((640 + 700 * (i + .5) / top, 270), (1, 0)) for i in range(top)]
    slots += [((1340, 270 + 320 * (i + .5) / right), (0, 1)) for i in range(right)]
    slots += [((1340 - 700 * (i + .5) / bottom, 590), (-1, 0)) for i in range(bottom)]
    slots += [((640, 590 - 320 * (i + .5) / left), (0, -1)) for i in range(left)]
    corners = [(640, 270), (1340, 270), (1340, 590), (640, 590)]
    return {'slots': slots, 'tags': [f'slot {i + 1}' for i in range(n)],
            'traces': [corners + [corners[0]]], 'nodes': corners,
            'main': list(range(n)), 'branches': []}


def parallel_layout(sizes):
    """A main loop (3 slots) feeding parallel branches; sizes = slots in each branch."""
    rows = {2: [270, 455], 3: [270, 400, 530]}[len(sizes)]
    lx, rx, left_x, bottom_y = 810, 1470, 560, 640
    slots = [((left_x, 455), (0, -1)), ((685, 270), (1, 0)), ((1000, bottom_y), (-1, 0))]
    tags, branches = ['main'] * 3, []
    for b, (y, k) in enumerate(zip(rows, sizes)):
        seg, idx = (rx - lx) / k, []
        for j in range(k):
            slots.append(((lx + seg * (j + .5), y), (1, 0)))
            tags.append(f'{"ABC"[b]}{j + 1}')
            idx.append(len(slots) - 1)
        branches.append(idx)
    traces = [[(left_x, bottom_y), (left_x, 270), (lx, 270)], [(lx, rows[0]), (lx, rows[-1])],
              [(rx, 270), (rx, bottom_y), (left_x, bottom_y)]] + [[(lx, y), (rx, y)] for y in rows]
    nodes = [(left_x, 270), (left_x, bottom_y), (rx, bottom_y)] + [(lx, y) for y in rows] + [(rx, y) for y in rows]
    return {'slots': slots, 'tags': tags, 'traces': traces, 'nodes': nodes,
            'main': [0, 1, 2], 'branches': branches}


def build_layout(spec):
    kind, arg = spec
    return series_layout(arg) if kind == 'series' else parallel_layout(arg)


def tray_rects(n):
    if n <= 6:
        return [pg.Rect(60, 190 + i * 130, 360, 110) for i in range(n)]
    rows = (n + 1) // 2  # two columns when there are many parts
    return [pg.Rect(60 + (i // rows) * 200, 190 + (i % rows) * 96, 190, 86) for i in range(n)]


class BreadboardScreen:
    """Place the collected parts on the board. Every stage has its own circuit (see components.CIRCUITS):
    series loops, a switch, resistor values, and parallel branches. Battery, LED and switch can be flipped."""

    def __init__(self, game):
        self.game = game
        self.title_font = pg.font.SysFont(FONT_NAMES, 52, bold=True)
        self.body_font = pg.font.SysFont(FONT_NAMES, 30, bold=True)
        self.small_font = pg.font.SysFont(FONT_NAMES, 24, bold=True)
        self.tiny_font = pg.font.SysFont(FONT_NAMES, 18, bold=True)
        self.label_font = pg.font.SysFont(FONT_NAMES, 34, bold=True)
        self.test_btn = Button((BOARD.x, 800, 300, 70), 'TEST CIRCUIT')
        self.clear_btn = Button((BOARD.x + 330, 800, 300, 70), 'CLEAR')
        self.continue_btn = Button((BOARD.x, 800, 300, 70), 'CONTINUE')
        self.start()

    def start(self):
        self.circuit = self.game.circuit
        self.layout = build_layout(self.circuit['layout'])
        self.parts = list(self.circuit['parts'])   # part number i = tray entry i (duplicates allowed)
        self.tray = tray_rects(len(self.parts))
        self.slots = [None] * len(self.layout['slots'])  # holds part numbers
        self.selected = None
        battery_dir = random.choice((1, -1))
        # polarity starts random; the switch starts open; at least one LED starts wrong on purpose
        self.dir = {}
        for i, kind in enumerate(self.parts):
            if kind == 'battery':
                self.dir[i] = battery_dir
            elif kind == 'led':
                self.dir[i] = random.choice((1, -1))
            elif kind == 'switch':
                self.dir[i] = -1
        leds = [i for i, k in enumerate(self.parts) if k == 'led']
        if leds and all(self.dir[i] == battery_dir for i in leds):
            self.dir[leds[0]] = -battery_dir
        self.result = {}   # part number of each LED -> 'ok' / 'dim' / 'burnt' after a test
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

    def slot_rect(self, i):
        (cx, cy), flow = self.layout['slots'][i]
        rect = pg.Rect(0, 0, *((200, 96) if flow[0] else (96, 200)))
        rect.center = (cx, cy)
        return rect

    def slot_at(self, pos):
        best, best_d = None, 1e9
        for i, (center, _) in enumerate(self.layout['slots']):
            if self.slot_rect(i).inflate(12, 12).collidepoint(pos):
                d = math.hypot(pos[0] - center[0], pos[1] - center[1])
                if d < best_d:
                    best, best_d = i, d
        return best

    def left_click(self, pos):
        if self.test_btn.rect.collidepoint(pos):
            self.test()
            return
        if self.clear_btn.rect.collidepoint(pos):
            self.slots = [None] * len(self.slots)
            self.selected = None
            self.result = {}
            self.say('Board cleared.')
            return
        for i, rect in enumerate(self.tray):
            if rect.collidepoint(pos):
                if i in self.slots:
                    self.say(f'{PART_NAMES[self.parts[i]]} is already on the board. Click it to pick it up.')
                else:
                    self.selected = None if self.selected == i else i
                return
        slot = self.slot_at(pos)
        if slot is None:
            return
        self.result = {}
        if self.selected is not None:
            self.slots[slot], self.selected = self.selected, self.slots[slot]  # swap with what is there
        elif self.slots[slot] is not None:
            self.selected, self.slots[slot] = self.slots[slot], None
        else:
            self.say('Select a part from the left first.')

    def flip(self, pos):
        slot = self.slot_at(pos)
        idx = self.slots[slot] if slot is not None and self.slots[slot] is not None else self.selected
        if idx is None:
            self.say('Hover over a part (or select one) and press R to flip it.')
            return
        kind = self.parts[idx]
        if kind not in POLAR:
            self.say(f'The {PART_NAMES[kind]} has no polarity, so there is nothing to flip.')
            return
        self.dir[idx] *= -1
        self.result = {}
        if kind == 'switch':
            self.say('Switch closed.' if self.dir[idx] == 1 else 'Switch open.')
        else:
            self.say(f'Flipped the {PART_NAMES[kind]}.')

    def say(self, text, color='white'):
        self.message, self.message_color = text, color

    # ----- circuit check -----
    def kind_at(self, slot):
        return self.parts[self.slots[slot]]

    def evaluate(self):
        """Returns (success, message, {led part number: state})."""
        lay = self.layout
        if None in self.slots:
            return False, f'Fill all {len(self.slots)} slots before testing the circuit.', {}
        slots_of = lambda chain: [self.slots[s] for s in chain]
        branched = bool(lay['branches'])
        all_main = slots_of(lay['main'])
        battery = next((i for i in all_main if self.parts[i] == 'battery'), None)
        if branched and any(self.parts[i] == 'battery' for ch in lay['branches'] for i in slots_of(ch)):
            return False, 'The battery must go in the main loop so that every branch shares it.', {}
        if battery is None:
            return False, 'There is no power source in the circuit. Place the battery.', {}
        if branched and any(self.parts[i] in RESISTANCE or self.parts[i] == 'led' for i in all_main):
            return False, 'Resistors and LEDs go in the branches. In the main loop they would starve every branch.', {}
        if any(self.parts[i] == 'switch' and self.dir[i] == -1 for i in all_main):
            return False, 'The switch is open, so no current can flow. Right-click or press R to close it.', {}

        flow = self.dir[battery]  # +1: current goes clockwise / along the slots
        chains = [(f'Branch {"ABC"[b]}: ', slots_of(ch)) for b, ch in enumerate(lay['branches'])] \
            if branched else [('', all_main)]
        states, problems, currents = {}, [], []
        for where, idxs in chains:
            leds = [i for i in idxs if self.parts[i] == 'led']
            if not leds:
                problems.append(where + 'there is no LED to light.')
            elif any(self.parts[i] == 'switch' and self.dir[i] == -1 for i in idxs):
                problems.append(where + 'the switch is open.')
            elif any(self.dir[i] != flow for i in leds):
                problems.append(where + 'an LED is reverse-biased, so no current flows. Check polarity.')
            else:
                ohms = sum(RESISTANCE.get(self.parts[i], 0) for i in idxs)
                if ohms == 0:
                    states.update({i: 'burnt' for i in leds})
                    problems.append(where + 'no resistor! The LED burns out. Add a resistor in series.')
                    continue
                ma = 1000 * (SUPPLY_V - LED_DROP * len(leds)) / ohms
                state = 'burnt' if ma > LED_MAX_MA else 'dim' if ma < LED_MIN_MA else 'ok'
                states.update({i: state for i in leds})
                if state == 'burnt':
                    problems.append(f'{where}{ma:.0f} mA burns out the LED. Use a larger resistor.')
                elif state == 'dim':
                    problems.append(f'{where}only {ma:.1f} mA, the LED is too dim. Use a smaller resistor.')
                else:
                    currents.append(ma)
        if problems:
            return False, 'No good. ' + problems[0], states
        amps = ', '.join(f'{c:.0f}' for c in currents)
        return True, f'Every LED lights up! Current: {amps} mA per path. Press Enter.', states

    def test(self):
        ok, message, states = self.evaluate()
        self.result = states
        self.done = ok
        self.say(message, GREEN if ok else RED)

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

        def note(text):  # small caption above a horizontal part / right of a vertical one
            surf = self.small_font.render(text, True, (60, 50, 30))
            x, y = (center[0], center[1] - 54) if fx else (center[0] + 70 + surf.get_width() // 2, center[1])
            screen.blit(surf, (x - surf.get_width() // 2, y - surf.get_height() // 2))

        ink, w = (40, 40, 40), 6
        if kind == 'wire':
            pg.draw.line(screen, (60, 120, 230), P(-100), P(100), 8)
        elif kind in RESISTANCE:
            ts = [-60 + 120 * k / 6 for k in range(7)]
            us = [0, 18, -18, 18, -18, 18, 0]
            pg.draw.line(screen, ink, P(-100), P(-60), w)
            pg.draw.lines(screen, ink, False, [P(t, u) for t, u in zip(ts, us)], w)
            pg.draw.line(screen, ink, P(60), P(100), w)
            ohms = RESISTANCE[kind]
            note(f'{ohms // 1000} k ohm' if ohms >= 1000 else f'{ohms} ohm')
        elif kind == 'switch':
            pg.draw.line(screen, ink, P(-100), P(-34), w)
            pg.draw.line(screen, ink, P(34), P(100), w)
            for t in (-34, 34):
                pg.draw.circle(screen, ink, P(t), 8)
            closed = direction == 1
            pg.draw.line(screen, (200, 60, 60), P(-34), P(34, 0) if closed else P(26, -44), 7)
            note('closed' if closed else 'open')
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

    def draw_led_state(self, screen, state, center):
        if state in ('ok', 'dim'):
            radii = ((110, 50), (80, 90), (52, 140)) if state == 'ok' else ((50, 25), (34, 45))
            glow = pg.Surface((240, 240), pg.SRCALPHA)
            for r, a in radii:
                pg.draw.circle(glow, (255, 235, 110, a), (120, 120), r)
            screen.blit(glow, (center[0] - 120, center[1] - 120))
            if state == 'ok':
                pg.draw.circle(screen, (255, 250, 200), center, 14)
        elif state == 'burnt':
            cx, cy = center
            pg.draw.line(screen, (30, 30, 30), (cx - 30, cy - 30), (cx + 30, cy + 30), 9)
            pg.draw.line(screen, (30, 30, 30), (cx - 30, cy + 30), (cx + 30, cy - 30), 9)

    def draw_board(self, screen):
        pg.draw.rect(screen, BOARD_COLOR, BOARD, border_radius=16)
        pg.draw.rect(screen, (150, 140, 110), BOARD, 3, border_radius=16)
        for x in range(BOARD.left + 30, BOARD.right - 20, 28):
            for y in range(BOARD.top + 24, BOARD.bottom - 10, 28):
                pg.draw.circle(screen, (206, 199, 168), (x, y), 3)

        trace = LIT if self.done else COPPER
        for line in self.layout['traces']:
            pg.draw.lines(screen, trace, False, line, 8)
        for node in self.layout['nodes']:
            pg.draw.circle(screen, trace, node, 12)

        for i, ((center, flow), tag) in enumerate(zip(self.layout['slots'], self.layout['tags'])):
            rect = self.slot_rect(i)
            pg.draw.rect(screen, BOARD_COLOR, rect, border_radius=10)
            idx = self.slots[i]
            if idx is None:
                pg.draw.rect(screen, (170, 160, 130), rect, 3, border_radius=10)
                text = self.small_font.render(tag, True, (140, 130, 100))
                screen.blit(text, (rect.centerx - text.get_width() // 2, rect.centery - text.get_height() // 2))
            else:
                kind = self.parts[idx]
                self.draw_symbol(kind, center, flow, self.dir.get(idx, 1))
                if kind == 'led':
                    self.draw_led_state(screen, self.result.get(idx), center)

    def draw_tray(self, screen):
        screen.blit(self.small_font.render('PARTS', True, GOLD), (60, 164))
        compact = len(self.parts) > 6
        for i, (kind, rect) in enumerate(zip(self.parts, self.tray)):
            placed = i in self.slots
            border = GOLD if self.selected == i else ((120, 100, 140) if placed else LILAC)
            pg.draw.rect(screen, (62, 18, 96), rect, border_radius=12)
            pg.draw.rect(screen, border, rect, 4 if self.selected == i else 2, border_radius=12)
            size = 56 if compact else 90
            screen.blit(get_part_icon(kind, size, dim=placed), (rect.x + 8, rect.centery - size // 2))
            font = self.tiny_font if compact else self.small_font
            name = PART_NAMES[kind]
            lines = [name.split(' (')[0], '(' + name.split(' (')[1]] if ' (' in name else name.split(' ', 1)
            color = (150, 130, 170) if placed else 'white'
            h = font.get_height()
            y = rect.centery - h * len(lines) // 2
            for line in lines:
                screen.blit(font.render(line, True, color), (rect.x + size + 18, y))
                y += h

    def draw(self):
        screen = self.game.screen
        screen.fill(BG)
        screen.blit(self.title_font.render('BREADBOARD', True, GOLD), (60, 18))
        stage = self.body_font.render(f"Stage {self.game.level + 1}: {self.circuit['title']}", True, LILAC)
        screen.blit(stage, (420, 32))
        screen.blit(self.small_font.render(self.circuit['goal'], True, 'white'), (60, 82))
        screen.blit(self.small_font.render(self.circuit['hint'], True, LILAC), (60, 110))
        info = 'Right-click or R: flip a part / toggle the switch.   Battery 9 V, LED drops 2 V, needs 10-25 mA.'
        screen.blit(self.small_font.render(info, True, LILAC), (60, 138))

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

        if self.selected is not None and not self.done:  # part following the cursor
            icon = get_part_icon(self.parts[self.selected], 80)
            mx, my = pg.mouse.get_pos()
            screen.blit(icon, (mx - 40, my - 40))
