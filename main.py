import os
import sys
import datetime as dt
from random import random
from queue import Queue
import pygame
import pygame_gui
import pytmx
import pickle


WINDOW_SIZE = WINDOW_WIDTH, WINDOW_HEIGHT = 600, 600
TITLE = 'TANK BATTLES'
TILE_SIZE = 40
FPS = 40
MAPS_DIR = 'data/maps'
FONTS_DIR = 'data/fonts'
GUI_THEMES_DIR = 'data/gui themes'
SAVED_SESSION_DIR = 'data/saved sessions'
SAVED_USER_INFO_DIR = 'data/saved user info'

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

player_coords = (0, 0)
user_info = {'sound_value': 100,
             'music_value': 100,
             'name': 'user_name',
             'high_scores': [('-', 0) for _ in range(10)]}

main_menu_manager = pygame_gui.UIManager(
    WINDOW_SIZE, f'{GUI_THEMES_DIR}/start_manu_theme.json')
game_pause_manager = pygame_gui.UIManager(WINDOW_SIZE)
game_process_manager = pygame_gui.UIManager(WINDOW_SIZE)

# Init main menu title text
title_size = 80
title_font = pygame.font.Font(f'{FONTS_DIR}/Pixel Georgia.ttf', title_size)
title_font.bold = 1
title_text = [title_font.render(text, True, COLOR_TEXT) for text in TITLE.split()]
title_text_height = sum([text.get_height() for text in title_text])
title_text_y = 120

# Init set name menu elements
label_btn_size = (45, 26)
entry_line_size = (150, 40)
label = pygame_gui.elements.ui_label.UILabel(
    relative_rect=pygame.Rect((
        (WINDOW_WIDTH - label_btn_size[0] - entry_line_size[0]) // 2,
        title_text_y + title_text_height), label_btn_size),
    text='NAME',
    manager=main_menu_manager)
name_entry_line = pygame_gui.elements.UITextEntryLine(
    relative_rect=pygame.Rect((
        (WINDOW_WIDTH + label_btn_size[0] - entry_line_size[0]) // 2,
        title_text_y + title_text_height), entry_line_size),
    manager=main_menu_manager)
name_entry_line.set_text_length_limit(15)

# Init main menu buttons
start_menu_buttons_intro = ['CONTINUE',
                            'NEW GAME',
                            'HIGH SCORES',
                            'HOW TO PLAY',
                            'EXIT']
btn_size = (180, 41)
indent_down = WINDOW_HEIGHT - 20
indent_top = title_text_y + title_text_height + label.rect.height
indent_left = 40
indent_right = WINDOW_WIDTH - 40

btn_x = (WINDOW_WIDTH - btn_size[0]) // 2
btn_y = (WINDOW_HEIGHT + indent_top - (btn_size[1]) * 5) // 2
btn_rect = pygame.Rect((btn_x, btn_y), btn_size)
start_menu_btn_dict = dict()
for btn_text in start_menu_buttons_intro:
    start_menu_btn_dict[btn_text] = pygame_gui.elements.UIButton(
        relative_rect=btn_rect, text=btn_text, manager=main_menu_manager)
    btn_rect.y += btn_size[1]

# Init sound buttons
sound_btn_size = (40, 40)
sound_slider_size = (130, 30)
sound_btn = pygame_gui.elements.UIButton(
    relative_rect=pygame.Rect((indent_left, indent_down - sound_btn_size[1]), sound_btn_size),
    text='', manager=main_menu_manager)
sound_value_slider = pygame_gui.elements.ui_horizontal_slider.UIHorizontalSlider(
    relative_rect=pygame.Rect((
        indent_left + 5 + sound_btn_size[0],
        sound_btn.rect.y + 5), sound_slider_size),
    value_range=(0, 100),
    start_value=100,
    manager=main_menu_manager)
music_btn = pygame_gui.elements.UIButton(
    relative_rect=pygame.Rect((
        indent_right - sound_btn_size[0],
        indent_down - sound_btn_size[1]), sound_btn_size),
    text='', manager=main_menu_manager)
music_value_slider = pygame_gui.elements.ui_horizontal_slider.UIHorizontalSlider(
    relative_rect=pygame.Rect((
        indent_right - 5 - sound_btn_size[0] - sound_slider_size[0],
        sound_btn.rect.y + 5), sound_slider_size),
    value_range=(0, 100),
    start_value=100,
    manager=main_menu_manager)


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

music_on_img = pygame.transform.scale(load_image("music_on.png"), sound_btn_size)
sound_on_img = pygame.transform.scale(load_image("sound_on.png"), sound_btn_size)
music_off_img = pygame.transform.scale(load_image("music_off.png"), sound_btn_size)
sound_off_img = pygame.transform.scale(load_image("sound_off.png"), sound_btn_size)

sprites_dict = {'Tank': (red_tank_hull, red_tank_turret),
                'Beast': (beast_tank_hull, beast_tank_turret),
                'Player': (green_tank_hull, green_tank_turret),
                'Heavy': (heavy_tank_hull, heavy_tank_turret)}
normal_bullet_dict = {0: bullet_0}


def get_player_coords():
    return player_coords


def terminate():
    pygame.quit()
    sys.exit()


def save_user_info():
    with open(f'{SAVED_USER_INFO_DIR}/save.dat', 'wb') as file:
        pickle.dump({'name': name_entry_line.text,
                     'sound_value': sound_value_slider.current_value,
                     'music_value': music_value_slider.current_value,
                     'high_scores': user_info['high_scores']}, file)


def load_user_info():
    global user_info
    with open(f'{SAVED_USER_INFO_DIR}/save.dat', 'rb') as file:
        user_info = pickle.load(file)
    name_entry_line.set_text(user_info['name'])
    sound_value_slider.set_current_value(user_info['sound_value'])
    music_value_slider.set_current_value(user_info['music_value'])


def save_game(game):
    with open(f'{SAVED_SESSION_DIR}/save.dat', 'wb') as file:
        pickle.dump(game, file)


def load_saved_game():
    with open(f'{SAVED_SESSION_DIR}/save.dat', 'rb') as file:
        game = pickle.load(file)
    return game


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
            show_game_message(screen, 'YOU LOST!', 'press button to continue')
            self.end_count += 1
            return 'lose'
        results = [mission() for mission in self.missions]
        if any(results):
            show_game_message(screen, 'YOU WON!', 'press button to continue')
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


def show_highscore_board():
    def draw_the_dialog_background(message, y=150):
        # init title
        font = pygame.font.Font(f'{FONTS_DIR}/Unicephalon.otf', 20)
        text = font.render(message, True, COLOR_TEXT)
        text_x = (WINDOW_WIDTH - text.get_width()) // 2
        text_y = y
        screen.blit(text, (text_x, text_y))

    # init fon
    fon = pygame.Surface((WINDOW_WIDTH * 0.7, WINDOW_HEIGHT * 0.7))
    fon.fill(pygame.Color((255, 0, 0)))
    screen.blit(fon, ((WINDOW_WIDTH - fon.get_width()) // 2,
                      (WINDOW_HEIGHT - fon.get_height()) // 2))

    draw_the_dialog_background('РЕКОРДЫ')
    draw_the_dialog_background('В РАЗРАБОТКЕ...', y=250)
    draw_the_dialog_background('press button', y=480)


def show_info_menu():
    def draw_the_dialog_background(message, y=150):
        # init title
        font = pygame.font.Font(f'{FONTS_DIR}/Unicephalon.otf', 20)
        text = font.render(message, True, COLOR_TEXT)
        text_x = (WINDOW_WIDTH - text.get_width()) // 2
        text_y = y
        screen.blit(text, (text_x, text_y))
    # init fon
    fon = pygame.Surface((WINDOW_WIDTH * 0.7, WINDOW_HEIGHT * 0.7))
    fon.fill(pygame.Color((0, 255, 0)))
    screen.blit(fon, ((WINDOW_WIDTH - fon.get_width()) // 2,
                      (WINDOW_HEIGHT - fon.get_height()) // 2))

    draw_the_dialog_background('КАК ИГРАТЬ')
    draw_the_dialog_background('В РАЗРАБОТКЕ...', y=250)
    draw_the_dialog_background('press button', y=480)


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


def show_game_message(surface, main_message, *secondary_messages):
    # Darken the background:
    transparent_dark_surface = pygame.Surface(WINDOW_SIZE)
    transparent_dark_surface.fill(pygame.Color(0, 0, 0))
    transparent_dark_surface.set_alpha(220)
    surface.blit(transparent_dark_surface, (0, 0))

    # Show message:
    main_font = pygame.font.Font(f'{FONTS_DIR}/Thintel.ttf', 120)
    second_font = pygame.font.Font(f'{FONTS_DIR}/Thintel.ttf', 30)
    main_text = main_font.render(main_message, True, (255, 255, 255))
    secondary_messages = \
        list(map(lambda elem: second_font.render(
            elem, True, (255, 255, 255)), secondary_messages))
    text_x = WINDOW_WIDTH // 2 - main_text.get_width() // 2
    text_y = WINDOW_HEIGHT // 2 - \
             (main_text.get_height() + sum([
                 text.get_height() for text in secondary_messages])) // 2
    surface.blit(main_text, (text_x, text_y))
    text_y += main_text.get_height()
    for message in secondary_messages:  # show secondary messages
        text_x = WINDOW_WIDTH // 2 - message.get_width() // 2
        surface.blit(message, (text_x, text_y))
        text_y += message.get_height()


def start_screen():
    def draw_the_main_background():
        # init fon
        fon = pygame.Surface(WINDOW_SIZE)
        fon.fill(pygame.Color((0, 0, 0)))
        screen.blit(fon, (0, 0))

        # init title
        y = title_text_y
        for text in title_text:
            screen.blit(text, ((WINDOW_WIDTH - text.get_width()) // 2, y))
            y += text.get_height()

    draw_the_main_background()
    do_show_info = False
    do_show_scores = False
    while True:
        time_delta = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_user_info()
                terminate()  # exit
            if event.type == pygame.KEYDOWN or \
                    event.type == pygame.MOUSEBUTTONDOWN:
                do_show_info = False
                do_show_scores = False
            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
                    pass
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == start_menu_btn_dict['CONTINUE']:
                        return load_saved_game()
                    elif event.ui_element == start_menu_btn_dict['NEW GAME']:
                        return getattr(LevelLoader(), f'init_lvl{1}_scene')()
                    elif event.ui_element == start_menu_btn_dict['HIGH SCORES']:
                        do_show_scores = True
                    elif event.ui_element == start_menu_btn_dict['HOW TO PLAY']:
                        do_show_info = True
                    elif event.ui_element == start_menu_btn_dict['EXIT']:
                        save_user_info()
                        terminate()  # exit
                    elif event.ui_element == sound_btn:
                        sound_value_slider.show()
                        music_value_slider.hide()
                    elif event.ui_element == music_btn:
                        sound_value_slider.hide()
                        music_value_slider.show()
            if pygame.mouse.get_pos()[1] < 525:
                if sound_value_slider.visible:
                    sound_value_slider.hide()
                if music_value_slider.visible:
                    music_value_slider.hide()
            sound_btn.set_image(
                sound_on_img if sound_value_slider.current_value else sound_off_img)
            music_btn.set_image(
                music_on_img if music_value_slider.current_value else music_off_img)

            main_menu_manager.process_events(event)
        main_menu_manager.update(time_delta)

        draw_the_main_background()

        main_menu_manager.draw_ui(screen)

        if do_show_scores:
            show_highscore_board()
        if do_show_info:
            show_info_menu()

        pygame.display.flip()
        clock.tick(FPS)


def main():
    lvl_count = 1
    lvl_loader = LevelLoader()
    game = getattr(lvl_loader, f'init_lvl{lvl_count}_scene')()

    # Главный игровой цикл:
    running = True
    load_user_info()
    game = start_screen()
    is_paused = False
    while running:
        # Цикл приема и обработки сообщений:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                if is_paused:
                    is_paused = False
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            continue
                        elif event.key == pygame.K_RETURN:
                            # save_game(game)
                            game = start_screen()
                            break
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

                elif event.key == pygame.K_F12:
                    now = ''.join([elem for elem in str(dt.datetime.now()) if elem.isdigit()])
                    pygame.image.save(screen, f'data/screenshots/screenshot_{now}.png')
                elif event.key == pygame.K_ESCAPE and not is_paused:
                    show_game_message(screen, 'PAUSE', 'press Enter to exit')
                    is_paused = True

        # if game.end_count == 5:
        #     pygame.time.delay(3000)
        #     if game.end_game_and_return_status(screen) == 'win':
        #         lvl_count += 1
        #     game = getattr(lvl_loader, f'init_lvl{lvl_count}_scene')()

        if not is_paused:
            game.render(screen)
            game.update_controlled_tanks()
            game.update_uncontrolled_tanks()
            game.end_game_and_return_status(screen)

        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()


if __name__ == "__main__":
    main()
