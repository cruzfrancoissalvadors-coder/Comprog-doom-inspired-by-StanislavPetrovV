import sys
from collections import Counter
import pygame as pg
from settings import *
from quiz import QuizScreen, FONT_NAMES, STAGES
from components import PART_NAMES, get_part_icon

BG, LILAC, GOLD, INK = QuizScreen.BG, QuizScreen.LILAC, QuizScreen.GOLD, QuizScreen.INK
CONFIRM_KEYS = (pg.K_RETURN, pg.K_KP_ENTER, pg.K_SPACE)


class Button:
    def __init__(self, rect, text):
        self.rect = pg.Rect(rect)
        self.text = text

    def hit(self, event):
        return event.type == pg.MOUSEBUTTONDOWN and event.button == 1 and self.rect.collidepoint(event.pos)

    def draw(self, screen, font, enabled=True):
        hover = enabled and self.rect.collidepoint(pg.mouse.get_pos())
        color = GOLD if hover else (LILAC if enabled else (120, 100, 140))
        pg.draw.rect(screen, color, self.rect, border_radius=12)
        label = font.render(self.text, True, INK)
        screen.blit(label, (self.rect.centerx - label.get_width() // 2,
                            self.rect.centery - label.get_height() // 2))


def blit_center(screen, surf, y, cx=HALF_WIDTH):
    screen.blit(surf, (cx - surf.get_width() // 2, y))


class MenuScreen:
    """Home page."""

    def __init__(self, game):
        self.game = game
        self.huge_font = pg.font.SysFont(FONT_NAMES, 96, bold=True)
        self.body_font = pg.font.SysFont(FONT_NAMES, 34, bold=True)
        self.small_font = pg.font.SysFont(FONT_NAMES, 26, bold=True)
        self.start_btn = Button((HALF_WIDTH - 220, 500, 440, 90), 'START GAME')
        self.quit_btn = Button((HALF_WIDTH - 220, 620, 440, 90), 'QUIT')

    def handle_event(self, event):
        if self.start_btn.hit(event) or (event.type == pg.KEYDOWN and event.key in CONFIRM_KEYS):
            self.game.start_run()
        elif self.quit_btn.hit(event):
            pg.quit()
            sys.exit()

    def draw_traces(self, screen):
        # decorative circuit traces
        color = (78, 36, 118)
        for y, x0, x1 in ((120, 0, 420), (200, 0, 300), (780, 1180, 1600), (840, 1300, 1600)):
            pg.draw.line(screen, color, (x0, y), (x1, y), 6)
            pg.draw.circle(screen, color, (x1 if x0 == 0 else x0, y), 12)
        pg.draw.lines(screen, color, False, [(1600, 120), (1250, 120), (1190, 180), (1190, 215)], 6)
        pg.draw.lines(screen, color, False, [(0, 780), (330, 780), (400, 710), (400, 600)], 6)

    def draw(self):
        screen = self.game.screen
        screen.fill(BG)
        self.draw_traces(screen)

        # pulsing LED above the title
        pulse = 0.5 + 0.5 * math.sin(pg.time.get_ticks() / 400)
        glow = pg.Surface((200, 200), pg.SRCALPHA)
        pg.draw.circle(glow, (255, 90, 90, int(50 + 70 * pulse)), (100, 100), 90)
        pg.draw.circle(glow, (255, 120, 120, int(90 + 100 * pulse)), (100, 100), 55)
        screen.blit(glow, (HALF_WIDTH - 100, 40))
        pg.draw.circle(screen, (240, 60, 60), (HALF_WIDTH, 140), 28)

        blit_center(screen, self.huge_font.render('ELECTROQUEST', True, GOLD), 250)
        blit_center(screen, self.body_font.render('Shoot. Collect parts. Build the circuit. Pass the boards.',
                                                  True, LILAC), 380)
        self.start_btn.draw(screen, self.body_font)
        self.quit_btn.draw(screen, self.body_font)
        blit_center(screen, self.small_font.render('Click START GAME or press Enter', True, LILAC), 760)


class InstructionsScreen:
    """Pop-up shown at the start of every stage."""

    def __init__(self, game):
        self.game = game
        self.title_font = pg.font.SysFont(FONT_NAMES, 52, bold=True)
        self.body_font = pg.font.SysFont(FONT_NAMES, 34, bold=True)
        self.small_font = pg.font.SysFont(FONT_NAMES, 26, bold=True)
        self.tiny_font = pg.font.SysFont(FONT_NAMES, 22, bold=True)
        self.panel = pg.Rect(250, 40, 1100, 820)
        self.start_btn = Button((HALF_WIDTH - 200, 760, 400, 80), 'START')

    def handle_event(self, event):
        if self.start_btn.hit(event) or (event.type == pg.KEYDOWN and event.key in CONFIRM_KEYS):
            self.game.begin_stage()

    def draw(self):
        game, screen = self.game, self.game.screen
        screen.fill(BG)
        pg.draw.rect(screen, (62, 18, 96), self.panel, border_radius=18)
        pg.draw.rect(screen, LILAC, self.panel, 3, border_radius=18)
        x, width = self.panel.x + 50, self.panel.width - 100

        blit_center(screen, self.title_font.render('MISSION BRIEFING', True, GOLD), 65)
        blit_center(screen, self.small_font.render(STAGES[game.level]['name'], True, LILAC), 135)

        screen.blit(self.small_font.render('OBJECTIVE', True, GOLD), (x, 190))
        y = 225
        for line in QuizScreen.wrap(game.circuit['goal'], self.body_font, width):
            screen.blit(self.body_font.render(line, True, 'white'), (x, y))
            y += 42

        steps = ['1. Shoot the enemies. Some of them carry electronic parts.',
                 '2. Walk over each dropped part to collect it.',
                 '3. Bring every part to the breadboard table and press E.',
                 '4. Complete the circuit on the breadboard.']
        if QUIZ_AFTER_CIRCUIT:
            steps.append('5. Then face the major exam to move up a stage.')
        y += 14
        for step in steps:
            for line in QuizScreen.wrap(step, self.small_font, width):
                screen.blit(self.small_font.render(line, True, LILAC), (x, y))
                y += 32

        # tip for this stage
        for line in QuizScreen.wrap('TIP: ' + game.circuit['hint'], self.tiny_font, width)[:2]:
            screen.blit(self.tiny_font.render(line, True, GOLD), (x, y + 6))
            y += 26

        # parts you need to find (decoys may be among them)
        counts = Counter(game.circuit['parts'])
        y = max(y + 14, 520)
        slot_w = width // len(counts)
        for i, (kind, n) in enumerate(counts.items()):
            cx = x + slot_w * i + slot_w // 2
            screen.blit(get_part_icon(kind, 84), (cx - 42, y))
            name = PART_NAMES[kind]
            lines = [name.split(' (')[0], '(' + name.split(' (')[1]] if ' (' in name else name.split(' ', 1)
            if n > 1:
                lines[0] += f' x{n}'
            for j, line in enumerate(lines):
                label = self.tiny_font.render(line, True, 'white')
                screen.blit(label, (cx - label.get_width() // 2, y + 86 + j * 22))

        controls = 'WASD move   Mouse aim   Click shoot   E use table   Esc quit'
        blit_center(screen, self.tiny_font.render(controls, True, LILAC), 715)
        self.start_btn.draw(screen, self.body_font)

