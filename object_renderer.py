import pygame as pg
from settings import *
from quiz import STAGES, FONT_NAMES
from components import get_part_icon


class ObjectRenderer:
    def __init__(self, game):
        self.game = game
        self.screen = game.screen
        self.wall_textures = self.load_wall_textures()
        self.sky_image = self.get_texture('resources/textures/sky.png', (WIDTH, HALF_HEIGHT + MAX_PITCH))
        self.sky_offset = 0
        self.blood_screen = self.get_texture('resources/textures/blood_screen.png', RES)
        self.digit_size = 90
        self.digit_images = [self.get_texture(f'resources/textures/digits/{i}.png', [self.digit_size] * 2)
                             for i in range(11)]
        self.digits = dict(zip(map(str, range(11)), self.digit_images))
        self.game_over_image = self.get_texture('resources/textures/game_over.png', RES)
        self.win_image = self.get_texture('resources/textures/win.png', RES)
        self.hud_font = pg.font.SysFont(FONT_NAMES, 34, bold=True)
        self.hud_small_font = pg.font.SysFont(FONT_NAMES, 26, bold=True)

    def draw(self):
        self.draw_background()
        self.render_game_objects()
        self.draw_player_health()
        self.draw_hud()
        self.draw_crosshair()  # add this line

    def draw_crosshair(self, size=12, gap=5, color=(255, 255, 255)):
        cx, cy = HALF_WIDTH, HALF_HEIGHT
        # dark outline first so it stays visible on light walls
        for c, w in (((0, 0, 0), 4), (color, 2)):
            pg.draw.line(self.screen, c, (cx - gap - size, cy), (cx - gap, cy), w)  # left
            pg.draw.line(self.screen, c, (cx + gap, cy), (cx + gap + size, cy), w)  # right
            pg.draw.line(self.screen, c, (cx, cy - gap - size), (cx, cy - gap), w)  # top
            pg.draw.line(self.screen, c, (cx, cy + gap), (cx, cy + gap + size), w)  # bottom

    def draw_text(self, text, x, y, font, color=(255, 230, 120), center=False):
        surf = font.render(text, True, color)
        shadow = font.render(text, True, (0, 0, 0))
        if center:
            x -= surf.get_width() // 2
        self.screen.blit(shadow, (x + 2, y + 2))
        self.screen.blit(surf, (x, y))
        return surf.get_height()

    def draw_hud(self):
        game = self.game
        enemies_left = len(game.object_handler.npc_positions)
        lines = [
            STAGES[game.level]['name'],
            f'Score: {game.score}',
            f'Enemies left: {enemies_left}',
        ]
        y = 10
        for text in lines:
            width = self.hud_font.size(text)[0]
            y += self.draw_text(text, WIDTH - width - 20, y, self.hud_font) + 4
        self.draw_parts_row(y)
        self.draw_text('Objective: ' + game.circuit['goal'], 20, 100, self.hud_small_font)
        self.draw_table_prompt()
        if pg.time.get_ticks() < game.toast_until:
            self.draw_text(game.toast_text, HALF_WIDTH, 150, self.hud_font, (160, 255, 160), center=True)

    def draw_parts_row(self, y):
        game = self.game
        parts, size, gap = game.circuit['parts'], 56, 10
        x0 = WIDTH - 20 - len(parts) * (size + gap) + gap
        for i, kind in enumerate(parts):
            rect = pg.Rect(x0 + i * (size + gap), y + 6, size, size)
            got = kind in game.inventory
            pg.draw.rect(self.screen, (20, 12, 30), rect, border_radius=8)
            self.screen.blit(get_part_icon(kind, size, dim=not got), rect)
            pg.draw.rect(self.screen, (120, 230, 120) if got else (110, 90, 130), rect, 2, border_radius=8)

    def draw_table_prompt(self):
        game = self.game
        if not game.object_handler.table.near():
            return
        if game.has_all_parts():
            text, color = 'Press E to use the breadboard table', (160, 255, 160)
        else:
            count = f'{len(game.inventory)}/{len(game.circuit["parts"])}'
            text, color = f'Collect all the parts first ({count})', (255, 230, 120)
        self.draw_text(text, HALF_WIDTH, 200, self.hud_font, color, center=True)

    def win(self):
        self.screen.blit(self.win_image, (0, 0))

    def game_over(self):
        self.screen.blit(self.game_over_image, (0, 0))

    def draw_player_health(self):
        health = str(self.game.player.health)
        for i, char in enumerate(health):
            self.screen.blit(self.digits[char], (i * self.digit_size, 0))
        self.screen.blit(self.digits['10'], ((i + 1) * self.digit_size, 0))

    def player_damage(self):
        self.screen.blit(self.blood_screen, (0, 0))

    def draw_background(self):
        horizon = HALF_HEIGHT + int(self.game.player.pitch)
        self.sky_offset = (self.sky_offset + 4.5 * self.game.player.rel) % WIDTH
        sky_y = horizon - self.sky_image.get_height()  # sky bottom edge sits on the horizon
        self.screen.blit(self.sky_image, (-self.sky_offset, sky_y))
        self.screen.blit(self.sky_image, (-self.sky_offset + WIDTH, sky_y))
        # floor
        pg.draw.rect(self.screen, FLOOR_COLOR, (0, horizon, WIDTH, HEIGHT - horizon))

    def render_game_objects(self):
        list_objects = sorted(self.game.raycasting.objects_to_render, key=lambda t: t[0], reverse=True)
        for depth, image, pos in list_objects:
            self.screen.blit(image, pos)

    @staticmethod
    def get_texture(path, res=(TEXTURE_SIZE, TEXTURE_SIZE)):
        texture = pg.image.load(path).convert_alpha()
        return pg.transform.scale(texture, res)

    def load_wall_textures(self):
        return {
            1: self.get_texture('resources/textures/1.png'),
            2: self.get_texture('resources/textures/2.png'),
            3: self.get_texture('resources/textures/3.png'),
            4: self.get_texture('resources/textures/4.png'),
            5: self.get_texture('resources/textures/5.png'),
        }