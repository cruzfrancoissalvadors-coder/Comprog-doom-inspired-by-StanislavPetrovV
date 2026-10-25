import math

# game settings
RES = WIDTH, HEIGHT = 1600, 900
# RES = WIDTH, HEIGHT = 1920, 1080
HALF_WIDTH = WIDTH // 2
HALF_HEIGHT = HEIGHT // 2
FPS = 0

PLAYER_POS = 1.5, 5  # mini_map
PLAYER_ANGLE = 0
PLAYER_SPEED = 0.004
PLAYER_ROT_SPEED = 0.002
PLAYER_SIZE_SCALE = 60
PLAYER_MAX_HEALTH = 100

MOUSE_SENSITIVITY = 0.0003
MOUSE_MAX_REL = 40
MOUSE_SENSITIVITY_Y = 0.35  # pixels of view shift per pixel of mouse movement
MAX_PITCH = 300             # how far (in pixels) the horizon can move up or down
PITCH_KEY_SPEED = 0.5       # pixels per ms when using the Up/Down arrow keys
MOUSE_BORDER_LEFT = 100
MOUSE_BORDER_RIGHT = WIDTH - MOUSE_BORDER_LEFT
MOUSE_BORDER_TOP = 100
MOUSE_BORDER_BOTTOM = HEIGHT - MOUSE_BORDER_TOP

FLOOR_COLOR = (30, 30, 30)

FOV = math.pi / 3
HALF_FOV = FOV / 2
NUM_RAYS = WIDTH // 2
HALF_NUM_RAYS = NUM_RAYS // 2
DELTA_ANGLE = FOV / NUM_RAYS
MAX_DEPTH = 20

SCREEN_DIST = HALF_WIDTH / math.tan(HALF_FOV)
SCALE = WIDTH // NUM_RAYS

TEXTURE_SIZE = 256
HALF_TEXTURE_SIZE = TEXTURE_SIZE // 2

# circuit / parts feature
CIRCUIT_POINTS = 200        # score for completing the breadboard
QUIZ_AFTER_CIRCUIT = True   # False: skip the quiz and go straight to the next stage
TABLE_POS = 9.5, 4.5        # breadboard table (map coordinates)
INTERACT_DIST = 1.8         # how close you must be to the table to use it
PICKUP_RADIUS = 0.7         # how close you must be to a dropped part to collect it
