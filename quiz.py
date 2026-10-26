import pygame as pg
from settings import *

FONT_NAMES = 'couriernew,courier,monospace'


STAGES = [
    {
        'name': 'Stage 1: Physics 2',
        'q': ('What law states that the line integral of magnetic field around a closed loop '
              'is proportional to the electric current enclosed?'),
        'choices': ["A) Gauss's Law", "B) Ampere's Law", "C) Faraday's Law", "D) Coulomb's Law"],
        'correct': 1,
    },
    {
        'name': 'Stage 2: Circuit Analysis',
        'q': ('Which theorem replaces a linear active network with a single voltage source '
              'and series resistor?'),
        'choices': ["A) Norton's Theorem", "B) Thevenin's Theorem", 'C) Superposition Theorem',
                    'D) Maximum Power Transfer'],
        'correct': 1,
    },
    {
        'name': 'Stage 3: Electronic Devices',
        'q': 'In which region does a Zener diode normally operate?',
        'choices': ['A) Forward active region', 'B) Cutoff region', 'C) Breakdown / Zener region',
                    'D) Saturation region'],
        'correct': 2,
    },
    {
        'name': 'Stage 4: Communications',
        'q': ('What modulation technique shifts the frequency of a carrier wave in accordance '
              'with the message signal?'),
        'choices': ['A) Amplitude Modulation (AM)', 'B) Frequency Modulation (FM)',
                    'C) Phase Shift Keying (PSK)', 'D) Pulse Code Modulation (PCM)'],
        'correct': 1,
    },
    {
        'name': 'Stage 5: Advanced Telecom (Final Boss to graduate)',
        'q': ('Which multiple access technology is fundamental to 4G LTE and 5G wireless '
              'networks to avoid ISI?'),
        'choices': ['A) CDMA', 'B) TDMA', 'C) FDMA',
                    'D) OFDM (Orthogonal Frequency Division Multiplexing)'],
        'correct': 3,
    },
]

CORRECT_POINTS = 500


class QuizScreen:
    BG = (42, 8, 69)
    LILAC = (216, 180, 254)
    GOLD = (255, 200, 80)
    INK = (42, 8, 69)
    GREEN = (120, 220, 120)
    RED = (240, 110, 110)
    DIM = (150, 130, 170)

    def __init__(self, game):
        self.game = game
        self.title_font = pg.font.SysFont(FONT_NAMES, 52, bold=True)
        self.body_font = pg.font.SysFont(FONT_NAMES, 34, bold=True)
        self.small_font = pg.font.SysFont(FONT_NAMES, 28, bold=True)
        self.stage = STAGES[0]
        self.buttons = []
        self.picked = None
        self.result = None
        self.locked_until = 0

    def start(self):
        self.stage = STAGES[self.game.level]
        self.picked = None
        self.result = None
        self.locked_until = pg.time.get_ticks() + 800
        btn_w, btn_h, gap = 1200, 80, 22
        x, y0 = HALF_WIDTH - btn_w // 2, 430
        self.buttons = [pg.Rect(x, y0 + i * (btn_h + gap), btn_w, btn_h)
                        for i in range(len(self.stage['choices']))]
        pg.mouse.set_visible(True)
        pg.event.set_grab(False)

    def handle_event(self, event):
        if pg.time.get_ticks() < self.locked_until:
            return

        clicked = event.type == pg.MOUSEBUTTONDOWN and event.button == 1
        if self.result is not None:
            confirm_keys = (pg.K_RETURN, pg.K_KP_ENTER, pg.K_SPACE)
            if clicked or (event.type == pg.KEYDOWN and event.key in confirm_keys):
                self.game.finish_quiz(self.result)
            return

        choice = None
        if clicked:
            for i, rect in enumerate(self.buttons):
                if rect.collidepoint(event.pos):
                    choice = i
        elif event.type == pg.KEYDOWN:
            if pg.K_1 <= event.key <= pg.K_4:
                choice = event.key - pg.K_1
            elif pg.K_a <= event.key <= pg.K_d:
                choice = event.key - pg.K_a

        if choice is not None and choice < len(self.buttons):
            self.picked = choice
            self.result = choice == self.stage['correct']
            if self.result:
                self.game.score += CORRECT_POINTS
            self.locked_until = pg.time.get_ticks() + 500

    @staticmethod
    def wrap(text, font, max_width):
        lines, line = [], ''
        for word in text.split():
            trial = f'{line} {word}'.strip()
            if font.size(trial)[0] > max_width and line:
                lines.append(line)
                line = word
            else:
                line = trial
        return lines + [line]

    def blit_center(self, surf, y):
        self.game.screen.blit(surf, (HALF_WIDTH - surf.get_width() // 2, y))

    def draw(self):
        screen = self.game.screen
        stage = self.stage
        screen.fill(self.BG)

        score = self.small_font.render(f'Score: {self.game.score}', True, self.LILAC)
        screen.blit(score, (30, 20))
        self.blit_center(self.title_font.render('HERE COMES THE MAJOR!', True, self.GOLD), 40)
        self.blit_center(self.small_font.render(stage['name'], True, self.LILAC), 110)

        y = 175
        for line in self.wrap(stage['q'], self.body_font, 1400):
            surf = self.body_font.render(line, True, 'white')
            self.blit_center(surf, y)
            y += surf.get_height() + 6

        mouse = pg.mouse.get_pos()
        for i, (rect, text) in enumerate(zip(self.buttons, stage['choices'])):
            if self.result is None:
                color = self.LILAC if rect.collidepoint(mouse) else (255, 255, 255)
            elif i == stage['correct']:
                color = self.GREEN
            elif i == self.picked:
                color = self.RED
            else:
                color = self.DIM
            pg.draw.rect(self.game.screen, color, rect, border_radius=10)
            label = self.body_font.render(text, True, self.INK)
            screen.blit(label, (rect.x + 24, rect.centery - label.get_height() // 2))

        if self.result is None:
            hint = 'Click an answer, or press 1-4 / A-D'
        else:
            if self.result:
                msg, color = f'CORRECT!  +{CORRECT_POINTS} points', self.GREEN
            else:
                msg, color = 'INCORRECT - review your ECE formula notes!', self.RED
            self.blit_center(self.body_font.render(msg, True, color), 350)
            hint = 'Click or press Enter to continue'
        self.blit_center(self.small_font.render(hint, True, self.LILAC), 850)

    def draw_final_score(self):
        text = f'Final Score: {self.game.score}'
        shadow = self.title_font.render(text, True, (0, 0, 0))
        surf = self.title_font.render(text, True, self.GOLD)
        y = HEIGHT - 120
        self.game.screen.blit(shadow, (HALF_WIDTH - surf.get_width() // 2 + 3, y + 3))
        self.blit_center(surf, y)
