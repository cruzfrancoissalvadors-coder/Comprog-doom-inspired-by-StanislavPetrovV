import pygame as pg
import sys
from settings import *
from map import *
from player import *
from raycasting import *
from object_renderer import *
from sprite_object import *
from object_handler import *
from weapon import *
from sound import *
from pathfinding import *
from quiz import *   # add to imports

class Game:
    def __init__(self):
        ...
        self.state = 'PLAYING'
        self.level = 0
        self.score = 0
        self.new_game()

    def new_game(self):
        ...
        self.quiz = QuizScreen(self)
        self.state = 'PLAYING'
        pg.mouse.set_visible(False)
        pg.event.set_grab(True)

    def start_quiz(self):                 # called when all NPCs are dead
        self.state = 'QUIZ'
        self.quiz.start()

    def answer_quiz(self, correct):
        if correct:
            self.score += 500
            self.level += 1
            if self.level >= len(STAGES):
                self.object_renderer.win()
                pg.display.flip()
                pg.time.delay(2000)
                self.level, self.score = 0, 0
            self.new_game()               # reload map/NPCs for the next stage
        else:
            self.object_renderer.game_over()
            pg.display.flip()
            pg.time.delay(1500)
            self.level, self.score = 0, 0
            self.new_game()

    def update(self):
        if self.state == 'PLAYING':
            self.player.update()
            self.raycasting.update()
            self.object_handler.update()
            self.weapon.update()
        pg.display.flip()
        self.delta_time = self.clock.tick(FPS)
        pg.display.set_caption(f'{self.clock.get_fps():.1f}')

    def draw(self):
        if self.state == 'QUIZ':
            self.quiz.draw()
        else:
            self.object_renderer.draw()
            self.weapon.draw()

    def check_events(self):
        self.global_trigger = False
        for event in pg.event.get():
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                pg.quit()
                sys.exit()
            elif event.type == self.global_event:
                self.global_trigger = True
            if self.state == 'QUIZ':
                self.quiz.handle_event(event)
            else:
                self.player.single_fire_event(event)
class Game:
    def __init__(self):
        pg.init()
        pg.mouse.set_visible(False)
        self.screen = pg.display.set_mode(RES)
        pg.event.set_grab(True)
        self.clock = pg.time.Clock()
        self.delta_time = 1
        self.global_trigger = False
        self.global_event = pg.USEREVENT + 0
        pg.time.set_timer(self.global_event, 40)
        self.new_game()

    def new_game(self):
        self.map = Map(self)
        self.player = Player(self)
        self.object_renderer = ObjectRenderer(self)
        self.raycasting = RayCasting(self)
        self.object_handler = ObjectHandler(self)
        self.weapon = Weapon(self)
        self.sound = Sound(self)
        self.pathfinding = PathFinding(self)
        pg.mixer.music.play(-1)

    def update(self):
        self.player.update()
        self.raycasting.update()
        self.object_handler.update()
        self.weapon.update()
        pg.display.flip()
        self.delta_time = self.clock.tick(FPS)
        pg.display.set_caption(f'{self.clock.get_fps() :.1f}')

    def draw(self):
        # self.screen.fill('black')
        self.object_renderer.draw()
        self.weapon.draw()
        # self.map.draw()
        # self.player.draw()

    def check_events(self):
        self.global_trigger = False
        for event in pg.event.get():
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                pg.quit()
                sys.exit()
            elif event.type == self.global_event:
                self.global_trigger = True
            self.player.single_fire_event(event)

    def run(self):
        while True:
            self.check_events()
            self.update()
            self.draw()


if __name__ == '__main__':
    game = Game()
    game.run()
