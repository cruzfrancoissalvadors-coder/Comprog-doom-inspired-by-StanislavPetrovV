from map import *
from player import *
from raycasting import *
from object_renderer import *
from object_handler import *
from weapon import *
from sound import *
from pathfinding import *
from components import *
from screens import *
from breadboard import *


class Game:
    def __init__(self):
        pg.init()
        self.screen = pg.display.set_mode(RES)
        self.clock = pg.time.Clock()
        self.delta_time = 1
        self.global_trigger = False
        self.global_event = pg.USEREVENT + 0
        pg.time.set_timer(self.global_event, 40)
        self.level = 0
        self.score = 0
        self.inventory = Counter()
        self.circuit = CIRCUITS[0]
        self.toast_text, self.toast_until = '', 0
        self.state = 'MENU'
        self.quiz = QuizScreen(self)
        self.menu = MenuScreen(self)
        self.instructions = InstructionsScreen(self)
        self.breadboard = BreadboardScreen(self)
        self.screens = {'MENU': self.menu, 'INSTRUCTIONS': self.instructions,
                        'BREADBOARD': self.breadboard, 'QUIZ': self.quiz}
        self.new_game('MENU')

    def new_game(self, state='INSTRUCTIONS'):
        self.inventory = Counter()
        self.circuit = CIRCUITS[self.level % len(CIRCUITS)]
        self.map = Map(self)
        self.player = Player(self)
        self.object_renderer = ObjectRenderer(self)
        self.raycasting = RayCasting(self)
        self.object_handler = ObjectHandler(self)
        self.weapon = Weapon(self)
        self.sound = Sound(self)
        self.pathfinding = PathFinding(self)
        pg.mixer.music.play(-1)
        self.set_state(state)

    def set_state(self, state):
        self.state = state
        playing = state == 'PLAYING'
        pg.mouse.set_visible(not playing)
        pg.event.set_grab(playing)
        if playing:
            pg.mouse.set_pos(HALF_WIDTH, HALF_HEIGHT)
            pg.mouse.get_rel()

    def restart_run(self):
        self.level = 0
        self.score = 0
        self.new_game('MENU')

    def start_run(self):
        self.set_state('INSTRUCTIONS')

    def begin_stage(self):
        self.set_state('PLAYING')

    def toast(self, text, seconds=2):
        self.toast_text, self.toast_until = text, pg.time.get_ticks() + int(seconds * 1000)

    def has_all_parts(self):
        return all(self.inventory[k] >= n for k, n in Counter(self.circuit['parts']).items())

    def open_breadboard(self):
        self.set_state('BREADBOARD')
        self.breadboard.start()

    def finish_circuit(self):
        self.score += CIRCUIT_POINTS
        if QUIZ_AFTER_CIRCUIT:
            self.start_quiz()
        else:
            self.advance_stage()

    def start_quiz(self):
        self.set_state('QUIZ')
        self.quiz.start()

    def advance_stage(self):
        self.level += 1
        if self.level >= len(STAGES):
            self.object_renderer.win()
            self.quiz.draw_final_score()
            pg.display.flip()
            pg.time.delay(3000)
            self.restart_run()
        else:
            self.new_game('INSTRUCTIONS')

    def finish_quiz(self, correct):
        if correct:
            self.advance_stage()
        else:
            self.object_renderer.game_over()
            self.quiz.draw_final_score()
            pg.display.flip()
            pg.time.delay(2500)
            self.restart_run()

    def update(self):
        if self.state == 'PLAYING':
            self.player.update()
            self.raycasting.update()
            self.object_handler.update()
            self.weapon.update()
        pg.display.flip()
        # cap delta_time so a pause (end screens, quiz) can't make the player jump
        self.delta_time = max(1, min(self.clock.tick(FPS if self.state == 'PLAYING' else 60), 100))
        pg.display.set_caption(f'{self.clock.get_fps() :.1f}')

    def draw(self):
        # self.screen.fill('black')
        if self.state in self.screens:
            self.screens[self.state].draw()
            return
        self.object_renderer.draw()
        self.weapon.draw()
        # self.map.draw()
        # self.player.draw()

    def check_events(self):
        self.global_trigger = False
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                sys.exit()
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                if self.state == 'BREADBOARD':  # Esc leaves the breadboard instead of quitting
                    self.set_state('PLAYING')
                    continue
                pg.quit()
                sys.exit()
            if event.type == self.global_event:
                self.global_trigger = True
            if self.state in self.screens:
                self.screens[self.state].handle_event(event)
            else:
                self.player.single_fire_event(event)
                if event.type == pg.KEYDOWN and event.key == pg.K_e:
                    self.object_handler.interact()

    def run(self):
        while True:
            self.check_events()
            self.update()
            self.draw()


if __name__ == '__main__':
    game = Game()
    game.run()
