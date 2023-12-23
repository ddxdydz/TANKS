import os
import sys
from random import random, choice
from datetime import datetime
from queue import Queue

import pygame
import pygame_gui
import pickle
import pytmx

from game_objects import *

WINDOW_SIZE = WINDOW_WIDTH, WINDOW_HEIGHT = 600, 600
TITLE = 'TANK BATTLES'
TILE_SIZE = 40
FPS = 15

MAPS_DIR = 'data/maps'
FONTS_DIR = 'data/fonts'
GUI_THEMES_DIR = 'data/gui_themes'
SAVED_USER_INFO_DIR = 'data/saved user info'
SOUND_DIR = 'data/sounds'
CUTSCENES_DIR = 'data/cutscenes'
SPRITES_DIR = 'sprites'

# Definition of constants (control)
FORWARD = 91
BACK = 92
TURN_RIGHT = 93
TURN_LEFT = 94
TURN_RIGHT_TURRET = 95
TURN_LEFT_TURRET = 96
SHOOT = 97

# Definition of constants (other)
WIN = 1
LOSE = 2
LOCAL_GAME_FINISHED = 3
TANK_BULLET = 10
URAN_BULET = 11
ENERGY_BULLET = 12
TNT_BULLET = 13

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
                   TURN_RIGHT: pygame.K_l, TURN_LEFT: pygame.K_j,
                   TURN_RIGHT_TURRET: pygame.K_o, TURN_LEFT_TURRET: pygame.K_u,
                   SHOOT: pygame.K_p}
CONTROL_KEYS_V4 = {FORWARD: pygame.K_KP8, BACK: pygame.K_KP2,
                   TURN_RIGHT: pygame.K_KP6, TURN_LEFT: pygame.K_KP4,
                   TURN_RIGHT_TURRET: pygame.K_KP9, TURN_LEFT_TURRET: pygame.K_KP7,
                   SHOOT: pygame.K_KP_PLUS}

DIRECTION_MOVE_BY_ANGLE = {0: (0, -1), 90: (-1, 0), 180: (0, 1), 270: (1, 0)}

COLOR_TEXT = pygame.Color((255, 255, 255))

# Init the pygame
pygame.init()
pygame.mixer.init()
pygame.display.set_caption(TITLE)
screen = pygame.display.set_mode(WINDOW_SIZE)
clock = pygame.time.Clock()

# Init UI
main_menu_manager = pygame_gui.UIManager(
    WINDOW_SIZE, os.path.join(os.getcwd(), GUI_THEMES_DIR, 'main_theme.json'))

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
accept_name_btn_size = (30, 26)
manipulate_user_btn_size = (20, 20)
select_box_size = (150, 200)
middle = (WINDOW_WIDTH - label_btn_size[0] - entry_line_size[0]) // 2
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
accept_name_btn = pygame_gui.elements.UIButton(
    relative_rect=pygame.Rect((
        middle + (label_btn_size[0] + entry_line_size[0]),
        title_text_y + title_text_height), accept_name_btn_size),
    text='OK',
    manager=main_menu_manager
)
select_box = pygame_gui.elements.UISelectionList(
    relative_rect=pygame.Rect((
        10,
        title_text_y + title_text_height), select_box_size),
    item_list=[],
    manager=main_menu_manager
)
accept_user_btn = pygame_gui.elements.UIButton(
    relative_rect=pygame.Rect((
        10,
        title_text_y + title_text_height + select_box_size[1]
    ), manipulate_user_btn_size),
    text='',
    manager=main_menu_manager
)
add_user_btn = pygame_gui.elements.UIButton(
    relative_rect=pygame.Rect((
        10 + (select_box_size[0] // 2 - manipulate_user_btn_size[0] // 2),
        title_text_y + title_text_height + select_box_size[1]
    ), manipulate_user_btn_size),
    text='',
    manager=main_menu_manager
)
remove_user_btn = pygame_gui.elements.UIButton(
    relative_rect=pygame.Rect((
        10 + (select_box_size[0] - manipulate_user_btn_size[0]),
        title_text_y + title_text_height + select_box_size[1]
    ), manipulate_user_btn_size),
    text='',
    manager=main_menu_manager
)

# Init main menu buttons
start_menu_buttons_intro = ['CONTINUE',
                            'NEW GAME',
                            'LOCAL GAME',
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
    relative_rect=pygame.Rect((
        indent_left, indent_down - sound_btn_size[1]), sound_btn_size),
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
    fullname = os.path.join('data/sprites', name)

    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()

    if colorkey == 0:
        image = pygame.image.load(fullname)
    else:
        image = pygame.image.load(fullname).convert()

    if colorkey is not None:
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


# Loading game menu graphics:
music_on_img = pygame.transform.scale(load_image("music_on.png"), sound_btn_size)
sound_on_img = pygame.transform.scale(load_image("sound_on.png"), sound_btn_size)
music_off_img = pygame.transform.scale(load_image("music_off.png"), sound_btn_size)
sound_off_img = pygame.transform.scale(load_image("sound_off.png"), sound_btn_size)
remove_user = pygame.transform.scale(load_image("remove_user.png"), manipulate_user_btn_size)
accept_user = pygame.transform.scale(load_image("accept_user.png"), manipulate_user_btn_size)
add_user = pygame.transform.scale(load_image("add_user.png"), manipulate_user_btn_size)

# Loading game menu sound:
back_to_menu = pygame.mixer.Sound(os.path.join(
    SOUND_DIR, 'menu', 'back_to_menu.mp3'))
choice_of_the_options = pygame.mixer.Sound(os.path.join(
    SOUND_DIR, 'menu', 'choice_of_the_options.mp3'))
selecting_of_the_options = pygame.mixer.Sound(os.path.join(
    SOUND_DIR, 'menu', 'selecting_of_the_options.mp3'))

icon = load_image('tank_icon.ico', colorkey=0)
pygame.display.set_icon(icon)


def play_background_music(name, loops=-1):
    load_user_info()
    pygame.mixer.music.stop()
    pygame.mixer.music.load(os.path.join(SOUND_DIR, 'music', f'{name}.mp3'))
    pygame.mixer.music.play(loops=loops)


def stop_background_music():
    pygame.mixer.music.stop()


def change_volume_background_music(volume):
    if volume > 1:
        volume = volume / 100
    pygame.mixer.music.set_volume(volume)


def get_player_coords():
    return load_user_info(True)[load_current_user()]['player_coords']


def set_player_coords(coords):
    save_user_info(coords)


def terminate():
    pygame.quit()
    sys.exit()


# Функции для работы с пользователями

def save_current_user(username=None):
    with open(f'{SAVED_USER_INFO_DIR}/current_user.dat', 'wb') as file:
        if username:
            name_entry_line.set_text(username)
        pickle.dump(name_entry_line.text, file)


def init_user_info():
    def create_file():
        if not os.path.exists(SAVED_USER_INFO_DIR):
            os.mkdir(SAVED_USER_INFO_DIR)

        with open(f'{SAVED_USER_INFO_DIR}/save.dat', 'wb') as file:
            save_current_user('USER_NAME')
            user = load_current_user()
            user_info = {user:
                             {'sound_value': 60,
                              'music_value': 60,
                              'current_score': 0,
                              'high_score': 0,
                              'current_lvl': 1,
                              'player_coords': (0, 0)}}
            pickle.dump(user_info, file)

    if os.path.exists(f'{SAVED_USER_INFO_DIR}/save.dat'):
        if os.path.getsize(f'{SAVED_USER_INFO_DIR}/save.dat') == 0:
            create_file()
        else:
            print('save.dat existing')
    else:
        create_file()


def load_current_user():
    with open(f'{SAVED_USER_INFO_DIR}/current_user.dat', 'rb') as file:
        username = pickle.load(file)
        return username


def save_user_info(coords=(0, 0)):
    user_info = load_user_info(return_user_info=True)
    user = load_current_user()
    if user not in user_info:
        user_info[user] = {}
        user_info[user]['current_score'] = 0
        user_info[user]['high_score'] = 0
        user_info[user]['current_lvl'] = 1
    user_info[user]['sound_value'] = sound_value_slider.current_value
    user_info[user]['music_value'] = music_value_slider.current_value
    user_info[user]['player_coords'] = coords
    with open(f'{SAVED_USER_INFO_DIR}/save.dat', 'wb') as file:
        pickle.dump(user_info, file)


def refresh_current_score_for_user(add_score):
    user_info = load_user_info(True)
    user = load_current_user()
    user_info[user]['current_score'] += add_score
    if add_score == -1:
        user_info[user]['current_score'] = 0
    if user_info[user]['current_score'] > user_info[user]['high_score']:
        user_info[user]['high_score'] = user_info[user]['current_score']
    with open(f'{SAVED_USER_INFO_DIR}/save.dat', 'wb') as file:
        pickle.dump(user_info, file)


def refresh_select_box_item_list():
    names = list(load_user_info(True).keys())
    select_box.set_item_list(names)


def load_user_info(return_user_info=False):
    with open(f'{SAVED_USER_INFO_DIR}/save.dat', 'rb') as file:
        user_info = pickle.load(file)
    if not return_user_info:
        user = load_current_user()
        sound_value_slider.set_current_value(user_info[user]['sound_value'])
        music_value_slider.set_current_value(user_info[user]['music_value'])
        change_volume_background_music(user_info[user]['music_value'])
    return user_info


def save_game(lvl):
    user_info = load_user_info(True)
    user_info[load_current_user()]['current_lvl'] = lvl
    with open(f'{SAVED_USER_INFO_DIR}/save.dat', 'wb') as file:
        pickle.dump(user_info, file)


def load_saved_game():
    return load_user_info(True)[load_current_user()]['current_lvl']


def rename_current_user():
    old_user = load_current_user()
    new_user = name_entry_line.text
    user_info = load_user_info(True)
    user_info[new_user] = user_info.pop(old_user)
    save_current_user(new_user)
    with open(f'{SAVED_USER_INFO_DIR}/save.dat', 'wb') as file:
        pickle.dump(user_info, file)
    refresh_select_box_item_list()


def delete_user():
    user = select_box.get_single_selection()
    user_info = load_user_info(True)
    user_info.pop(user)
    first_user = list(user_info.keys())[0]
    save_current_user(first_user)
    with open(f'{SAVED_USER_INFO_DIR}/save.dat', 'wb') as file:
        pickle.dump(user_info, file)
    refresh_select_box_item_list()


def get_ranges_from_detect(line):
    return eval(line[7:])


class Map:
    def __init__(self, filename):
        self.tiled_map = pytmx.load_pygame(f"{MAPS_DIR}/{filename}")

        self.map = self.generate_map()

        self.height = self.tiled_map.height
        self.width = self.tiled_map.width

        self.camera = Camera(self.width, self.height)

        # Init tile lists
        self.free_tiles = []
        self.break_tiles = []
        self.unbreak_tiles = []

        for y in range(self.height):
            for x in range(self.width):
                type_of_tile = self.get_type_of_tile(x, y)
                id_of_tile = self.tiled_map.get_tile_gid(x, y, 0)
                if 'free' in type_of_tile and id_of_tile not in self.free_tiles:
                    self.free_tiles.append(id_of_tile)
                elif type_of_tile == 'break' and id_of_tile not in self.break_tiles:
                    self.break_tiles.append(id_of_tile)
                elif 'unbreak' in type_of_tile and id_of_tile not in self.unbreak_tiles:
                    self.unbreak_tiles.append(id_of_tile)
        self.shadow = []
        self.lava = []
        self.map_objects = []

    def update_objects(self):
        for map_object in self.map_objects:
            x, y = map_object.get_position()
            if map_object.hidden:
                map_object.do_respawn()
            else:
                if isinstance(self.map[y][x], Player):
                    map_object.trigger_action(self)
                else:
                    self.map[y][x] = map_object

    def render(self, screen):
        screen.fill('#000000')
        camera_coord = \
            abs(self.camera.rect.x // TILE_SIZE), \
            abs(self.camera.rect.y // TILE_SIZE)
        for layer in self.tiled_map.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                for x, y, gid in layer:

                    # Объекты вне зоны действия камеры не будут отрисовываться
                    if not (x in range(camera_coord[0], self.camera.rect.width) and
                            y in range(camera_coord[1], self.camera.rect.height)):
                        continue

                    gid = self.map[y][x]
                    object_stand_on = False
                    # Если на блоке уже кто-то стоит
                    if not isinstance(gid, int):
                        gid = self.get_free_block(x, y)
                        object_stand_on = True

                    tile = self.tiled_map.get_tile_image_by_gid(gid)
                    if tile:
                        tile_rect = pygame.Rect(
                            0, 0, x * self.tiled_map.tilewidth,
                                  y * self.tiled_map.tileheight)
                        self.camera.apply(tile_rect)
                        screen.blit(tile, (tile_rect.width, tile_rect.height))

                        if (x, y) in self.lava:
                            screen.blit(lava, (tile_rect.width, tile_rect.height))

                        # Если на блоке кто-то стоит, надо отрисовать стоящего
                        if object_stand_on:
                            screen.blit(self.map[y][x].image,
                                        (tile_rect.width, tile_rect.height))
                            if getattr(self.map[y][x], 'tank_turret', False):
                                screen.blit(self.map[y][x].tank_turret.image,
                                            (tile_rect.width, tile_rect.height))
                            if self.map[y][x].respawn:
                                if self.map[y][x].respawn_time <= 90:
                                    self.map[y][x] = self.get_free_block(x, y)

                        if (x, y) in self.shadow:
                            shadow = pygame.Surface(
                                (self.tiled_map.tilewidth,
                                 self.tiled_map.tileheight))
                            shadow.fill(pygame.Color(0, 0, 0))
                            shadow.set_alpha(99)
                            screen.blit(shadow, (tile_rect.width,
                                                 tile_rect.height))
        self.update_objects()

    def generate_map(self):
        return [[self.tiled_map.get_tile_gid(x, y, 0)
                 for x in range(self.tiled_map.width)]
                for y in range(self.tiled_map.height)]

    def get_tile_id(self, position):
        return self.map[position[1]][position[0]]

    def get_type_of_tile(self, x, y):
        if x not in range(self.width) or y not in range(self.height):
            return None
        check_prop = self.tiled_map.get_tile_properties
        return check_prop(x, y, 0)['type']

    def get_free_block(self, x, y):
        id_of_free_block = self.tiled_map.get_tile_gid(x, y, 0)
        if id_of_free_block not in self.free_tiles:
            id_of_free_block = self.free_tiles[0]
        return id_of_free_block

    def is_free(self, position):
        return (self.get_tile_id(position) in self.free_tiles
                or isinstance(self.get_tile_id(position), MapObject)) and \
               position not in self.shadow

    def find_player(self, control_keys):
        for y in range(self.height):
            for x in range(self.width):
                if self.map[y][x].__repr__() == 'Player':
                    if self.map[y][x].control_keys == control_keys:
                        return x, y

    def give_game_objects_lists(self, sprite_group):
        destinations = dict()
        player_list: Player = []
        tank_list = []
        for tile_object in self.tiled_map.objects:
            # Парсинг тени и лавы
            if tile_object.name in ['Shadow', 'Lava']:
                if tile_object.name == 'Shadow':
                    special_group = self.shadow
                else:
                    special_group = self.lava
                x = int(tile_object.x // TILE_SIZE)
                y = int(tile_object.y // TILE_SIZE)
                w = int(tile_object.width // TILE_SIZE)
                h = int(tile_object.height // TILE_SIZE)
                for y_step in range(y, y + h):
                    for x_step in range(x, x + w):
                        special_group.append((x_step, y_step))
            # Парсинг объектов карты
            elif 'Map' in tile_object.name:
                x, y = int(tile_object.x // TILE_SIZE), int(tile_object.y // TILE_SIZE)
                respawn = tile_object.properties.get('respawn', False)
                respawn_time = tile_object.properties.get('respawn_time', 0)
                hidden = tile_object.properties.get('hidden', False)
                init_object_string = f'{tile_object.name}((x, y), {respawn},' \
                                     f' {respawn_time}, {hidden})'

                self.map_objects.append(eval(init_object_string))
            # Парсинг танков
            else:
                rotate_turret = tile_object.properties['rotate_turret']
                rotate_hull = tile_object.properties['rotate_hull']
                destination = str(tile_object.properties['destination'])
                respawn = tile_object.properties.get('respawn', False)
                x, y = int(tile_object.x // TILE_SIZE), int(tile_object.y // TILE_SIZE)
                init_object_string = f'{tile_object.name.split(" ")[0]}((x, y),' \
                                     f' rotate_turret=rotate_turret,' \
                                     f' rotate_hull=rotate_hull, group=sprite_group,' \
                                     f' respawn=respawn)'
                if 'Player' in tile_object.name:
                    player_list.append(eval(init_object_string))
                else:
                    tank_list.append(eval(init_object_string))

                if destination == 'self':
                    destinations[tank_list[-1]] = None
                elif destination == 'player':
                    destinations[tank_list[-1]] = get_player_coords
                elif 'detect' in destination:
                    def detect_func(range_x, range_y):
                        if get_player_coords()[0] in range_x and \
                                get_player_coords()[1] in range_y:
                            return get_player_coords
                        return None

                    ranges = get_ranges_from_detect(destination)
                    destinations[tank_list[-1]] = (detect_func, ranges)
                elif 'pos' in destination:
                    destinations[tank_list[-1]] = \
                        eval(destination[len('pos '):])

        return player_list, tank_list, destinations


class Game:
    def __init__(self, map, bullets, sprites_group=None):
        self.map = map
        self.camera = self.map.camera

        # Init objects groups
        self.sprites_group = [] if sprites_group is None else sprites_group
        self.controlled_tanks, self.uncontrolled_tanks, self.destinations = \
            (self.map.give_game_objects_lists(sprites_group[0]))

        self.defeat_reasons = []
        self.missions = []
        self.events = []
        self.cutscenes = []
        self.is_active_cutscene = False
        self.final_lvl = True

        self.bullets = bullets

        self.timer = 0

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
            bullet_x, bullet_y = \
                [round(i) for i in bullet.get_position()]
            if bullet_x not in range(0, self.map.width) or \
                    bullet_y not in range(0, self.map.height):
                del self.bullets[self.bullets.index(bullet)]
                continue
            if not self.map.is_free((bullet_x, bullet_y)):
                if 'water' not in self.map.get_type_of_tile(bullet_x, bullet_y):
                    result = self.destruct_cell(bullet_x, bullet_y, bullet)
                    if result == 'break':
                        bullet.sounds_break()
                        if not bullet.damage_type == ENERGY_BULLET:
                            del self.bullets[self.bullets.index(bullet)]
                        else:
                            bullet.damage_type = None
                    else:
                        bullet.sounds_unbreak()
                        if not bullet.damage_type == ENERGY_BULLET or 'full' in result:
                            del self.bullets[self.bullets.index(bullet)]
                        else:
                            bullet.damage_type = None

    def destruct_cell(self, bullet_x, bullet_y, bullet=None):
        # Обработка попадания пули в танк
        if getattr(self.map.map[bullet_y][bullet_x], 'team', False):
            tank = self.map.map[bullet_y][bullet_x]
            # Если танк случайно въехал в свою пулю

            damage = 1
            if bullet:
                if tank == bullet.owner and tank.dict_id_bullets['damage_type'] == bullet.damage_type:
                    return
                if bullet.damage_type == URAN_BULET:
                    damage = 2
            tank.health -= damage
            if tank.health <= 0:
                if tank.is_crashed:
                    self.map.map[bullet_y][bullet_x] = \
                        self.map.get_free_block(bullet_x, bullet_y)
                    tank.clear_the_tank()
                else:
                    if bullet:
                        if bullet.owner == tank:
                            bullet.owner.kills -= 1
                        elif bullet.owner:
                            bullet.owner.kills += 1
                    tank.destroy_the_tank(self.uncontrolled_tanks)
                self.draw_explosion(bullet_x, bullet_y)
                return 'break'
            self.draw_flash(bullet_x, bullet_y)
            return 'unbreak small'
        elif self.map.map[bullet_y][bullet_x] in self.map.break_tiles:
            self.map.map[bullet_y][bullet_x] = \
                self.map.get_free_block(bullet_x, bullet_y)
            self.draw_smoke(bullet_x, bullet_y)
        elif self.map.get_type_of_tile(bullet_x, bullet_y) == 'tnt':
            self.make_reflect_explode(bullet_x, bullet_y, bullet)
            self.draw_explosion(bullet_x, bullet_y)
        elif self.map.get_tile_id((bullet_x, bullet_y)) in self.map.unbreak_tiles:
            self.draw_flash(bullet_x, bullet_y)
            return 'unbreak full'
        return 'break'

    def draw_explosion(self, x, y):
        rect = pygame.Rect(0, 0, x * TILE_SIZE, y * TILE_SIZE)
        self.camera.apply(rect)
        screen.blit(explosion, (rect.w, rect.h))

    def draw_flash(self, x, y):
        rect = pygame.Rect(0, 0, x * TILE_SIZE, y * TILE_SIZE)
        self.camera.apply(rect)
        screen.blit(flash, (rect.w, rect.h))

    def draw_smoke(self, x, y):
        rect = pygame.Rect(0, 0, x * TILE_SIZE, y * TILE_SIZE)
        self.camera.apply(rect)
        screen.blit(smoke, (rect.w, rect.h))

    def make_explode(self, x, y):
        for y_step in (max((0, y - 1)), y, min(self.map.height, y + 1)):
            for x_step in (max((0, x - 1)), x, min(self.map.height, x + 1)):
                self.destruct_cell(x_step, y_step)
                self.draw_explosion(x_step, y_step)
        play_sound(None, os.path.join(SOUND_DIR, 'other', 'boss_shot.mp3'))

    def make_reflect_explode(self, x, y, bullet=None):
        owner = None
        if bullet:
            if bullet.owner:
                owner = bullet.owner
        self.map.map[y][x] = self.map.get_free_block(x, y)
        for angle in range(0, 271, 90):
            tnt_bullet = Bullet((x, y), angle, tnt_bullet_dict, owner)
            self.bullets.append(tnt_bullet)

    def update_controlled_tanks(self):
        for player in self.controlled_tanks:
            is_movement_key_pressed = False

            player.update_timers(clock)
            if player.is_crashed:
                continue
            unpack_player_coords = self.map.find_player(player.control_keys)
            if not unpack_player_coords:
                cur_x, cur_y = next_x, next_y = player.get_position()
            else:
                cur_x, cur_y = next_x, next_y = unpack_player_coords

            rotate_turret, rotate_hull = player.get_rotate()
            self.map.map[cur_y][cur_x] = player

            if pygame.key.get_pressed()[player.control_keys[FORWARD]]:
                is_movement_key_pressed = True
                while player.rotate_hull != 0:
                    player.set_rotate(90)

            elif pygame.key.get_pressed()[player.control_keys[BACK]]:
                is_movement_key_pressed = True
                while player.rotate_hull != 180:
                    player.set_rotate(90)

            elif pygame.key.get_pressed()[player.control_keys[TURN_RIGHT]]:
                is_movement_key_pressed = True
                while player.rotate_hull != 270:
                    player.set_rotate(90)

            elif pygame.key.get_pressed()[player.control_keys[TURN_LEFT]]:
                is_movement_key_pressed = True
                while player.rotate_hull != 90:
                    player.set_rotate(90)

            if is_movement_key_pressed:
                dx, dy = DIRECTION_MOVE_BY_ANGLE[player.rotate_hull]
                next_x, next_y = cur_x + dx, cur_y + dy
                if self.map.is_free((next_x, next_y)):
                    if player.move_forward():
                        self.map.map[cur_y][cur_x] = self.map.get_free_block(cur_x, cur_y)
                        self.map.map[next_y][next_x] = player
            if pygame.key.get_pressed()[player.control_keys[TURN_RIGHT_TURRET]]:
                if player.rotate_turret == 180:
                    player.is_turret_rotating_right_up = False
                elif player.rotate_turret == 0:
                    player.is_turret_rotating_right_up = True

                if player.is_turret_rotating_right_up:
                    player.turn_turret_right()
                else:
                    player.turn_turret_left()
            elif pygame.key.get_pressed()[player.control_keys[TURN_LEFT_TURRET]]:
                if player.rotate_turret == 180:
                    player.is_turret_rotating_left_up = False
                elif player.rotate_turret == 0:
                    player.is_turret_rotating_left_up = True

                if player.is_turret_rotating_left_up:
                    player.turn_turret_left()
                else:
                    player.turn_turret_right()

            elif pygame.key.get_pressed()[player.control_keys[SHOOT]]:
                player.shoot(self.bullets)

            self.camera.update(player)
            self.camera.apply(player)
            self.map.camera = self.camera
            set_player_coords(player.get_position())

            if (next_x, next_y) == (cur_x, cur_y):
                player.play_brake()

    def update_uncontrolled_tanks(self):
        for tank in self.uncontrolled_tanks:
            tank.update_timers(clock)
            if tank.is_crashed:
                continue

            destination = self.destinations[tank]

            if callable(destination):
                destination = destination()

            elif isinstance(destination, tuple):
                if callable(destination[0]):
                    destination = destination[0](*destination[1])
                    if destination != None:
                        self.destinations[tank] = destination
                        if callable(destination):
                            destination = destination()

            if random() > 1 - tank.accuracy:
                self.calculate_uncontrolled_tank_turret(tank)

            if random() > 1 - tank.speed:
                if destination != None:
                    path = self.find_path(tank.get_position(), destination)
                    if len(path) > 2:
                        self.calculate_uncontrolled_tank_move(path, tank)
            x, y = tank.get_position()
            self.map.map[y][x] = tank

    def calculate_uncontrolled_tank_turret(self, tank):
        def break_check(cell):
            if cell not in self.map.unbreak_tiles:
                if cell.__repr__() == 'Player' and tank.team == 'green':
                    return True
                return False
            return True

        def from_other_team(cell):
            try:
                team = getattr(cell, 'team', tank.team)
                return tank.team != team
            except Exception as e:
                return False

        cur_x, cur_y = tank.get_position()
        rotate_turret = tank.get_rotate()[0]

        down_y_axis = [self.map.map[y][cur_x]
                       for y in range(cur_y, len(self.map.map))]
        up_y_axis = [self.map.map[y][cur_x]
                     for y in range(cur_y, 0, -1)]
        left_x_axis = [self.map.map[cur_y][x]
                       for x in range(cur_x, 0, -1)]
        right_x_axis = [self.map.map[cur_y][x]
                        for x in range(cur_x, len(self.map.map[0]))]

        for cell in left_x_axis:
            if break_check(cell):
                break
            if from_other_team(cell):
                if rotate_turret == 90:
                    tank.shoot(self.bullets)
                elif rotate_turret == 0:
                    tank.turn_turret_left()
                elif rotate_turret == 180:
                    tank.turn_turret_right()
                return None
        for cell in right_x_axis:
            if break_check(cell):
                break
            if from_other_team(cell):
                if rotate_turret == 270:
                    tank.shoot(self.bullets)
                elif rotate_turret == 0:
                    tank.turn_turret_right()
                elif rotate_turret == 180:
                    tank.turn_turret_left()
                return None
        for cell in up_y_axis:
            if break_check(cell):
                break
            if from_other_team(cell):
                if rotate_turret == 0:
                    tank.shoot(self.bullets)
                elif rotate_turret == 90:
                    tank.turn_turret_right()
                elif rotate_turret == 270:
                    tank.turn_turret_left()
                elif rotate_turret == 180:
                    tank.turn_turret_right()
                return None
        for cell in down_y_axis:
            if break_check(cell):
                break
            if from_other_team(cell):
                if rotate_turret == 180:
                    tank.shoot(self.bullets)
                elif rotate_turret == 0:
                    tank.turn_turret_left()
                elif rotate_turret == 270:
                    tank.turn_turret_right()
                elif rotate_turret == 90:
                    tank.turn_turret_left()
                return None

    def calculate_uncontrolled_tank_move(self, path, tank):
        def turn_hull_optimal(degree):
            if rotate_hull + 90 == degree:
                tank.turn_left()
            else:
                tank.turn_right()

        cur_x, cur_y = tank.get_position()
        rotate_hull = tank.get_rotate()[1]
        next_step = path[1]
        direction_move = self.calculate_direction(
            tank.get_position(), next_step)
        next_x = cur_x + direction_move[0]
        next_y = cur_y + direction_move[1]
        if direction_move == (0, 1):
            if rotate_hull == 180:
                if tank.move_forward():
                    self.map.map[cur_y][cur_x] = \
                        self.map.get_free_block(cur_x, cur_y)
                    self.map.map[next_y][next_x] = tank
            else:
                turn_hull_optimal(180)
        if direction_move == (1, 0):
            if rotate_hull == 270:
                if tank.move_forward():
                    self.map.map[cur_y][cur_x] = \
                        self.map.get_free_block(cur_x, cur_y)
                    self.map.map[next_y][next_x] = tank
            else:
                turn_hull_optimal(270)
        if direction_move == (0, -1):
            if rotate_hull == 0:
                if tank.move_forward():
                    self.map.map[cur_y][cur_x] = \
                        self.map.get_free_block(cur_x, cur_y)
                    self.map.map[next_y][next_x] = tank
            else:
                turn_hull_optimal(0)
        if direction_move == (-1, 0):
            if rotate_hull == 90:
                if tank.move_forward():
                    self.map.map[cur_y][cur_x] = \
                        self.map.get_free_block(cur_x, cur_y)
                    self.map.map[next_y][next_x] = tank
            else:
                turn_hull_optimal(90)

    def calculate_direction(self, this_step, next_step):
        return tuple(next_step[i] - this_step[i]
                     for i in range(len(this_step)))

    def find_path(self, start, destination):
        def calculate_distance_for_destination(cell):
            a, b = abs(cell[0] - destination[0]) + 1, \
                   abs(cell[1] - destination[1])
            c = pow((a ** 2 + b ** 2), 0.5)

            return c

        def get_neighbours(cell):
            neighbours = []
            pathfinder = self.map.map[start[1]][start[0]]
            for y in (cell[1] - 1, cell[1], cell[1] + 1):
                if y == cell[1]:
                    x_list = (cell[0] - 1, cell[0] + 1)
                else:
                    x_list = (cell[0], cell[0])
                for x in x_list:
                    if all([(0 <= y < len(self.map.map)),
                            (0 <= x < len(self.map.map[0]))]):
                        if pathfinder.__repr__() == 'Convoy':
                            if self.map.map[y][x] == self.map.free_tiles[0] \
                                    or (x, y) == destination:
                                neighbours.append((x, y))
                        elif self.map.is_free((x, y)) or \
                                (x, y) == destination:
                            neighbours.append((x, y))
            return neighbours

        queue = Queue()
        queue.put(start)
        came_from = {}
        came_from[start] = None
        restriction = 50  # ограничение по поиску соседей в целях оптимизации

        while not queue.empty():
            current_cell = queue.get()
            cells = get_neighbours(current_cell)

            for cell in cells:
                if cell not in came_from:
                    came_from[cell] = current_cell
                    queue.put(cell)

            restriction -= 1
            if restriction < 0:
                break
        current_cell = destination
        path = [destination]
        while current_cell != start:
            if current_cell not in came_from:
                distances = [(cell, calculate_distance_for_destination(cell))
                             for cell in came_from.keys()]
                current_cell = min(distances, key=lambda x: x[1])[0]
                path = [current_cell]
            if current_cell != start:
                current_cell = came_from[current_cell]
            path.append(current_cell)
        path.reverse()
        return path

    def end_game_and_return_status(self, screen, return_status=False):
        reasons = [reason() for reason in self.defeat_reasons]
        if any(reasons):
            if not return_status:
                if self.timer == 0:
                    play_background_music('lose', 0)
                show_game_message(screen, 'YOU LOSE!',
                                  'press any button to continue')
                self.timer += 1
            return LOSE
        results = [mission() for mission in self.missions]
        if any(results):
            status = WIN
            if len(self.controlled_tanks) > 1:
                status = LOCAL_GAME_FINISHED

            if not return_status:
                _, begin_uncontrolled, _ = \
                    self.map.give_game_objects_lists(self.sprites_group[0])
                if self.timer == 0:
                    play_background_music('win')
                if len(self.controlled_tanks) > 1:
                    top_player = max(self.controlled_tanks, key=lambda x: x.kills)
                    name = CONTROLLED_PLAYERS_DICT[top_player.control_keys[SHOOT]]['name']
                    message = f'{name.upper()} WIN'
                    score_message = f'SCORE: {top_player.kills}'
                else:
                    temp_score = calculate_highscore(self.uncontrolled_tanks, begin_uncontrolled)
                    message = 'YOU WIN'
                    user_info = load_user_info(True)
                    user = load_current_user()
                    global_score = user_info[user]['current_score'] + temp_score
                    score_message = f'LEVEL SCORE: {temp_score}    ' \
                                    f'GLOBAL SCORE: {global_score}'
                show_game_message(screen, message,
                                  f'press any button to continue',
                                  score_message)
                self.timer += 1
            return status

    def make_events(self):
        [event() for event in self.events]

    def parse_cutscenes_from_file(self, name_file):
        with open(f'{CUTSCENES_DIR}/{name_file}', 'r', encoding='utf-8') as file:
            if '10' in name_file:
                self.final_lvl = True

            def trigger_on_detect(coords, ranges):
                if coords[0] in ranges[0] and coords[1] in ranges[1]:
                    return True
                return False

            for line in file:
                if 'detect' in line:
                    ranges = get_ranges_from_detect(line)
                    self.cutscenes.append(
                        {'trigger': trigger_on_detect,
                         'args': ranges, 'content': []})
                elif line != '\n':
                    if ':::' in line:
                        content = [i.replace('\n', '') for i in line.split(':::')]
                        content[1] = content[1].replace('[CURRENT_USER]', load_current_user())
                    else:
                        content = [int(i) for i in line.split(', ')]
                    self.cutscenes[-1]['content'].append(tuple(content))

    def show_cutscenes(self, return_status=False):
        def remove_cutscene():
            self.is_active_cutscene = False
            self.camera.update(self.controlled_tanks[0])
            self.cutscenes.remove(scene)
            self.timer = 0

        if return_status:
            return self.is_active_cutscene

        for scene in self.cutscenes:
            trigger, args = scene['trigger'], \
                            (get_player_coords(), scene['args'])
            if trigger(*args):
                if self.is_active_cutscene:
                    if self.timer == 0:
                        try:
                            replica = scene['content'].pop(0)
                            self.timer = 60
                        except IndexError:
                            remove_cutscene()
                            return True
                    else:
                        try:
                            replica = scene['content'][0]
                        except IndexError:
                            remove_cutscene()
                            return True

                    if isinstance(replica[0], int) and \
                            isinstance(replica[1], int):
                        self.move_camera(replica)
                        replica = None
                    elif len(replica[1]) > 45:
                        stroke = []
                        line = replica[1].split()
                        begin_index = 0
                        for i in range(1, len(line) + 1):
                            if sum(len(j) for j in line[begin_index:i]) + i - 1 > 45:
                                stroke.append(' '.join(line[begin_index:i]))
                                begin_index = i
                            if i == len(line):
                                stroke.append(' '.join(line[begin_index:i]))
                        replica = (replica[0], stroke)

                    show_cutscene(screen, replica)
                    self.timer -= 1
                    if self.final_lvl:
                        rect = pygame.Rect(0, 0, 1720, 320)
                        self.camera.apply(rect)
                        screen.blit(boss_hull, (rect.w, rect.h))
                    return True
                self.is_active_cutscene = True
                self.timer = 60

                return True

    def move_camera(self, coords):
        if self.timer == 1:
            self.camera.map_x, self.camera.map_y = coords
            self.camera.update(coords, immediately=True)
        self.camera.update(coords)


class Camera:
    def __init__(self, width, height, shift_x=7, shift_y=7):
        self.width = width
        self.height = height
        self.rect = pygame.Rect(0, 0, self.width, self.height)
        self.shift_x = shift_x
        self.shift_y = shift_y
        self.map_x, self.map_y = 0, 0

    def apply(self, obj):
        if isinstance(obj, Bullet):
            obj.rect.x += self.rect.left
            obj.rect.y += self.rect.top
        if isinstance(obj, Tank):
            pass
        elif isinstance(obj, pygame.Rect):
            obj.width += self.rect.left
            obj.height += self.rect.top

    def update(self, target, immediately=False):
        if isinstance(target, tuple):
            target_x, target_y = target
            if self.map_x > target_x:
                self.map_x -= 1
            elif self.map_x < target_x:
                self.map_x += 1

            if self.map_y > target_y:
                self.map_y -= 1
            elif self.map_y < target_y:
                self.map_y += 1
            target_x, target_y = self.map_x, self.map_y
        else:
            target_x = target.x
            target_y = target.y
            self.map_x, self.map_y = target_x, target_y

        dx = -(target_x * TILE_SIZE - (self.shift_x * TILE_SIZE))
        dy = -(target_y * TILE_SIZE - (self.shift_y * TILE_SIZE))

        # ограничения камеры, чтобы она не показала черных границы
        if abs(dx) >= (self.width - 14) * TILE_SIZE:
            dx = self.rect.x
            if immediately:
                dx = -(self.width - 15) * TILE_SIZE
        if dx > 0:
            dx = 0

        if abs(dy) >= (self.height - 14) * TILE_SIZE:
            dy = self.rect.y
        if dy > 0:
            dy = 0
            if immediately:
                dx = -(self.height - 15) * TILE_SIZE
        self.rect = pygame.Rect(dx, dy, self.width, self.height)


class LevelLoader:
    def init_reasons_and_missions(self, game):
        def debug_show_fps():
            fps = round(clock.get_fps())
            if fps > 13:
                color = (0, 255, 0)
            elif fps > 9:
                color = (255, 255, 0)
            else:
                color = (255, 0, 0)
            font = pygame.font.Font(f'{FONTS_DIR}/Thintel.ttf', 40)
            text = font.render(f'FPS: {fps}', True, pygame.Color(color))
            screen.blit(text, (WINDOW_WIDTH - text.get_width(), 0))

        def show_hp():
            player_health = game.controlled_tanks[0].health
            size_x = health.get_width()
            if player_health > 2:
                x = (screen.get_width() // 2) - ((player_health * size_x) // 2)
            else:
                x = (screen.get_width() // 2) - ((2 * size_x) // 2)
            y = 15
            for i in range(2):
                screen.blit(losted_health, (x + (size_x * i), y))
            for i in range(player_health):
                if i < 2:
                    screen.blit(health, (x + (size_x * i), y))
                else:
                    screen.blit(extra_health, (x + (size_x * i), y))

        # Инициализация условий

        self.stand_on_control_point = \
            lambda: game.map.get_type_of_tile(
                get_player_coords()[0],
                get_player_coords()[1]) == 'free_control_point'
        self.all_bots_are_dead = \
            lambda: len(game.uncontrolled_tanks) == 0
        self.player_are_dead = \
            lambda: game.controlled_tanks[0].is_crashed
        self.convoy_turn_around = \
            lambda: [tank.shoot([]) for tank in game.uncontrolled_tanks
                     if tank.__repr__() == 'Convoy']
        self.all_convoy_is_dead = \
            lambda: [i.__repr__() for i in
                     game.uncontrolled_tanks].count('Convoy') < 2

        # Добавление "постоянных" событий
        game.events.extend((show_hp, debug_show_fps))

    def init_local_game(self, players_controls):
        def highscores_showed():
            return False

        def timer_ticking():
            game.timer -= 1

        def show_timer_and_highscores_after_game():
            if game.timer >= 0:
                color = (255, 255, 255)
                font = pygame.font.Font(f'{FONTS_DIR}/Thintel.ttf', 40)
                text = font.render(f'{game.timer // 100}', True, pygame.Color(color))
                screen.blit(text, (WINDOW_WIDTH // 2 - text.get_width() // 2, 0))
            else:
                for tank in game.controlled_tanks:
                    tank.is_crashed = True
                show_highscore_board(game.controlled_tanks)
                if pygame.key.get_pressed()[pygame.K_SPACE]:
                    game.missions[0] = lambda: True

        def show_health_and_kills_on_players():
            for tank in game.controlled_tanks:
                player_health = tank.health
                if player_health > 0:
                    small_health = pygame.transform.scale(health.copy(), (10, 10))
                    losted_small_health = pygame.transform.scale(losted_health.copy(), (10, 10))
                    extra_small_health = pygame.transform.scale(extra_health.copy(), (10, 10))

                    x, y = tank.get_position()[0] * TILE_SIZE, tank.get_position()[1] * TILE_SIZE
                    # Отрисовка "киллов"
                    color = (255, 255, 0)
                    font = pygame.font.Font(f'{FONTS_DIR}/Thintel.ttf', 20)
                    text = font.render(f'{tank.kills}', True, pygame.Color(color))
                    screen.blit(text, (x, y + TILE_SIZE))

                    # Отрисовка хп
                    size_x = 10
                    if player_health > 2:
                        x += TILE_SIZE // 2 - (player_health * size_x) // 2
                    else:
                        x += TILE_SIZE // 2 - (2 * size_x) // 2
                    for i in range(2):
                        screen.blit(losted_small_health, (x + (size_x * i), y))
                    for i in range(player_health):
                        if i < 2:
                            screen.blit(small_health, (x + (size_x * i), y))
                        else:
                            screen.blit(extra_small_health, (x + (size_x * i), y))

        def random_map_object():
            args = ((7, 7), True, 1000, False)
            if len(game.map.map_objects) == 2:
                new_map_obj = choice(
                    (Boost_MapObject, Uran_MapObject, Energy_MapObject))(*args)
                game.map.map_objects.append(new_map_obj)
            mp_obj = game.map.map_objects[-1]
            if mp_obj.respawn_time == 1:
                new_map_obj = choice(
                    (Boost_MapObject, Uran_MapObject, Energy_MapObject))(*args)
                game.map.map_objects[-1] = new_map_obj

        def reload_map():
            if game.timer % 1500 == 0:
                for y in range(game.map.tiled_map.height):
                    for x in range(game.map.tiled_map.width):
                        if game.map.get_tile_id((x, y)) != game.map.tiled_map.get_tile_gid(x, y, 0):
                            game.draw_smoke(x, y)
                game.map.map = game.map.generate_map()
                # Чтобы танк не застрял в возродившемся блоке
                for tank in game.controlled_tanks:
                    tank_pos = tank.get_position()
                    if not game.map.is_free(tank_pos):
                        game.map.map[tank_pos[1]][tank_pos[0]] = game.map.get_free_block(tank_pos[0],
                                                                                         tank_pos[1])

        play_background_music('local_game')

        main_map = Map('local_game.tmx')

        bullets = []
        all_sprites = pygame.sprite.Group()
        game = Game(main_map, bullets, sprites_group=[all_sprites])
        self.init_reasons_and_missions(game)

        game.timer = 6000

        # Покрас каждого танка
        for tank_index in range(len(game.controlled_tanks)):
            tank = game.controlled_tanks[tank_index]
            setattr(tank, 'control_keys',
                    eval(f'CONTROL_KEYS_V{tank_index + 1}'))
            tank.init_tank_graphics(tank.get_position(), tank.get_rotate()[1], tank.get_rotate()[0])

        # Удаление танков, которые не участвуют в игре
        active_tanks = []
        for tank in game.controlled_tanks:
            if tank.control_keys in players_controls:
                active_tanks.append(tank)
        game.controlled_tanks = active_tanks.copy()

        game.missions = [highscores_showed]
        game.events[0] = show_health_and_kills_on_players
        game.events.extend(
            [timer_ticking, show_timer_and_highscores_after_game, random_map_object, reload_map])

        return game

    def init_lvl1_scene(self):
        main_map = Map("1_lvl.tmx")
        play_background_music('1_lvl')

        all_sprites = pygame.sprite.Group()

        bullets = []
        game = Game(main_map, bullets, sprites_group=[all_sprites])
        self.init_reasons_and_missions(game)
        game.parse_cutscenes_from_file('1_lvl')

        game.missions = [self.all_bots_are_dead]
        game.defeat_reasons = [self.player_are_dead]
        return game

    def init_lvl2_scene(self):
        main_map = Map("2_lvl.tmx")
        play_background_music('2_lvl')

        all_sprites = pygame.sprite.Group()

        bullets = []

        game = Game(main_map, bullets, sprites_group=[all_sprites])
        game.parse_cutscenes_from_file('2_lvl')

        self.init_reasons_and_missions(game)
        game.missions = [lambda: game.map.is_free((38, 9))]
        game.defeat_reasons = [self.player_are_dead, lambda: game.map.is_free((1, 9))]
        return game

    def init_lvl3_scene(self):
        def open_door():
            if all(cell in game.map.free_tiles for cell in
                   sum([game.map.map[23][1:3], game.map.map[24][1:3]], [])):
                game.map.map[6][19] = game.map.free_tiles[0]

        main_map = Map("3_lvl.tmx")
        play_background_music('3_lvl')
        all_sprites = pygame.sprite.Group()

        bullets = []

        game = Game(main_map, bullets, sprites_group=[all_sprites])
        self.init_reasons_and_missions(game)
        game.events.extend([open_door, self.convoy_turn_around])
        game.parse_cutscenes_from_file('3_lvl')

        game.missions = [self.stand_on_control_point]
        game.defeat_reasons = [self.player_are_dead]
        return game

    def init_lvl4_scene(self):
        main_map = Map("4_lvl.tmx")
        play_background_music('4_lvl')
        all_sprites = pygame.sprite.Group()

        bullets = []

        game = Game(main_map, bullets, sprites_group=[all_sprites])
        game.parse_cutscenes_from_file('4_lvl')
        self.init_reasons_and_missions(game)
        game.events.append(self.convoy_turn_around)

        convoy_here = lambda: [i.__repr__() for i in sum(
            [game.map.map[60][22:26],
             game.map.map[61][22:26]], [])].count('Convoy') == 2
        game.missions = [convoy_here]
        game.defeat_reasons = [self.player_are_dead, self.all_convoy_is_dead]
        return game

    def init_lvl5_scene(self):

        main_map = Map("5_lvl.tmx")
        play_background_music('5_lvl')
        all_sprites = pygame.sprite.Group()

        bullets = []

        game = Game(main_map, bullets, sprites_group=[all_sprites])
        self.init_reasons_and_missions(game)
        game.events.append(self.convoy_turn_around)
        game.parse_cutscenes_from_file('5_lvl')

        game.missions = [self.stand_on_control_point]
        game.defeat_reasons = [self.player_are_dead]
        return game

    def init_lvl6_scene(self):
        def open_door():
            if all(cell in game.map.free_tiles for cell in sum(
                    [game.map.map[9][19:21],
                     game.map.map[10][19:21]], [])):
                game.map.map[21][27] = game.map.free_tiles[0]

        main_map = Map("6_lvl.tmx")
        play_background_music('6_lvl')
        all_sprites = pygame.sprite.Group()

        bullets = []

        game = Game(main_map, bullets, sprites_group=[all_sprites])
        game.events.append(open_door)
        game.parse_cutscenes_from_file('6_lvl')

        self.init_reasons_and_missions(game)
        game.missions = [self.stand_on_control_point]
        game.defeat_reasons = [self.player_are_dead]
        return game

    def init_lvl7_scene(self):
        def explode_tnt():
            if get_player_coords() == (22, 5):
                game.make_reflect_explode(27, 5)
                game.events.remove(explode_tnt)

        main_map = Map("7_lvl.tmx")
        play_background_music('7_lvl')
        all_sprites = pygame.sprite.Group()

        bullets = []

        game = Game(main_map, bullets, sprites_group=[all_sprites])
        game.parse_cutscenes_from_file('7_lvl')

        self.init_reasons_and_missions(game)
        game.missions = [self.stand_on_control_point]
        game.defeat_reasons = [self.player_are_dead]
        game.events.append(explode_tnt)
        return game

    def init_lvl8_scene(self):
        def open_door():
            if all(cell in game.map.free_tiles for cell in sum(
                    [game.map.map[21][2:4], game.map.map[22][2:4],
                     game.map.map[21][6:8], game.map.map[22][6:8]], [])):
                game.map.map[23][17] = game.map.free_tiles[0]
                game.map.map[33][17] = game.map.free_tiles[0]
                game.map.shadow.append((17, 23))
                stop_background_music()
                if game.cutscenes:
                    game.cutscenes[0]['trigger'] = lambda arg1, arg2: True

        main_map = Map("8_lvl.tmx")
        play_background_music('8_lvl')
        all_sprites = pygame.sprite.Group()

        bullets = []

        game = Game(main_map, bullets, sprites_group=[all_sprites])
        game.parse_cutscenes_from_file('8_lvl')
        self.init_reasons_and_missions(game)

        game.events.append(open_door)

        game.missions = [lambda: (17, 33) == get_player_coords()]
        game.defeat_reasons = [self.player_are_dead]
        return game

    def init_lvl9_scene(self):
        def lava_kill_tanks():
            for group in [game.uncontrolled_tanks, game.controlled_tanks]:
                for tank in group:
                    if tank.get_position() in game.map.lava:
                        tank.destroy_the_tank(group)

        def lava_spread():
            game.timer += 1
            if game.timer == 10:
                game.map.lava.extend(
                    [(x, game.map.lava[-1][1] + 1) for x in range(1, 14)])
            elif game.timer > 10:
                game.timer = 0

        main_map = Map("9_lvl.tmx")
        play_background_music('9_lvl')
        all_sprites = pygame.sprite.Group()

        bullets = []

        game = Game(main_map, bullets, sprites_group=[all_sprites])
        game.camera.shift_y = 10

        game.events.extend([lava_spread, lava_kill_tanks])

        self.init_reasons_and_missions(game)
        game.missions = [self.stand_on_control_point]
        game.defeat_reasons = [self.player_are_dead]
        return game

    def init_lvl10_scene(self):
        play_background_music('10_lvl')
        player_moves = [get_player_coords()]
        time_for_explode = 150
        time_for_shoot = 30

        def lava_kill_tanks():
            for group in [game.uncontrolled_tanks,
                          game.controlled_tanks]:
                for tank in group:
                    if tank.get_position() in game.map.lava:
                        tank.destroy_the_tank(group)

        def explode_player_every_momenth():
            nonlocal time_for_explode
            nonlocal time_for_shoot
            time_for_explode -= 1
            if time_for_explode <= 0:
                if time_for_explode == 0:
                    play_sound(None, os.path.join(
                        SOUND_DIR, 'other', 'marker.mp3'))
                if len(player_moves) > 4 * 4:
                    time_for_shoot -= 1
                    rect = pygame.Rect(0, 0, player_moves[0][0] * TILE_SIZE,
                                       player_moves[0][1] * TILE_SIZE)
                    game.camera.apply(rect)
                    screen.blit(target_confirmed, (rect.width, rect.height))
                    if time_for_shoot == 0:
                        game.make_explode(*player_moves[0])
                        time_for_explode = 150
                        time_for_shoot = 30
                        screen.blit(target_confirmed, (rect.width, rect.height))
            else:
                if time_for_explode == 141:
                    play_sound(None, os.path.join(
                        SOUND_DIR, 'other', 'boss_load.mp3'))
                if time_for_explode == 45:
                    play_sound(None, os.path.join(
                        SOUND_DIR, 'other', 'boss_gun_raise.mp3'))
                player_moves.append((min(
                    42, get_player_coords()[0]), get_player_coords()[1]))
                if len(player_moves) > 5 * 4:
                    player_moves.pop(0)

                rect = pygame.Rect(0, 0, player_moves[0][0] * TILE_SIZE,
                                   player_moves[0][1] * TILE_SIZE)
                game.camera.apply(rect)
                screen.blit(target_search, (rect.width, rect.height))

        def open_doors():
            lock_cell = game.map.unbreak_tiles[1]
            if all([isinstance(game.map.map[1][7], Tank),
                    isinstance(game.map.map[20][7], Tank)]):
                game.map.map[10][15] = game.map.get_free_block(15, 10)
                game.map.map[11][15] = game.map.get_free_block(15, 11)
            else:
                game.map.map[10][15] = lock_cell
                game.map.map[11][15] = lock_cell

            if all(cell in game.map.free_tiles for cell in
                   sum([game.map.map[2][22:24], game.map.map[3][22:24],
                        game.map.map[6][30:32], game.map.map[7][30:32],
                        game.map.map[18][21:23], game.map.map[19][21:23],
                        game.map.map[21][29:31]], [])):
                game.map.map[10][36] = game.map.get_free_block(15, 10)
                game.map.map[11][36] = game.map.get_free_block(15, 11)
            if all(cell in game.map.free_tiles for cell in sum(
                    [game.map.map[0][51:55], game.map.map[1][51:55]], [])):
                for x in range(51, 56):
                    game.map.map[6][x] = game.map.get_free_block(51, 6)

            if all(cell in game.map.free_tiles for cell in sum(
                    [game.map.map[20][51:55], game.map.map[21][51:55]], [])):
                for x in range(51, 56):
                    game.map.map[15][x] = game.map.get_free_block(51, 15)

        def lock_control_points_first_chapter():
            lock_cell = game.map.unbreak_tiles[1]
            if all(cell in game.map.free_tiles for cell in sum(
                    [game.map.map[1][1:3], game.map.map[2][1:3],
                     game.map.map[1][11:13], game.map.map[2][11:13]], [])):
                game.map.map[1][6] = lock_cell
                game.map.map[1][8] = lock_cell
                game.map.map[2][7] = lock_cell

            if all(cell in game.map.free_tiles for cell in sum(
                    [game.map.map[19][1:3], game.map.map[20][1:3],
                     game.map.map[14][6:8], game.map.map[15][6:8]], [])):
                game.map.map[20][6] = lock_cell
                game.map.map[19][7] = lock_cell

        def shadow_chapter():
            if get_player_coords() in [(16, 10), (16, 11)]:
                for y in range(0, 22):
                    for x in range(0, 16):
                        if (x, y) not in game.map.shadow:
                            game.map.shadow.append((x, y))

            if get_player_coords() in [(37, 10), (37, 11)]:
                for y in range(0, 22):
                    for x in range(16, 34):
                        if (x, y) not in game.map.shadow:
                            game.map.shadow.append((x, y))

        def render_boss():
            rect = pygame.Rect(0, 0, 1720, 320)
            game.camera.apply(rect)
            screen.blit(boss_hull, (rect.w, rect.h))

        def final_explode():
            if boss_lifes_over():
                game.final_lvl = False
                game.cutscenes[0]['trigger'] = lambda arg1, arg2: True
                for y in range(7, 14, 2):
                    for x in range(48, 58, 2):
                        game.make_explode(x, y)

        main_map = Map("10_lvl.tmx")
        all_sprites = pygame.sprite.Group()

        bullets = []

        game = Game(main_map, bullets, sprites_group=[all_sprites])
        self.init_reasons_and_missions(game)
        game.parse_cutscenes_from_file('10_lvl')

        # Замещение воды на лаву, чтобы придать уровню зловещий вид
        for y in range(game.map.height):
            for x in range(game.map.width):
                type_of_tile = game.map.get_type_of_tile(x, y)
                if type_of_tile == 'free_lava':
                    game.map.lava.append((x, y))

        game.events.extend([render_boss, lava_kill_tanks,
                            explode_player_every_momenth,
                            lock_control_points_first_chapter,
                            shadow_chapter, open_doors, final_explode])

        boss_lifes_over = lambda: all(
            cell in game.map.free_tiles
            for cell in sum([game.map.map[7][51:56],
                             game.map.map[14][51:56]], []))

        game.missions = [lambda: len(game.cutscenes) == 0]
        game.defeat_reasons = [self.player_are_dead]
        return game


def show_highscore_board(players_from_local_game=None):
    # init fon
    fon = pygame.Surface((WINDOW_WIDTH * 1, WINDOW_HEIGHT * 0.7))
    fon.fill(pygame.Color((180, 180, 180)))
    black_box = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
    black_box.fill(pygame.Color((0, 0, 0)))
    screen.blit(black_box, ((WINDOW_WIDTH - black_box.get_width()) // 2,
                            (WINDOW_HEIGHT - black_box.get_height()) // 2))
    screen.blit(fon, ((WINDOW_WIDTH - fon.get_width()) // 2,
                      (WINDOW_HEIGHT - fon.get_height()) // 2))
    if players_from_local_game:
        scores = [(CONTROLLED_PLAYERS_DICT[tank.control_keys[SHOOT]]['name'], tank.kills)
                  for tank in players_from_local_game]
    else:
        user_info = load_user_info(True)
        scores = [(user, str(user_info[user]['high_score']))
                  for user in user_info]
    scores = reversed(sorted(scores, key=lambda x: x[1]))
    labels = [': '.join((i[0].ljust(10, '-'), str(i[1])))
              for i in scores]
    draw_the_dialog_background('РЕКОРДЫ')
    for y in range(250, 500, 50):
        if labels:
            string_score = labels.pop(0)
        else:
            string_score = ''
        draw_the_dialog_background(string_score, y=y)


def calculate_highscore(end_game, begin_game):
    if not isinstance(end_game, Game) and not isinstance(begin_game, Game):
        lvl_score = len([tank for tank in begin_game if tank.team == 'black']) - \
                    len([tank for tank in end_game if tank.team == 'black'])
    else:
        lvl_score = len([tank for tank in
                         begin_game.uncontrolled_tanks if tank.team == 'black']) - \
                    len([tank for tank in
                         end_game.uncontrolled_tanks if tank.team == 'black'])
    return lvl_score


def draw_the_dialog_background(message, y=150):
    # init title
    size = 60
    if len(message) > 10:
        size //= 2
    font = pygame.font.Font(f'{FONTS_DIR}/Thintel.ttf', size)
    text = font.render(message, True, COLOR_TEXT)
    text_x = (WINDOW_WIDTH - text.get_width()) // 2
    text_y = y
    screen.blit(text, (text_x, text_y))


def show_info_menu():
    # init fon
    fon = pygame.Surface((WINDOW_WIDTH * 1, WINDOW_HEIGHT * 0.70))
    black_box = pygame.Surface((WINDOW_WIDTH * 0.7, WINDOW_HEIGHT * 0.85))
    fon.fill(pygame.Color((180, 180, 180)))
    black_box.fill(pygame.Color((0, 0, 0)))
    screen.blit(black_box, ((WINDOW_WIDTH - black_box.get_width()) // 2,
                            (WINDOW_HEIGHT - black_box.get_height()) // 2))
    screen.blit(fon, ((WINDOW_WIDTH - fon.get_width()) // 2,
                      (WINDOW_HEIGHT - fon.get_height()) // 2))

    labels = ('W, S - кнопки движения корпуса.',
              'A, D - кнопки поворота корпуса.',
              'Q, E - кнопки поворота башни.',
              'R - кнопка стрельбы.',
              'F12 - скриншот игры. Лежит в папке data/screenshots',
              'Кнопки "+" и "-" контролируют громкость звука во время игры',
              'Кнопки "PGUP" и "PGDOWN" контролирует громкость музыки',
              'В игре есть система очков.',
              'За каждого мертвого врага тебе дают одно очко.',
              'Учти, что возрождающиеся танки идут не в счет',
              '',
              'Чтобы выиграть - выполняй приказы. Отбой!', '')
    draw_the_dialog_background('КАК ИГРАТЬ')
    for y in range(200, 500, 25):
        draw_the_dialog_background(
            labels[min((y // 25) - (200 // 25), len(labels) - 1)], y=y)


class Informer:
    def __init__(self):
        self.info_list = []

    def add_info(self, text, image=None):
        args = {'text': text,
                'image': image,
                'timer': 10}
        self.info_list.append(args)

    def show_toast_info(self):
        for info in self.info_list:
            text = info['text']
            image = info['image']

            font = pygame.font.Font(f'{FONTS_DIR}/Thintel.ttf', 20)
            black_box = pygame.Surface((WINDOW_WIDTH, 20))
            black_box.fill((0, 0, 0))
            render = font.render(text, False, (255, 255, 255))

            screen.blit(black_box, (0, WINDOW_HEIGHT - black_box.get_height()))

            pos_x, pos_y = WINDOW_WIDTH // 2 - render.get_width() // 2, \
                           WINDOW_HEIGHT - black_box.get_height()
            if image:
                image = pygame.transform.scale(image, (20, 20))
                image_pos_x = (WINDOW_WIDTH - image.get_width() - render.get_width()) // 2
                pos_x = (WINDOW_WIDTH + image.get_width() - render.get_width()) // 2
                screen.blit(image, (image_pos_x, pos_y))

            screen.blit(render, (pos_x, pos_y))
            info['timer'] -= 1
        self.info_list = [i for i in self.info_list if i['timer'] > 0]


def lobby_for_local_game():
    font = pygame.font.Font(f'{FONTS_DIR}/Thintel.ttf', 20)
    players_controls = []

    while True:
        for event in pygame.event.get():
            black_box = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
            screen.blit(black_box, (0, 0))

            # Отрисовка клавиш для управления танком
            for shoot_key in CONTROLLED_PLAYERS_DICT:
                control_set = CONTROLLED_PLAYERS_DICT[shoot_key]['control_set']
                if control_set in players_controls:
                    control_sprite = CONTROLLED_PLAYERS_DICT[shoot_key]['all_sprite']
                else:
                    control_sprite = CONTROLLED_PLAYERS_DICT[shoot_key]['shoot_sprite']
                x, y = CONTROLLED_PLAYERS_DICT[shoot_key]['sprite_coord'](control_sprite)
                screen.blit(control_sprite, (x, y))

            if event.type == pygame.KEYDOWN:
                for shoot_key in CONTROLLED_PLAYERS_DICT:
                    if event.key == shoot_key:
                        control_set = CONTROLLED_PLAYERS_DICT[shoot_key]['control_set']
                        if control_set not in players_controls:
                            play_sound(None, os.path.join(SOUND_DIR, 'menu', 'player_join.mp3'))
                            players_controls.append(control_set)
                        else:
                            play_sound(None, os.path.join(SOUND_DIR, 'menu', 'player_leave.mp3'))
                            players_controls.remove(control_set)

                if event.key == pygame.K_ESCAPE:
                    return
                if event.key == pygame.K_SPACE:
                    if len(players_controls) > 1:
                        return LevelLoader().init_local_game(players_controls)

            draw_the_dialog_background('Правила просты - не мухлевать и по-честному получать угар',
                                       WINDOW_HEIGHT // 2)
            draw_the_dialog_background('Чтобы начать мясорубу, нажмите ПРОБЕЛ', WINDOW_HEIGHT - 100)

        pygame.display.flip()
        clock.tick(FPS)


def show_confirmation_dialog(manager, action_long_desc):
    dialog_size = (260, 200)
    confirmation_dialog = pygame_gui.windows.UIConfirmationDialog(
        rect=pygame.Rect(
            ((WINDOW_WIDTH - dialog_size[0]) // 2,
             (WINDOW_HEIGHT - dialog_size[1]) // 2),
            dialog_size),
        manager=manager,
        window_title='Подтвеждение',
        action_long_desc=action_long_desc,
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


def show_cutscene(surface, replica):
    # Рисование черных полос:
    dark_rect = pygame.Surface((WINDOW_WIDTH, 150))
    dark_rect.fill(pygame.Color(0, 0, 0))
    surface.blit(dark_rect, (0, 79 - 150))
    surface.blit(dark_rect, (0, 450))
    if replica:
        character = replica[0]
        image = CHARACTERS_DICT.get(replica[0], CHARACTERS_DICT[None])
        message = replica[1]

        surface.blit(image, (60, 410))

        # Показ сообщения:
        character_font = pygame.font.Font(f'{FONTS_DIR}/Thintel.ttf', 60)
        character_text = character_font.render(character, True, (255, 255, 255))

        surface.blit(character_text, (90 + image.get_width(), 410 + image.get_height() // 2))

        message_font = pygame.font.Font(f'{FONTS_DIR}/Thintel.ttf', 30)
        text_y = 510
        if isinstance(message, list):
            for sub_message in message:
                message_text = message_font.render(sub_message, True, (255, 255, 255))
                surface.blit(message_text, (65, text_y))
                text_y += message_text.get_height()
        else:
            message_text = message_font.render(message, True, (255, 255, 255))
            surface.blit(message_text, (65, text_y))
        skip_text = message_font.render('>ПРОБЕЛ', True, (255, 255, 255))
        forward_skip_text = message_font.render('>>>CTRL + ПРОБЕЛ', True, (255, 255, 255))
        surface.blit(skip_text, (WINDOW_WIDTH - skip_text.get_width() - 10,
                                 WINDOW_HEIGHT - skip_text.get_height() - 10))
        surface.blit(forward_skip_text, (WINDOW_WIDTH - skip_text.get_width() -
                                         forward_skip_text.get_width() - 50,
                                         WINDOW_HEIGHT - skip_text.get_height() - 10))


def start_screen():
    play_background_music('menu')
    name_entry_line.set_text(load_current_user())
    refresh_select_box_item_list()

    def new_game():
        refresh_current_score_for_user(-1)
        save_game(1)
        return getattr(LevelLoader(), f'init_lvl{1}_scene')()

    def draw_the_main_background():
        # init fon
        fon = pygame.Surface(WINDOW_SIZE)
        fon.fill(pygame.Color((0, 0, 0)))
        screen.blit(fon, (0, 0))

        # init title
        y = title_text_y
        for text in title_text:
            screen.blit(text, (
                (WINDOW_WIDTH - text.get_width()) // 2, y))
            y += text.get_height()

    draw_the_main_background()
    do_show_info = False
    do_show_scores = False
    conf_dialog = None
    func_to_confirm = None
    while True:
        time_delta = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_user_info()
                terminate()  # exit
            if event.type == pygame.MOUSEBUTTONDOWN:
                do_show_info = False
                do_show_scores = False
            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_BUTTON_ON_HOVERED:
                    volume = load_user_info()[load_current_user()]['sound_value'] / 100
                    choice_of_the_options.set_volume(volume)
                    choice_of_the_options.play()
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    volume = load_user_info()[load_current_user()]['sound_value'] / 100
                    selecting_of_the_options.set_volume(volume)
                    selecting_of_the_options.play()
                    if event.ui_element == \
                            start_menu_btn_dict['CONTINUE']:
                        return getattr(LevelLoader(),
                                       f'init_lvl{load_saved_game()}_scene')()
                    elif event.ui_element == start_menu_btn_dict['NEW GAME']:
                        if load_saved_game() > 1:
                            conf_dialog = show_confirmation_dialog(
                                main_menu_manager,
                                'Найдена сохраненная игра. ' +
                                'Вы уверены, что хотите начать сначала?')
                            func_to_confirm = new_game
                        else:
                            return new_game()
                    elif event.ui_element == start_menu_btn_dict['LOCAL GAME']:
                        result = lobby_for_local_game()
                        if result != None:
                            return result
                    elif event.ui_element == start_menu_btn_dict['HIGH SCORES']:
                        do_show_scores = True
                    elif event.ui_element == start_menu_btn_dict['HOW TO PLAY']:
                        do_show_info = True
                    elif event.ui_element == start_menu_btn_dict['EXIT']:
                        save_user_info()
                        conf_dialog = show_confirmation_dialog(
                            main_menu_manager, 'Вы уверены, что хотите выйти?')
                        func_to_confirm = terminate
                    elif event.ui_element == accept_name_btn:
                        rename_current_user()
                    elif event.ui_element == sound_btn:
                        sound_value_slider.show()
                        music_value_slider.hide()
                    elif event.ui_element == music_btn:
                        sound_value_slider.hide()
                        music_value_slider.show()
                    elif event.ui_element == accept_user_btn:
                        user = select_box.get_single_selection()
                        if user:
                            save_current_user(user)
                    elif event.ui_element == remove_user_btn:
                        user = select_box.get_single_selection()
                        if len(load_user_info(True)) > 1 and user:
                            conf_dialog = show_confirmation_dialog(
                                main_menu_manager, 'Внимание, весь прогресс этого пользователя'
                                                   ' будет удален!')
                            func_to_confirm = delete_user
                    elif event.ui_element == add_user_btn:
                        users = (load_user_info(True).keys())
                        user = choice(('TankLover', 'СуПеРбЕс', 'Связист Игорь', 'Юзер!'))
                        if user in users:
                            user = ''.join(choice(
                                ('1', '2', '3', '4', '5', '6', '7', '8', '9', '0')) for _
                                           in range(15))
                        save_current_user(user)
                        save_user_info()
                        refresh_select_box_item_list()

            if conf_dialog:
                if conf_dialog.process_event(event):
                    if func_to_confirm:
                        rect = conf_dialog.confirm_button.get_abs_rect()
                        x, y, w, h = rect.x, rect.y, rect.w, rect.h
                        mouse_x, mouse_y = event.pos
                        if mouse_x in range(x, x + w) and \
                                mouse_y in range(y, y + h):
                            if func_to_confirm != delete_user:
                                return func_to_confirm()
                            else:
                                func_to_confirm()

            if pygame.mouse.get_pos()[1] < 525:
                if sound_value_slider.visible:
                    sound_value_slider.hide()
                if music_value_slider.visible:
                    music_value_slider.hide()
            sound_btn.set_image(
                sound_on_img if sound_value_slider.current_value else sound_off_img)
            music_btn.set_image(
                music_on_img if music_value_slider.current_value else music_off_img)
            accept_user_btn.set_image(accept_user)
            remove_user_btn.set_image(remove_user)
            add_user_btn.set_image(add_user)

            main_menu_manager.process_events(event)

        # Apply all settings in real time
        save_user_info()
        load_user_info()
        main_menu_manager.update(time_delta)

        draw_the_main_background()

        main_menu_manager.draw_ui(screen)

        if do_show_scores:
            show_highscore_board()
        if do_show_info:
            show_info_menu()

        pygame.display.flip()
        clock.tick(FPS)


def show_titles():
    play_background_music('titles')
    file = open(f'{CUTSCENES_DIR}/titles', 'r', encoding='utf-8')
    labels = [line.strip() for line in file]
    file.close()

    for timer in range(0, 3700, 2):
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    return start_screen()
        screen.fill('#000000')
        for y in range(WINDOW_HEIGHT, 5000, 50):
            draw_the_dialog_background(
                labels[min((y // 50 - WINDOW_HEIGHT // 50) - 1,
                           len(labels) - 1)], y=y - timer)

        pygame.display.flip()
        clock.tick(FPS)
    return start_screen()


def main():
    global score
    lvl_count = 1
    lvl_loader = LevelLoader()
    skiping_cutscene = False
    informer = Informer()

    # Main game loop:
    running = True
    load_user_info()
    game = start_screen()
    is_paused = False
    while running:
        # Loop of receiving and processing events:
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
                            volume = load_user_info()[load_current_user()]['sound_value'] / 100
                            back_to_menu.set_volume(volume)
                            back_to_menu.play()
                            game = start_screen()
                            break
            if event.type == pygame.KEYDOWN:
                # Контроль громкости
                if event.key == pygame.K_PAGEDOWN:
                    value = max(0, music_value_slider.current_value - 5)
                    music_value_slider.set_current_value(value)
                    coords = get_player_coords()
                    save_user_info(coords)
                    informer.add_info(str(value), music_on_img)
                elif event.key == pygame.K_PAGEUP:
                    value = min(100, music_value_slider.current_value + 5)
                    music_value_slider.set_current_value(value)
                    coords = get_player_coords()
                    save_user_info(coords)
                    informer.add_info(str(value), music_on_img)
                elif event.key in (pygame.K_PLUS, pygame.K_EQUALS):
                    value = min(100, sound_value_slider.current_value + 5)
                    sound_value_slider.set_current_value(value)
                    coords = get_player_coords()
                    save_user_info(coords)
                    informer.add_info(str(value), sound_on_img)
                elif event.key == pygame.K_MINUS:
                    value = max(0, sound_value_slider.current_value - 5)
                    sound_value_slider.set_current_value(value)
                    coords = get_player_coords()
                    save_user_info(coords)
                    informer.add_info(str(value), sound_on_img)

                # Завершение игры
                elif event.key and game.end_game_and_return_status(
                        screen, return_status=True) and game.timer > 15:
                    status = game.end_game_and_return_status(
                        screen, return_status=True)
                    if status == WIN:
                        temp_score = calculate_highscore(game, getattr(
                            lvl_loader, f'init_lvl{lvl_count}_scene')())
                        refresh_current_score_for_user(temp_score)
                        if lvl_count != load_saved_game():
                            lvl_count = load_saved_game()
                        lvl_count += 1
                        save_game(min(lvl_count, 10))
                    elif status == LOCAL_GAME_FINISHED:
                        game = start_screen()
                        break
                    if lvl_count == 11:
                        show_titles()
                        game = start_screen()
                    else:
                        game = getattr(lvl_loader, f'init_lvl{lvl_count}_scene')()
                elif event.key == pygame.K_SPACE and \
                        game.is_active_cutscene and \
                        not skiping_cutscene:
                    if pygame.key.get_mods() & pygame.KMOD_CTRL:
                        skiping_cutscene = True
                    else:
                        game.timer = 1

                elif event.key == pygame.K_F12:
                    try:
                        now = ''.join([elem for elem in str(datetime.now()) if elem.isdigit()])
                        filename = f'screenshot_{now}.jpg'
                        screenshot_path = os.path.join(os.getcwd(), 'data', 'screenshots',
                                                       filename)
                        pygame.image.save(screen.copy(), screenshot_path)
                        informer.add_info('Скриншот сделан', accept_user)
                    except Exception:
                        informer.add_info('Скриншот не сделан, ошибка программы', remove_user)
                elif event.key == pygame.K_ESCAPE and not is_paused:
                    show_game_message(screen, 'PAUSE', 'press Enter to exit')
                    is_paused = True

        if skiping_cutscene:
            game.timer = 0

        if not is_paused:
            game.render(screen)
            if not game.is_active_cutscene:
                if game.end_game_and_return_status(screen) is None:
                    skiping_cutscene = False
                    game.make_events()
                    game.update_controlled_tanks()
                    game.update_uncontrolled_tanks()
            game.show_cutscenes()
        informer.show_toast_info()
        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()


if __name__ == "__main__":
    init_user_info()
    main()
