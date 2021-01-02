import os
import sys
from random import random
from queue import Queue
import pygame
import pygame_gui
import pytmx
import pickle


WINDOW_SIZE = WINDOW_WIDTH, WINDOW_HEIGHT = 600, 600
TITLE = 'BATTLE TANKS'
TILE_SIZE = 40
FPS = 40
MAPS_DIR = 'data/maps'
FONTS_DIR = 'data/fonts'

# Control
FORWARD = 91
BACK = 92
TURN_RIGHT = 93
TURN_LEFT = 94
TURN_RIGHT_TURRET = 95
TURN_LEFT_TURRET = 96
SHOOT = 97

# Control keys dicts
CONTROL_KEYS_V1 = {FORWARD: pygame.K_w, BACK: pygame.K_s,
                   TURN_RIGHT: pygame.K_d, TURN_LEFT: pygame.K_a,
                   TURN_RIGHT_TURRET: pygame.K_e, TURN_LEFT_TURRET: pygame.K_q,
                   SHOOT: pygame.K_r}
CONTROL_KEYS_V2 = {FORWARD: pygame.K_g, BACK: pygame.K_b,
                   TURN_RIGHT: pygame.K_n, TURN_LEFT: pygame.K_v,
                   TURN_RIGHT_TURRET: pygame.K_h, TURN_LEFT_TURRET: pygame.K_f,
                   SHOOT: pygame.K_c}
CONTROL_KEYS_V3 = {FORWARD: pygame.K_i, BACK: pygame.K_k,
                   TURN_RIGHT: pygame.K_j, TURN_LEFT: pygame.K_l,
                   TURN_RIGHT_TURRET: pygame.K_u, TURN_LEFT_TURRET: pygame.K_o,
                   SHOOT: pygame.K_p}
CONTROL_KEYS_V4 = {FORWARD: pygame.K_UP, BACK: pygame.K_DOWN,
                   TURN_RIGHT: pygame.K_RIGHT, TURN_LEFT: pygame.K_LEFT,
                   TURN_RIGHT_TURRET: 44, TURN_LEFT_TURRET: 46, SHOOT: 47}

DIRECTION_MOVE_BY_ANGLE = {0: (0, -1), 90: (-1, 0), 180: (0, 1), 270: (1, 0)}

COLOR_TEXT = pygame.Color((255, 255, 255))

# Init the pygame
pygame.init()
pygame.mixer.init()
pygame.display.set_caption(TITLE)
screen = pygame.display.set_mode(WINDOW_SIZE)
clock = pygame.time.Clock()

custom_settings = {'language': 'русский',
                   'sound_value': 100,
                   'music_value': 100,
                   'user_name': ''}

player_coords = (0, 0)
lvl_count_id = 5

general_manager = pygame_gui.UIManager(WINDOW_SIZE)
main_menu_manager = pygame_gui.UIManager(WINDOW_SIZE)
settings_menu_manager = pygame_gui.UIManager(WINDOW_SIZE)
game_types_menu_manager = pygame_gui.UIManager(WINDOW_SIZE)
game_level_menu_manager = pygame_gui.UIManager(WINDOW_SIZE)

# Init menu
intro_text_menu = ['ПРОДОЛЖИТЬ',
                   'ИГРАТЬ ЛОКАЛЬНО',
                   'РЕКОРДЫ',
                   'КАК ИГРАТЬ',
                   'НАСТРОЙКИ',
                   'ВЫЙТИ']

menu_btn_size = (150, 40)
sound_btn_size = (40, 40)
name_entry_line_size = (200, 29)
indent_between_buttons = 10
indent_down = round(WINDOW_WIDTH * 0.05)
indent_top = 118 + (404 - len(intro_text_menu) * (indent_between_buttons + menu_btn_size[1])) // 2
indent_left = 49

dict_menu_buttons = dict()
# init menu buttons
btn_menu_rect = pygame.Rect((indent_left, indent_top), menu_btn_size)
for btn_txt in intro_text_menu:
    dict_menu_buttons[btn_txt] = \
        pygame_gui.elements.UIButton(
            relative_rect=btn_menu_rect, text=btn_txt, manager=main_menu_manager)
    btn_menu_rect.y += menu_btn_size[1] + indent_between_buttons
# init sound off/on buttons
menu_sound_btn = pygame_gui.elements.UIButton(
    relative_rect=pygame.Rect((WINDOW_WIDTH - indent_left - sound_btn_size[0] * 2 - indent_between_buttons,
                               WINDOW_HEIGHT - indent_down - sound_btn_size[1]), sound_btn_size),
    text='sound_on', manager=main_menu_manager)
menu_music_btn = pygame_gui.elements.UIButton(
    relative_rect=pygame.Rect((WINDOW_WIDTH - indent_left - sound_btn_size[0],
                               WINDOW_HEIGHT - indent_down - sound_btn_size[1]), sound_btn_size),
    text='music_on', manager=main_menu_manager)
# init set name menu button
name_entry_line = pygame_gui.elements.UITextEntryLine(
    relative_rect=pygame.Rect((indent_left, WINDOW_HEIGHT - indent_down - name_entry_line_size[1]),
                              name_entry_line_size), manager=main_menu_manager)

# Init settings buttons
btn_size = (200, 50)
btn_cords = (WINDOW_WIDTH - btn_size[0]) // 2, 200
language_menu_size = btn_size

indent_x = btn_size[1] + indent_between_buttons
small_btn_size = (btn_size[1], btn_size[1])
slider_size = (btn_size[0] - indent_between_buttons - btn_size[1], btn_size[1])

# init language menu
language_btn = pygame_gui.elements.ui_drop_down_menu.UIDropDownMenu(
    options_list=['Русский', 'Английский'],
    starting_option='Русский',
    relative_rect=pygame.Rect((btn_cords[0], btn_cords[1]), btn_size),
    manager=settings_menu_manager)
# init sound buttons
settings_sound_btn = pygame_gui.elements.UIButton(
    relative_rect=pygame.Rect((btn_cords[0], btn_cords[1] + indent_x), small_btn_size),
    text='SOUND', manager=settings_menu_manager)
sound_value_slider = pygame_gui.elements.ui_horizontal_slider.UIHorizontalSlider(
    relative_rect=pygame.Rect(
        (btn_cords[0] + small_btn_size[0] + indent_between_buttons,
         btn_cords[1] + indent_x), slider_size),
    value_range=(0, 101),
    start_value=100,
    manager=settings_menu_manager)

# init music buttons
settings_music_btn = pygame_gui.elements.UIButton(
    relative_rect=pygame.Rect((btn_cords[0], btn_cords[1] + indent_x * 2), small_btn_size),
    text='MUSIC', manager=settings_menu_manager)
music_value_slider = pygame_gui.elements.ui_horizontal_slider.UIHorizontalSlider(
    relative_rect=pygame.Rect((btn_cords[0] + small_btn_size[0] + indent_between_buttons,
                               btn_cords[1] + indent_x * 2), slider_size),
    value_range=(0, 101),
    start_value=100,
    manager=settings_menu_manager)

# init close button
settings_close_btn = pygame_gui.elements.UIButton(
    relative_rect=pygame.Rect((btn_cords[0], btn_cords[1] + indent_x * 3), btn_size),
    text='CLOSE', manager=settings_menu_manager)

# Init game types menu buttons
offset = 20
single_player_btn = pygame_gui.elements.UIButton(
    relative_rect=pygame.Rect((btn_cords[0], btn_cords[1] + offset), btn_size),
    text='SINGLE PLAYER', manager=game_types_menu_manager)
two_player_btn = pygame_gui.elements.UIButton(
    relative_rect=pygame.Rect((btn_cords[0], btn_cords[1] + offset + indent_x * 2), btn_size),
    text='TWO PLAYERS', manager=game_types_menu_manager)
three_player_btn = pygame_gui.elements.UIButton(
    relative_rect=pygame.Rect((btn_cords[0], btn_cords[1] + offset + indent_x * 3), btn_size),
    text='THREE PLAYERS', manager=game_types_menu_manager)
game_types_menu_close_btn = pygame_gui.elements.UIButton(
    relative_rect=pygame.Rect((btn_cords[0], btn_cords[1] + indent_x * 5), btn_size),
    text='CLOSE', manager=game_types_menu_manager)

# Init game levels buttons
dict_level_buttons = dict()
level_list = ['1', '2', '3', '4', '5']
level_btn_size = (60, 60)
start_cords = ((WINDOW_WIDTH - (indent_between_buttons + level_btn_size[1]) * len(level_list)) // 2, 200)
btn_level_rect = pygame.Rect(start_cords, level_btn_size)
for btn_lvl in level_list:
    dict_level_buttons[btn_lvl] = \
        pygame_gui.elements.UIButton(
            relative_rect=btn_level_rect, text=btn_lvl, manager=game_level_menu_manager)
    btn_level_rect.x += level_btn_size[0] + indent_between_buttons

survival_mode_btn = pygame_gui.elements.UIButton(
    relative_rect=pygame.Rect((start_cords[0], 300),
                              (btn_level_rect.x - start_cords[0], level_btn_size[1])),
    text='SURVIVAL MODE', manager=game_level_menu_manager)

level_menu_close_btn = pygame_gui.elements.UIButton(
    relative_rect=pygame.Rect((btn_cords[0], btn_cords[1] + indent_x * 5), btn_size),
    text='CLOSE', manager=game_level_menu_manager)


def load_image(name, colorkey=None):
    fullname = os.path.join('data', name)

    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()

    image = pygame.image.load(fullname).convert()

    if colorkey is not None:
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


# Loading game graphics
green_tank_turret = pygame.transform.scale(load_image("green_turret.png", colorkey=-1), (TILE_SIZE, TILE_SIZE))
green_tank_hull = pygame.transform.scale(load_image("green_hull.png", colorkey=-1), (TILE_SIZE, TILE_SIZE))
red_tank_turret = pygame.transform.scale(load_image("red_turret.png", colorkey=-1), (TILE_SIZE, TILE_SIZE))
red_tank_hull = pygame.transform.scale(load_image("red_hull.png", colorkey=-1), (TILE_SIZE, TILE_SIZE))
beast_tank_hull = pygame.transform.scale(load_image("beast_hull.png", colorkey=-1), (TILE_SIZE, TILE_SIZE))
beast_tank_turret = pygame.transform.scale(load_image("beast_turret.png", colorkey=-1), (TILE_SIZE, TILE_SIZE))
heavy_tank_hull = pygame.transform.scale(load_image("heavy_hull.png", colorkey=-1), (TILE_SIZE, TILE_SIZE))
heavy_tank_turret = pygame.transform.scale(load_image("heavy_turret.png", colorkey=-1), (TILE_SIZE, TILE_SIZE))
crash_tank = pygame.transform.scale(load_image("crached_turret.png", colorkey=-1), (TILE_SIZE, TILE_SIZE))
bullet_0 = pygame.transform.scale(load_image("bullet_0.png", colorkey=-1), (TILE_SIZE, TILE_SIZE))

sprites_dict = {'Tank': (red_tank_hull, red_tank_turret),
                'Beast': (beast_tank_hull, beast_tank_turret),
                'Player': (green_tank_hull, green_tank_turret),
                'Heavy': (heavy_tank_hull, heavy_tank_turret)}
normal_bullet_dict = {0: bullet_0}


def get_player_coords():
    return player_coords


def set_custom_settings(*args):
    for elem in args:
        print()


def show_message(screen, message):
    font = pygame.font.Font(None, 50)
    text = font.render(message, True, (50, 70, 0))
    text_w = text.get_width()
    text_h = text.get_height()
    text_x = WINDOW_WIDTH // 2 - text_w // 2
    text_y = WINDOW_HEIGHT // 2 - text_h // 2
    pygame.draw.rect(screen, (200, 150, 50), (text_x - 10, text_y - 10,
                                              text_w + 20, text_h + 20))
    screen.blit(text, (text_x, text_y))


def terminate():
    pygame.quit()
    sys.exit()


class Map:
    def __init__(self, filename):
        self.tiled_map = pytmx.load_pygame(f"{MAPS_DIR}/{filename}")

        self.map = [[self.tiled_map.get_tile_gid(x, y, 0)
                     for x in range(self.tiled_map.width)]
                    for y in range(self.tiled_map.height)]

        self.height = self.tiled_map.height
        self.width = self.tiled_map.width

        self.camera = Camera(self.width, self.height)

        # Инициализация разрушаемых/неразрушаемых/свободных и других блоков через TiledMap
        self.free_tiles = []
        self.break_tiles = []
        self.unbreak_tiles = []

        check_properties = self.tiled_map.get_tile_properties

        for y in range(self.height):
            for x in range(self.width):

                type_of_tile = check_properties(x, y, 0)['type']
                id_of_tile = self.tiled_map.get_tile_gid(x, y, 0)
                if type_of_tile == 'free' and id_of_tile not in self.free_tiles:
                    self.free_tiles.append(id_of_tile)
                elif type_of_tile == 'break' and id_of_tile not in self.break_tiles:
                    self.break_tiles.append(id_of_tile)
                elif type_of_tile == 'unbreak' and id_of_tile not in self.unbreak_tiles:
                    self.unbreak_tiles.append(id_of_tile)

    def render(self, screen):
        for layer in self.tiled_map.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                for x, y, gid in layer:
                    gid = self.map[y][x]

                    tank_stand_on = False
                    # Если на блоке стоит танк, то блок под ним отрисовывается первым свободным из списка
                    if not isinstance(gid, int):
                        gid = self.get_free_block(x, y)
                        tank_stand_on = True

                    tile_image = self.tiled_map.get_tile_image_by_gid(gid)
                    if tile_image:
                        tile_rect = pygame.Rect(0, 0, x * TILE_SIZE, y * TILE_SIZE)
                        # camera move
                        self.camera.apply(tile_rect)
                        # tile render
                        screen.blit(tile_image, (tile_rect.width, tile_rect.height))
                        # tank render
                        if tank_stand_on:
                            screen.blit(self.map[y][x].image, (tile_rect.width, tile_rect.height))
                            screen.blit(self.map[y][x].tank_turret.image, (tile_rect.width, tile_rect.height))

    def get_tile_id(self, position):
        return self.map[position[1]][position[0]]

    def get_type_of_tile(self, x, y):
        check_prop = self.tiled_map.get_tile_properties
        return check_prop(x, y, 0)['type']

    def get_free_block(self, x, y):
        id_of_free_block = self.tiled_map.get_tile_gid(x, y, 0)
        if id_of_free_block not in self.free_tiles:
            id_of_free_block = self.free_tiles[0]
        return id_of_free_block

    def is_free(self, position):
        return self.get_tile_id(position) in self.free_tiles

    def find_player(self):
        for y in range(self.height):
            for x in range(self.width):
                if self.map[y][x].__repr__() == 'Player':
                    return x, y

    def give_tanks_list_and_destinations(self, sprite_group):
        destinations = dict()
        tank_list = list()
        for tile_object in self.tiled_map.objects:
            if tile_object.name != 'Player':
                rotate_turret, rotate_hull = tile_object.properties['rotate_turret'],\
                                             tile_object.properties['rotate_hull']
                destination = tile_object.properties['destination']
                x, y = int(tile_object.x // TILE_SIZE), int(tile_object.y // TILE_SIZE)
                if 'Tank' in tile_object.name:
                    tank_list.append(Tank((x, y), rotate_turret=rotate_turret,
                                          rotate_hull=rotate_hull, group=sprite_group))
                elif 'Beast' in tile_object.name:
                    tank_list.append(Beast((x, y), rotate_turret=rotate_turret,
                                           rotate_hull=rotate_hull, group=sprite_group))
                elif 'Heavy' in tile_object.name:
                    tank_list.append(Heavy((x, y), rotate_turret=rotate_turret,
                                           rotate_hull=rotate_hull, group=sprite_group))
                if destination == 'self':
                    destinations[tank_list[-1]] = (x, y)
                elif destination == 'player':
                    destinations[tank_list[-1]] = get_player_coords

        return tank_list, destinations


class Tank(pygame.sprite.Sprite):
    def __init__(self, position, rotate_turret=0, rotate_hull=0,
                 control_keys=CONTROL_KEYS_V1, group=None, is_player=False):
        super().__init__()

        self.is_player = is_player

        self.speed = 0.20
        self.accuracy = 0.20
        self.health = 1

        self.crash_tank_image_turret = crash_tank
        self.dict_id_bullets = normal_bullet_dict

        # init turret
        self.tank_turret = pygame.sprite.Sprite()
        self.tank_turret.image = sprites_dict[self.__repr__()][1]
        self.tank_turret.rect = self.tank_turret.image.get_rect()
        self.tank_turret.rect.x, self.tank_turret.rect.y = \
            position[0] * TILE_SIZE, position[1] * TILE_SIZE

        # init hull
        self.image = sprites_dict[self.__repr__()][0]
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = \
            position[0] * TILE_SIZE, position[1] * TILE_SIZE

        self.rotate_turret = 0
        self.set_turret_rotate(rotate_turret)
        self.rotate_hull = 0
        self.set_rotate(rotate_hull)
        self.x, self.y = position

        self.group = group
        if self.group is not None:
            self.group.add(self)
            self.group.add(self.tank_turret)

        self.control_keys = control_keys
        self.is_crashed = False

        # timers
        self.shooting_cooldown = 40 * FPS
        self.current_shooting_cooldown = 0

        self.move_forward_cooldown = 8 * FPS
        self.current_move_forward_cooldown = 0

        self.move_back_cooldown = 10 * FPS
        self.current_move_back_cooldown = 0

        self.turn_cooldown = 20 * FPS
        self.current_turn_cooldown = 0

        self.turn_turret_cooldown = 30 * FPS
        self.current_turn_turret_cooldown = 0

    def update_timers(self):
        self.current_shooting_cooldown -= clock.get_time()
        self.current_move_forward_cooldown -= clock.get_time()
        self.current_move_back_cooldown -= clock.get_time()
        self.current_turn_cooldown -= clock.get_time()
        self.current_turn_turret_cooldown -= clock.get_time()

    def get_position(self):
        return self.x, self.y

    def get_rotate(self):
        return self.rotate_turret, self.rotate_hull

    def set_control_keys(self, keys):
        self.control_keys = keys

    def set_position(self, position):
        self.tank_turret.rect.x, self.tank_turret.rect.y = \
            position[0] * TILE_SIZE, position[1] * TILE_SIZE
        self.rect.x, self.rect.y = \
            position[0] * TILE_SIZE, position[1] * TILE_SIZE
        self.x, self.y = position

    def set_turret_rotate(self, rotate):
        self.rotate_turret = (self.rotate_turret + rotate) % 360
        self.tank_turret.image = pygame.transform.rotate(self.tank_turret.image, rotate)

    def set_rotate(self, rotate):
        self.rotate_hull = (self.rotate_hull + rotate) % 360
        self.image = pygame.transform.rotate(self.image, rotate)
        self.set_turret_rotate(rotate)

    def move_forward(self):
        if self.current_move_forward_cooldown <= 0:
            direction_move = [round(i) for i in DIRECTION_MOVE_BY_ANGLE[self.rotate_hull]]
            self.set_position((self.x + direction_move[0], self.y + direction_move[1]))
            self.current_move_forward_cooldown = self.move_forward_cooldown
            return True
        return False

    def move_back(self):
        if self.current_move_back_cooldown <= 0:
            direction_move = [round(i) for i in DIRECTION_MOVE_BY_ANGLE[self.rotate_hull]]
            self.set_position((self.x - direction_move[0], self.y - direction_move[1]))
            self.current_move_back_cooldown = self.move_back_cooldown
            return True
        return False

    def turn_right(self):
        if self.current_turn_cooldown <= 0:
            self.set_rotate(270)
            self.current_turn_cooldown = self.turn_cooldown
            return True
        return False

    def turn_left(self):
        if self.current_turn_cooldown <= 0:
            self.set_rotate(90)
            self.current_turn_cooldown = self.turn_cooldown
            return True
        return False

    def turn_turret_right(self):
        if self.current_turn_turret_cooldown <= 0:
            self.set_turret_rotate(270)
            self.current_turn_turret_cooldown = self.turn_turret_cooldown
            return True
        return False

    def turn_turret_left(self):
        if self.current_turn_turret_cooldown <= 0:
            self.set_turret_rotate(90)
            self.current_turn_turret_cooldown = self.turn_turret_cooldown
            return True
        return False

    def shoot(self, bullets_list):
        if self.current_shooting_cooldown <= 0:
            bullets_list.append(Bullet(
                self.get_position(), self.rotate_turret, self.dict_id_bullets[0]))
            self.current_shooting_cooldown = self.shooting_cooldown
            return True
        return False

    def destroy_the_tank(self, another_group):
        self.is_crashed = True
        self.tank_turret.image = pygame.transform.rotate(
            self.crash_tank_image_turret, self.get_rotate()[1])
        if not self.is_player:
            another_group.remove(self)

    def clear_the_tank(self):
        self.group.remove(self)
        self.group.remove(self.tank_turret)

    def __repr__(self):
        if self.is_player:
            return 'Player'
        else:
            return 'Tank'


class Beast(Tank):
    def __init__(self, position, rotate_turret=0, rotate_hull=0, control_keys=CONTROL_KEYS_V1,
                 group=None, is_player=False):
        super().__init__(position, rotate_turret, rotate_hull, control_keys, group, is_player)
        self.speed = 0.666
        self.accuracy = 0.333

    def __repr__(self):
        return 'Beast'


class Heavy(Tank):
    def __init__(self, position, rotate_turret=0, rotate_hull=0, control_keys=CONTROL_KEYS_V1,
                 group=None, is_player=False):
        super().__init__(position, rotate_turret, rotate_hull, control_keys, group, is_player)
        self.speed = 0.10
        self.accuracy = 0.40
        self.health = 2

    def __repr__(self):
        return 'Heavy'


class Bullet(pygame.sprite.Sprite):
    def __init__(self, position, rotate, image):
        super().__init__()
        self.x, self.y = position
        self.direction_move = DIRECTION_MOVE_BY_ANGLE[rotate]

        self.image = pygame.transform.rotate(image, rotate)
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = \
            position[0] * TILE_SIZE, position[1] * TILE_SIZE

        self.group = pygame.sprite.Group()
        self.group.add(self)

    def get_position(self):
        return self.x, self.y

    def get_direction_move(self):
        return self.direction_move

    def set_position(self, position):
        self.x, self.y = position

    def next_move(self):
        self.x += self.direction_move[0]
        self.y += self.direction_move[1]
        self.rect.x, self.rect.y = \
            self.x * TILE_SIZE, self.y * TILE_SIZE

    def render(self, surface):
        self.group.draw(surface)


class Game:
    def __init__(self, map, controlled_tanks, bullets, sprites_group=list()):
        self.map = map

        self.camera = self.map.camera

        # Инициализация миссий и "причин для поражения"
        self.defeat_reasons = []
        self.missions = []

        # Группы танков
        self.sprites_group = sprites_group
        self.controlled_tanks = controlled_tanks
        self.uncontrolled_tanks, self.destinations = \
            (self.map.give_tanks_list_and_destinations(sprites_group[0]))

        self.bullets = bullets

        self.end_count = 0

    def render(self, screen):
        self.map.camera = self.camera

        self.map.render(screen)

        self.update_bullets()
        for bullet in self.bullets:
            self.camera.apply(bullet)
            bullet.render(screen)

    def update_bullets(self):
        for bullet in self.bullets:
            bullet.next_move()
            bullet_x, bullet_y = [round(i) for i in bullet.get_position()]
            if not self.map.is_free((bullet_x, bullet_y)):
                if self.map.get_type_of_tile(bullet_x, bullet_y) != 'water':
                    del self.bullets[self.bullets.index(bullet)]
                    if isinstance(self.map.map[bullet_y][bullet_x], Tank):
                        tank = self.map.map[bullet_y][bullet_x]
                        tank.health -= 1
                        if tank.health <= 0:
                            if tank.is_crashed:
                                self.map.map[bullet_y][bullet_x] = self.map.get_free_block(bullet_x, bullet_y)
                                tank.clear_the_tank()
                            else:
                                tank.destroy_the_tank(self.uncontrolled_tanks)
                    elif self.map.map[bullet_y][bullet_x] in self.map.break_tiles:
                        self.map.map[bullet_y][bullet_x] = self.map.get_free_block(bullet_x, bullet_y)
                    elif self.map.get_type_of_tile(bullet_x, bullet_y) == 'tnt':
                        self.map.map[bullet_y][bullet_x] = self.map.get_free_block(bullet_x, bullet_y)
                        for angle in range(0, 271, 90):
                            self.bullets.append(Bullet((
                                bullet_x, bullet_y), angle, self.controlled_tanks[0].dict_id_bullets[0]))

    def update_controlled_tanks(self):
        for tank in self.controlled_tanks:
            tank.update_timers()
            if tank.is_crashed:
                continue

            cur_x, cur_y = tank.get_position()
            rotate_turret, rotate_hull = tank.get_rotate()
            dx, dy = DIRECTION_MOVE_BY_ANGLE[rotate_hull]
            self.map.map[cur_y][cur_x] = tank

            if pygame.key.get_pressed()[tank.control_keys[FORWARD]]:
                next_x, next_y = cur_x + dx, cur_y + dy
                if self.map.is_free((next_x, next_y)):
                    if tank.move_forward():
                        self.map.map[cur_y][cur_x] = self.map.get_free_block(cur_x, cur_y)
                        self.map.map[next_y][next_x] = tank
            elif pygame.key.get_pressed()[tank.control_keys[BACK]]:
                next_x, next_y = cur_x + dx, cur_y + dy
                if self.map.is_free((next_x, next_y)):
                    if tank.move_back():
                        self.map.map[cur_y][cur_x] = self.map.get_free_block(cur_x, cur_y)
                        self.map.map[next_y][next_x] = tank
            if pygame.key.get_pressed()[tank.control_keys[TURN_RIGHT]]:
                tank.turn_right()
            elif pygame.key.get_pressed()[tank.control_keys[TURN_LEFT]]:
                tank.turn_left()
            if pygame.key.get_pressed()[tank.control_keys[TURN_RIGHT_TURRET]]:
                tank.turn_turret_right()
            elif pygame.key.get_pressed()[tank.control_keys[TURN_LEFT_TURRET]]:
                tank.turn_turret_left()
            elif pygame.key.get_pressed()[tank.control_keys[SHOOT]]:
                tank.shoot(self.bullets)

            self.camera.update(tank)
            self.camera.apply(tank)
            self.map.camera = self.camera
            global player_coords
            player_coords = tank.get_position()

    def update_uncontrolled_tanks(self):
        for tank in self.uncontrolled_tanks:
            tank.update_timers()
            if tank.is_crashed:
                continue

            destination = self.destinations[tank]
            # Для динамических целей, которые требуют обновления данных о себе
            if callable(destination):
                destination = destination()
            # нахождение цели
            path, status = self.find_path(tank.get_position(), destination)

            # Поскольку бот соображает слишком быстро, задержка через рандом должна снизить его скорость
            if random() > 1 - tank.accuracy:
                self.calculate_uncontrolled_tank_turret(tank)

            if random() > 1 - tank.speed:
                if len(path) > 3 and destination != None:
                    self.calculate_uncontrolled_tank_move(path, destination, tank)
            else:
                x, y = tank.get_position()
                self.map.map[y][x] = tank

    def calculate_uncontrolled_tank_turret(self, tank):
        cur_x, cur_y = tank.get_position()
        rotate_turret = tank.get_rotate()[0]
        row_cells = self.map.map[cur_y].copy()

        down_y_axis = [self.map.map[y][cur_x] for y in range(cur_y, len(self.map.map))]
        up_y_axis = [self.map.map[y][cur_x] for y in range(cur_y, 0, -1)]
        left_x_axis = [self.map.map[cur_y][x] for x in range(cur_x, 0, -1)]
        right_x_axis = [self.map.map[cur_y][x] for x in range(cur_x, len(self.map.map[0]))]
        for cell in left_x_axis:  # 90
            if cell in self.map.unbreak_tiles:
                if 'Player' in left_x_axis:
                    print('left', left_x_axis)
                break
            if isinstance(cell, Tank) and cell in self.controlled_tanks:
                if rotate_turret == 90:
                    tank.shoot(self.bullets)
                elif rotate_turret == 0:
                    tank.turn_turret_left()
                elif rotate_turret == 90:
                    tank.turn_turret_right()
                elif rotate_turret == 180:
                    tank.turn_turret_right()
                return None
        for cell in right_x_axis:  # 270
            if cell in self.map.unbreak_tiles:
                if 'Player' in right_x_axis:
                    print('right', right_x_axis)
                break
            if isinstance(cell, Tank) and cell in self.controlled_tanks:
                if rotate_turret == 270:
                    tank.shoot(self.bullets)
                elif rotate_turret == 0:
                    tank.turn_turret_right()
                elif rotate_turret == 270:
                    tank.turn_turret_right()
                elif rotate_turret == 180:
                    tank.turn_turret_left()
                return None
        for cell in up_y_axis:  # 0
            if cell in self.map.unbreak_tiles:
                if 'Player' in up_y_axis:
                    print('up', up_y_axis)
                break
            if isinstance(cell, Tank) and cell in self.controlled_tanks:
                if rotate_turret == 0:
                    tank.shoot(self.bullets)
                elif rotate_turret == 90:
                    tank.turn_turret_right()
                elif rotate_turret == 270:
                    tank.turn_turret_left()
                elif rotate_turret == 180:
                    tank.turn_turret_right()
                return None
        for cell in down_y_axis:  # 180
            if cell in self.map.unbreak_tiles:
                if 'Player' in down_y_axis:
                    print('up', down_y_axis)
                break
            if isinstance(cell, Tank) and cell in self.controlled_tanks:
                if rotate_turret == 180:
                    tank.shoot(self.bullets)
                elif rotate_turret == 0:
                    tank.turn_turret_left()
                elif rotate_turret == 270:
                    tank.turn_turret_right()
                elif rotate_turret == 90:
                    tank.turn_turret_left()
                return None

    def calculate_uncontrolled_tank_move(self, path, destination, tank):
        cur_x, cur_y = tank.get_position()
        rotate_hull = tank.get_rotate()[1]
        next_step = path[2]
        direction_move = self.calculate_direction(tank.get_position(), next_step)
        next_x = cur_x + direction_move[0]
        next_y = cur_y + direction_move[1]
        if direction_move == (0, 1):
            if rotate_hull == 180:
                if tank.move_forward():
                    self.map.map[cur_y][cur_x] = self.map.get_free_block(cur_x, cur_y)
                    self.map.map[next_y][next_x] = tank
            else:
                tank.turn_left()
        if direction_move == (1, 0):
            if rotate_hull == 270:
                if tank.move_forward():
                    self.map.map[cur_y][cur_x] = self.map.get_free_block(cur_x, cur_y)
                    self.map.map[next_y][next_x] = tank
            else:
                tank.turn_right()
        if direction_move == (0, -1):
            if rotate_hull == 0:
                if tank.move_forward():
                    self.map.map[cur_y][cur_x] = self.map.get_free_block(cur_x, cur_y)
                    self.map.map[next_y][next_x] = tank
            else:
                tank.turn_right()
        if direction_move == (-1, 0):
            if rotate_hull == 90:
                if tank.move_forward():
                    self.map.map[cur_y][cur_x] = self.map.get_free_block(cur_x, cur_y)
                    self.map.map[next_y][next_x] = tank
            else:
                tank.turn_left()

    def calculate_direction(self, this_step, next_step):
        return tuple(next_step[i] - this_step[i] for i in range(len(this_step)))

    def find_path(self, start, destination):
        if start == destination:
            return [start, start, start, start], 'complete'
        status = 'full'
        # создаем граф, используя соседние клетки
        graph = {}
        for y, row in enumerate(self.map.map):
            for x, column in enumerate(row):
                graph[(x, y)] = graph.get((x, y), []) + self.check_neighbour(x, y, start)

        queue = Queue()
        queue.put(start)
        came_from = {}
        came_from[start] = None

        # для каждой клетки в очереди записывается клетка, из которой они пришли
        while not queue.empty():
            current_cell = queue.get()
            cells = graph[current_cell]
            for cell in cells:
                # если графа нет в "откуда пришел", то добавляем ему точку, откуда он пришел, и кидаем в очередь
                if cell not in came_from:
                    queue.put(cell)
                    came_from[cell] = current_cell
        # идем обратно от конца до старта
        current_cell = destination
        path = [destination]
        while current_cell != start:
            # если у точки дислокации нет точки, откуда она пришла. Такое бывает, если старт окружают заборы
            if current_cell not in came_from:
                status = 'incomplete'
                segment_of_broken_path = -1
                while current_cell not in came_from:
                    current_cell = list(came_from.keys())[segment_of_broken_path]
                    segment_of_broken_path -= 1

            current_cell = came_from[current_cell]
            path.append(current_cell)
        path.append(start)
        path.reverse()
        return path, status

    def check_neighbour(self, x, y, pathfinder_coords):
        cells_list = [(x, y)]
        is_next_neighbor = lambda p1, p2: True if all([(0 <= p2 < len(self.map.map)),
                                                       (0 <= p1 < len(self.map.map[0]))]) else False
        while True:
            cells_list_copy = cells_list.copy()
            cells_list = []
            for coords in cells_list_copy:
                x, y = coords
                if is_next_neighbor(*coords):
                    for y_step in (y - 1, y, y + 1):
                        if y_step == y:
                            x_list = (x - 1, x + 1)
                        else:
                            x_list = (x, x)
                        for x_step in x_list:
                            if is_next_neighbor(x_step, y_step):
                                neighbour_cell = self.map.map[y_step][x_step]
                                if (self.map.is_free((x_step, y_step)) or
                                    (isinstance(neighbour_cell, Tank) and neighbour_cell in self.controlled_tanks))\
                                        and (x_step, y_step) != pathfinder_coords:
                                    cells_list.append((x_step, y_step))
            return cells_list

    def end_game_and_return_status(self, screen):
        results = [reason() for reason in self.defeat_reasons]
        if any(results):
            show_message(screen, 'Вы проиграли.')
            self.end_count += 1
            return 'lose'
        results = [mission() for mission in self.missions]
        if any(results):
            show_message(screen, 'Победа!')
            self.end_count += 1
            return 'win'


class Camera:
    # зададим начальный сдвиг камеры
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.rect = pygame.Rect(0, 0, self.width, self.height)

    # сдвинуть объект obj на смещение камеры
    def apply(self, obj):
        if isinstance(obj, Bullet):
            obj.rect.x += self.rect.left
            obj.rect.y += self.rect.top
        if isinstance(obj, Tank):
            pass
        elif isinstance(obj, pygame.Rect):
            obj.width += self.rect.left
            obj.height += self.rect.top

    # позиционировать камеру на объекте target
    def update(self, target):
        # dx = -(target.rect.x + target.rect.w // 2 - self.width // 2)
        dx = -(target.x * TILE_SIZE - (3 * TILE_SIZE))
        dy = -(target.y * TILE_SIZE - (3 * TILE_SIZE))

        # ограничения камеры, чтобы она не показала черных границы
        if abs(dx) >= (self.width - 14) * TILE_SIZE:
            dx = self.rect.x
        if dx > 0:
            dx = 0

        if abs(dy) >= (self.height - 14) * TILE_SIZE:
            dy = self.rect.y
        if dy > 0:
            dy = 0
        self.rect = pygame.Rect(dx, dy, self.width, self.height)


def show_settings_menu():
    def draw_background():
        draw_the_main_background()
        draw_the_dialog_background('SETTINGS')

    is_open_a_conf_dialog = False
    draw_background()
    while True:
        time_delta = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if not is_open_a_conf_dialog:
                    show_confirmation_dialog(settings_menu_manager)
                    is_open_a_conf_dialog = True
            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_CONFIRMATION_DIALOG_CONFIRMED:
                    terminate()
                if event.user_type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
                    print(event.text)
                if event.user_type == pygame_gui.UI_BUTTON_ON_HOVERED:
                    print('Наведение на кнопку')
                    # return  # начинаем игру
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    is_open_a_conf_dialog = False
                    print('g')
                    if event.ui_element == settings_close_btn:
                        print('g')
                        return
                    draw_background()
            settings_menu_manager.process_events(event)
            general_manager.process_events(event)
        settings_menu_manager.update(time_delta)
        general_manager.update(time_delta)

        if is_open_a_conf_dialog:
            draw_background()

        settings_menu_manager.draw_ui(screen)
        general_manager.draw_ui(screen)

        pygame.display.flip()
        clock.tick(FPS)


def show_highscore_board():
    # init fon
    fon = pygame.Surface((WINDOW_WIDTH * 0.7, WINDOW_HEIGHT * 0.7))
    fon.fill(pygame.Color((255, 0, 0)))
    screen.blit(fon, ((WINDOW_WIDTH - fon.get_width()) // 2,
                      (WINDOW_HEIGHT - fon.get_height()) // 2))

    draw_the_dialog_background('РЕКОРДЫ')
    draw_the_dialog_background('В РАЗРАБОТКЕ...', y=250)
    draw_the_dialog_background('press button', y=480)


def show_info_menu():
    # init fon
    fon = pygame.Surface((WINDOW_WIDTH * 0.7, WINDOW_HEIGHT * 0.7))
    fon.fill(pygame.Color((0, 255, 0)))
    screen.blit(fon, ((WINDOW_WIDTH - fon.get_width()) // 2,
                      (WINDOW_HEIGHT - fon.get_height()) // 2))

    draw_the_dialog_background('КАК ИГРАТЬ')
    draw_the_dialog_background('В РАЗРАБОТКЕ...', y=250)
    draw_the_dialog_background('press button', y=480)


def show_the_game_menu():
    def draw_sign_name_type_game():
        text_size0 = 20
        font = pygame.font.Font(f'{FONTS_DIR}/Unicephalon.otf', text_size0)
        text1 = font.render('PLAYING WITH BOTS', True, COLOR_TEXT)
        text2 = font.render('PLAYING WITH PLAYERS', True, COLOR_TEXT)
        screen.blit(text1, (
            (WINDOW_WIDTH - text1.get_width()) // 2, btn_cords[1]))
        screen.blit(text2, (
            (WINDOW_WIDTH - text2.get_width()) // 2, btn_cords[1] + indent_x * 2))

    def draw_background():
        draw_the_main_background()
        draw_the_dialog_background('GAME MENU')
        draw_sign_name_type_game()

    is_open_a_conf_dialog = False
    draw_background()
    while True:
        time_delta = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if not is_open_a_conf_dialog:
                    show_confirmation_dialog(game_types_menu_manager)
                    is_open_a_conf_dialog = True
            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_CONFIRMATION_DIALOG_CONFIRMED:
                    terminate()
                if event.user_type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
                    print(event.text)
                if event.user_type == pygame_gui.UI_BUTTON_ON_HOVERED:
                    print('Наведение на кнопку')
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    is_open_a_conf_dialog = False
                    if event.ui_element == game_types_menu_close_btn:
                        return
                    elif event.ui_element == single_player_btn:
                        show_the_level_list()
                        draw_background()
                    elif event.ui_element == two_player_btn:
                        pass
                    elif event.ui_element == three_player_btn:
                        pass
                    draw_background()
            game_types_menu_manager.process_events(event)
            general_manager.process_events(event)
        game_types_menu_manager.update(time_delta)
        general_manager.update(time_delta)

        if is_open_a_conf_dialog:
            draw_background()

        game_types_menu_manager.draw_ui(screen)
        general_manager.draw_ui(screen)

        pygame.display.flip()
        clock.tick(FPS)


def show_the_level_list():
    global lvl_count_id
    def draw_background():
        draw_the_main_background()
        draw_the_dialog_background('LEVELS:')

    is_open_a_conf_dialog = False
    draw_background()
    while True:
        time_delta = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if not is_open_a_conf_dialog:
                    show_confirmation_dialog(game_level_menu_manager)
                    is_open_a_conf_dialog = True
            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_CONFIRMATION_DIALOG_CONFIRMED:
                    terminate()
                if event.user_type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
                    print(event.text)
                if event.user_type == pygame_gui.UI_BUTTON_ON_HOVERED:
                    print('Наведение на кнопку')
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    is_open_a_conf_dialog = False
                    if event.ui_element == level_menu_close_btn:
                        return
                    elif event.ui_element == survival_mode_btn:
                        pass
                    elif event.ui_element == dict_level_buttons['1']:
                        lvl_count_id = 1
                    elif event.ui_element == dict_level_buttons['2']:
                        lvl_count_id = 2
                    elif event.ui_element == dict_level_buttons['3']:
                        lvl_count_id = 3
                    elif event.ui_element == dict_level_buttons['4']:
                        lvl_count_id = 4
                    elif event.ui_element == dict_level_buttons['5']:
                        lvl_count_id = 5
                    draw_background()
            game_level_menu_manager.process_events(event)
            general_manager.process_events(event)
        game_level_menu_manager.update(time_delta)
        general_manager.update(time_delta)

        if is_open_a_conf_dialog:
            draw_background()

        game_level_menu_manager.draw_ui(screen)
        general_manager.draw_ui(screen)

        pygame.display.flip()
        clock.tick(FPS)


def draw_the_dialog_background(message, y=150):
    # init title
    font = pygame.font.Font(f'{FONTS_DIR}/Unicephalon.otf', 20)
    text = font.render(message, True, COLOR_TEXT)
    text_x = (WINDOW_WIDTH - text.get_width()) // 2
    text_y = y
    screen.blit(text, (text_x, text_y))


def draw_the_main_background():
    # init fon
    fon = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
    fon.fill(pygame.Color((0, 0, 0)))
    screen.blit(fon, (0, 0))

    # init title
    font = pygame.font.Font(f'{FONTS_DIR}/Unicephalon.otf', 60)
    text = font.render(TITLE, True, COLOR_TEXT)
    text_x = WINDOW_WIDTH // 2 - text.get_width() // 2
    text_y = round(WINDOW_HEIGHT * 0.1)
    screen.blit(text, (text_x, text_y))


def show_confirmation_dialog(manager):
    dialog_size = (260, 200)
    confirmation_dialog = pygame_gui.windows.UIConfirmationDialog(
        rect=pygame.Rect(
            ((WINDOW_WIDTH - dialog_size[0]) // 2,
             (WINDOW_HEIGHT - dialog_size[1]) // 2),
            dialog_size),
        manager=manager,
        window_title='Подтвеждение',
        action_long_desc='Вы уверены, что хотите вытйти?',
        action_short_name='OK',
        blocking=True)
    return confirmation_dialog


def start_screen():
    def draw_sign_name_entry_line():
        text_size0 = 20
        font0 = pygame.font.Font(f'{FONTS_DIR}/Unicephalon.otf', text_size0)
        name_entry_text = font0.render('ВАШЕ ИМЯ:', True, COLOR_TEXT)
        screen.blit(name_entry_text, (round(WINDOW_WIDTH * 0.085), 522))

    def draw_background():
        draw_the_main_background()
        draw_sign_name_entry_line()

    draw_background()
    is_open_a_conf_dialog = False
    do_show_info = False
    do_show_scores = False
    while True:
        time_delta = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if not is_open_a_conf_dialog:
                    show_confirmation_dialog(main_menu_manager)
                    is_open_a_conf_dialog = True
            if event.type == pygame.KEYDOWN or \
                    event.type == pygame.MOUSEBUTTONDOWN:
                do_show_info = False
                do_show_scores = False
                draw_background()
            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_CONFIRMATION_DIALOG_CONFIRMED:
                    terminate()  # exit
                if event.user_type == pygame_gui.UI_TEXT_ENTRY_FINISHED:
                    print(event.text)
                if event.user_type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
                    print(event.text)
                if event.user_type == pygame_gui.UI_BUTTON_ON_HOVERED:
                    pass
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    is_open_a_conf_dialog = False
                    if event.ui_element == dict_menu_buttons['ПРОДОЛЖИТЬ']:  # Continue
                        return  # start game
                    elif event.ui_element == dict_menu_buttons['ИГРАТЬ ЛОКАЛЬНО']:  # Play local
                        show_the_game_menu()
                        draw_background()
                    elif event.ui_element == dict_menu_buttons['РЕКОРДЫ']:  # Highscore board
                        do_show_scores = True
                    elif event.ui_element == dict_menu_buttons['КАК ИГРАТЬ']:  # How to play
                        do_show_info = True
                    elif event.ui_element == dict_menu_buttons['НАСТРОЙКИ']:  # Settings
                        show_settings_menu()
                        draw_background()
                    elif event.ui_element == dict_menu_buttons['ВЫЙТИ']:  # Exit
                        if not is_open_a_conf_dialog:
                            show_confirmation_dialog(main_menu_manager)
                            is_open_a_conf_dialog = True

            main_menu_manager.process_events(event)
            general_manager.process_events(event)
        main_menu_manager.update(time_delta)
        general_manager.update(time_delta)

        if is_open_a_conf_dialog:
            draw_background()

        main_menu_manager.draw_ui(screen)
        general_manager.draw_ui(screen)

        if do_show_scores:
            show_highscore_board()
        if do_show_info:
            show_info_menu()

        pygame.display.flip()
        clock.tick(FPS)


class LevelLoader:
    def init_lvl1_scene(self):
        # Формирование кадра(команды рисования на холсте):
        main_map = Map("1_lvl.tmx")
        all_sprites = pygame.sprite.Group()  # создадим группу, содержащую все спрайты

        controlled_tanks = [
            Tank((7, 1), rotate_turret=0, rotate_hull=180, group=all_sprites,
                 control_keys=CONTROL_KEYS_V1, is_player=True)]

        bullets = []
        game = Game(main_map, controlled_tanks, bullets, sprites_group=[all_sprites])

        game.missions = [lambda: len(game.uncontrolled_tanks) == 0]
        game.defeat_reasons = [lambda: game.controlled_tanks[0].is_crashed]

        return game

    def init_lvl2_scene(self):
        # Формирование кадра(команды рисования на холсте):
        main_map = Map("2_lvl.tmx")
        all_sprites = pygame.sprite.Group()  # создадим группу, содержащую все спрайты

        controlled_tanks = [
            Tank((1, 1), rotate_turret=0, rotate_hull=180, group=all_sprites,
                 control_keys=CONTROL_KEYS_V1, is_player=True)]

        bullets = []

        game = Game(main_map, controlled_tanks, bullets, sprites_group=[all_sprites])

        stand_on_control_point = lambda: game.map.get_type_of_tile(
            get_player_coords()[0], get_player_coords()[1]) == 'free_control_point'

        game.missions = [stand_on_control_point]
        game.defeat_reasons = [lambda: game.controlled_tanks[0].is_crashed]

        return game

    def init_lvl3_scene(self):
        # Формирование кадра(команды рисования на холсте):
        main_map = Map("3_lvl.tmx")
        all_sprites = pygame.sprite.Group()  # создадим группу, содержащую все спрайты

        controlled_tanks = [
            Tank((7, 7), rotate_turret=0, rotate_hull=180, group=all_sprites,
                 control_keys=CONTROL_KEYS_V1, is_player=True)]

        bullets = []

        game = Game(main_map, controlled_tanks, bullets, sprites_group=[all_sprites])

        game.missions = [lambda: len(game.uncontrolled_tanks) == 0]
        game.defeat_reasons = [lambda: game.controlled_tanks[0].is_crashed]

        return game

    def init_lvl4_scene(self):
        # Формирование кадра(команды рисования на холсте):
        main_map = Map("4_lvl.tmx")
        all_sprites = pygame.sprite.Group()  # создадим группу, содержащую все спрайты

        controlled_tanks = [
            Tank((1, 1), rotate_turret=0, rotate_hull=180, group=all_sprites,
                 control_keys=CONTROL_KEYS_V1, is_player=True)]

        bullets = []

        game = Game(main_map, controlled_tanks, bullets, sprites_group=[all_sprites])

        game.missions = [lambda: len(game.uncontrolled_tanks) == 0]
        game.defeat_reasons = [lambda: game.controlled_tanks[0].is_crashed]

        return game

    def init_lvl5_scene(self):
        # Формирование кадра(команды рисования на холсте):
        main_map = Map("5_lvl.tmx")
        all_sprites = pygame.sprite.Group()  # создадим группу, содержащую все спрайты

        controlled_tanks = [
            Tank((1, 1), rotate_turret=0, rotate_hull=180, group=all_sprites,
                 control_keys=CONTROL_KEYS_V1, is_player=True)]

        bullets = []

        game = Game(main_map, controlled_tanks, bullets, sprites_group=[all_sprites])

        stand_on_control_point = lambda: game.map.get_type_of_tile(
            get_player_coords()[0], get_player_coords()[1]) == 'free_control_point'

        game.missions = [lambda: len(game.uncontrolled_tanks) == 0, stand_on_control_point]
        game.defeat_reasons = [lambda: game.controlled_tanks[0].is_crashed]

        return game


def main():
    lvl_count = 5
    lvl_loader = LevelLoader()
    game = getattr(lvl_loader, f'init_lvl{lvl_count}_scene')()

    # Главный игровой цикл:
    running = True
    start_screen()
    while running:
        # Цикл приема и обработки сообщений:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:

                # if event.key == pygame.K_SPACE:
                #     lvl_count += 1
                #     if lvl_count > 5:
                #         lvl_count = 0
                #     game = getattr(lvl_loader, f'init_lvl{lvl_count}_scene')

                # Features for testing:
                if event.key == pygame.K_h:
                    game.controlled_tanks[0].health = 999
                elif event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5]:
                    lvl_count = event.unicode
                    game = getattr(lvl_loader, f'init_lvl{lvl_count}_scene')()

        # if game.end_count == 5:
        #     pygame.time.delay(3000)
        #     if game.end_game_and_return_status(screen) == 'win':
        #         lvl_count += 1
        #     game = getattr(lvl_loader, f'init_lvl{lvl_count}_scene')()

        game.render(screen)
        game.update_controlled_tanks()
        game.update_uncontrolled_tanks()
        # game.end_game_and_return_status(screen)

        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()


if __name__ == "__main__":
    main()
