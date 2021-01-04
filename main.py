import os
import sys
import pygame
from queue import Queue
from random import random, choice
import pytmx
from copy import deepcopy
from sprites import *

WINDOW_SIZE = WINDOW_WIDTH, WINDOW_HEIGHT = 600, 600
TILE_SIZE = 40
FPS = 15
MAPS_DIR = "maps"

# Control
FORWARD = 91
BACK = 92
TURN_RIGHT = 93
TURN_LEFT = 94
TURN_RIGHT_TURRET = 95
TURN_LEFT_TURRET = 96
SHOOT = 97

# Control keys dicts
CONTROL_KEYS_V1 = \
    {FORWARD: pygame.K_w, BACK: pygame.K_s,
     TURN_RIGHT: pygame.K_d, TURN_LEFT: pygame.K_a,
     TURN_RIGHT_TURRET: pygame.K_e, TURN_LEFT_TURRET: pygame.K_q,
     SHOOT: pygame.K_r}
CONTROL_KEYS_V2 = \
    {FORWARD: pygame.K_g, BACK: pygame.K_b,
     TURN_RIGHT: pygame.K_n, TURN_LEFT: pygame.K_v,
     TURN_RIGHT_TURRET: pygame.K_h, TURN_LEFT_TURRET: pygame.K_f,
     SHOOT: pygame.K_c}
CONTROL_KEYS_V3 = \
    {FORWARD: pygame.K_i, BACK: pygame.K_k,
     TURN_RIGHT: pygame.K_j, TURN_LEFT: pygame.K_l,
     TURN_RIGHT_TURRET: pygame.K_u, TURN_LEFT_TURRET: pygame.K_o,
     SHOOT: pygame.K_p}
CONTROL_KEYS_V4 = \
    {FORWARD: pygame.K_UP, BACK: pygame.K_DOWN,
     TURN_RIGHT: pygame.K_RIGHT, TURN_LEFT: pygame.K_LEFT,
     TURN_RIGHT_TURRET: 44, TURN_LEFT_TURRET: 46, SHOOT: 47}

DIRECTION_MOVE_BY_ANGLE = {0: (0, -0.9), 90: (-0.9, 0), 180: (0, 0.9), 270: (0.9, 0)}


def get_player_coords():
    with open('player_coords.txt') as file:
        coords = eval(file.readline())
        file.close()
        return coords


def set_player_coords(coords):
    with open('player_coords.txt', 'w+') as file:
        file.seek(0)
        file.write(str(coords))
        file.close()


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


class Map:
    def __init__(self, filename):
        self.map = []
        self.tiled_map = TiledMap(filename)
        for y in range(self.tiled_map.tmx_data.height):
            self.map.append([self.tiled_map.get_tile_id(x, y) for x in range(self.tiled_map.tmx_data.width)])

        self.height = len(self.map)
        self.width = len(self.map[0])
        self.tile_size = TILE_SIZE

        self.camera = Camera(self.width, self.height)

        # Инициализация разрушаемых/неразрушаемых/свободных и других блоков через TiledMap
        check_prop = self.tiled_map.tmx_data.get_tile_properties
        self.free_tiles = []
        self.break_tiles = []
        self.unbreak_tiles = []
        for y in range(self.height):
            for x in range(self.width):
                type_of_tile = check_prop(x, y, 0)['type']
                id_of_tyle = self.tiled_map.get_tile_id(x, y)
                if 'free' in type_of_tile and id_of_tyle not in self.free_tiles:
                    self.free_tiles.append(id_of_tyle)
                elif type_of_tile == 'break' and id_of_tyle not in self.break_tiles:
                    self.break_tiles.append(id_of_tyle)
                elif type_of_tile == 'unbreak' and id_of_tyle not in self.unbreak_tiles:
                    self.unbreak_tiles.append(id_of_tyle)
        self.shadow = []

    def render(self, screen):
        screen.fill('#000000')
        ti = self.tiled_map.tmx_data.get_tile_image_by_gid
        for layer in self.tiled_map.tmx_data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                for x, y, gid in layer:
                    gid = self.map[y][x]
                    tank_stand_on = False
                    # Если на блоке стоит танк, то блок под ним отрисовывается первым свободным из списка
                    if not isinstance(gid, int):
                        gid = self.get_free_block(x, y)
                        tank_stand_on = True

                    tile = ti(gid)
                    if tile:
                        tile_rect = pygame.Rect(0, 0, x * self.tiled_map.tmx_data.tilewidth,
                                                y * self.tiled_map.tmx_data.tileheight)
                        self.camera.apply(tile_rect)
                        screen.blit(tile, (tile_rect.width, tile_rect.height))

                        if tank_stand_on:
                            screen.blit(self.map[y][x].image, (tile_rect.width, tile_rect.height))
                            screen.blit(self.map[y][x].tank_turret.image, (tile_rect.width, tile_rect.height))
                            if self.map[y][x].respawn:
                                if self.map[y][x].respawn_time <= 90:
                                    self.map[y][x] = self.get_free_block(x, y)

                        if (x, y) in self.shadow:
                            shadow = pygame.Surface((self.tiled_map.tmx_data.tilewidth,
                                                     self.tiled_map.tmx_data.tileheight))
                            shadow.fill(pygame.Color(0, 0, 0))
                            shadow.set_alpha(99)
                            screen.blit(shadow, (tile_rect.width, tile_rect.height))

    def get_tile_id(self, position):
        return self.map[position[1]][position[0]]

    def get_type_of_tile(self, x, y):
        check_prop = self.tiled_map.tmx_data.get_tile_properties
        type_of_tile = check_prop(x, y, 0)['type']
        return type_of_tile

    def get_free_block(self, x, y):
        id_of_free_block = self.tiled_map.tmx_data.get_tile_gid(x, y, 0)
        if id_of_free_block not in self.free_tiles:
            id_of_free_block = self.free_tiles[0]
        return id_of_free_block

    def is_free(self, position):
        return self.get_tile_id(position) in self.free_tiles and position not in self.shadow

    def find_player(self):
        for y in range(self.height):
            for x in range(self.width):
                if self.map[y][x].__repr__() == 'Player':
                    return x, y

    def give_player_list_and_tanks_list_and_destinations(self, sprite_group):
        destinations = dict()
        player_list = []
        tank_list = []
        for tile_object in self.tiled_map.tmx_data.objects:
            if tile_object.name == 'Shadow':
                x, y, w, h = int(tile_object.x // TILE_SIZE), int(tile_object.y // TILE_SIZE),\
                             int(tile_object.width // TILE_SIZE), int(tile_object.height // TILE_SIZE)
                # print('shadow:', x, y, w, h)
                for y_step in range(y, y + h):
                    for x_step in range(x, x + w):
                        # print((x_step, y_step))
                        self.shadow.append((x_step, y_step))

            else:
                rotate_turret, rotate_hull = tile_object.properties['rotate_turret'],\
                                             tile_object.properties['rotate_hull']
                destination = tile_object.properties['destination']
                respawn = tile_object.properties.get('respawn', False)
                x, y = int(tile_object.x // TILE_SIZE), int(tile_object.y // TILE_SIZE)
                if 'Player' in tile_object.name:
                    player_list.append(Player((x, y), rotate_turret=rotate_turret,
                                          rotate_hull=rotate_hull, group=sprite_group, respawn=respawn))
                elif 'Tank' in tile_object.name:
                    tank_list.append(Tank((x, y), rotate_turret=rotate_turret,
                                          rotate_hull=rotate_hull, group=sprite_group, respawn=respawn))
                elif 'Beast' in tile_object.name:
                    tank_list.append(Beast((x, y), rotate_turret=rotate_turret,
                                           rotate_hull=rotate_hull, group=sprite_group, respawn=respawn))
                elif 'Heavy' in tile_object.name:
                    tank_list.append(Heavy((x, y), rotate_turret=rotate_turret,
                                           rotate_hull=rotate_hull, group=sprite_group, respawn=respawn))
                elif 'Allied' in tile_object.name:
                    tank_list.append(Allied((x, y), rotate_turret=rotate_turret,
                                           rotate_hull=rotate_hull, group=sprite_group, respawn=respawn))
                if destination == 'self':
                    destinations[tank_list[-1]] = None
                elif destination == 'player':
                    destinations[tank_list[-1]] = get_player_coords
                elif 'detect' in destination:
                    def detect_func(range_x, range_y):
                        return get_player_coords() if (
                                    get_player_coords()[0] in range_x and get_player_coords()[1] in range_y) else None

                    ranges = eval(destination[7:])
                    destinations[tank_list[-1]] = (detect_func, ranges)
                elif 'pos' in destination:
                    destinations[tank_list[-1]] = eval(destination[len('pos '):])

        return player_list, tank_list, destinations


class TiledMap:
    def __init__(self, filename):
        tm = pytmx.load_pygame(f"{MAPS_DIR}/{filename}")
        self.width = tm.width * tm.tilewidth
        self.height = tm.height * tm.tileheight
        self.tmx_data = tm

    def render(self, surface):
        self.tmx_data.reload_images()
        ti = self.tmx_data.get_tile_image_by_gid
        for layer in self.tmx_data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                for x, y, gid in layer:
                    tile = ti(gid)
                    if tile:
                        surface.blit(tile, (x * self.tmx_data.tilewidth, y * self.tmx_data.tileheight))

    def get_tile_id(self, x, y):
        return int(self.tmx_data.get_tile_gid(x, y, 0))

    def make_map(self):
        temp_surface = pygame.Surface((self.width, self.height))
        self.render(temp_surface)
        return temp_surface


class Game:
    def __init__(self, map, bullets, clock, sprites_group=list()):
        self.map = map
        self.clock = clock
        self.camera = self.map.camera

        # Инициализация миссий и "причин для поражения"
        self.defeat_reasons = []
        self.missions = []

        # Группы танков
        self.sprites_group = sprites_group        
        self.controlled_tanks, self.uncontrolled_tanks,\
        self.destinations = (self.map.give_player_list_and_tanks_list_and_destinations(sprites_group[0]))

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
            if bullet_x not in range(0, self.map.width) or bullet_y not in range(0, self.map.height):
                del self.bullets[self.bullets.index(bullet)]
                continue
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
                        self.make_explode(bullet_x, bullet_y)

    def make_explode(self, x, y):
        self.map.map[y][x] = self.map.get_free_block(x, y)
        for angle in range(0, 271, 90):
            self.bullets.append(Bullet(
                (x, y), angle, self.controlled_tanks[0].dict_id_bullets[0]))

    def update_controlled_tanks(self):
        for tank in self.controlled_tanks:
            tank.update_timers(self.clock)
            if tank.is_crashed:
                continue
            unpack_player_coords = self.map.find_player()
            if not unpack_player_coords:
                cur_x, cur_y = next_x, next_y = tank.get_position()
            else:
                cur_x, cur_y = next_x, next_y = unpack_player_coords

            rotate_turret, rotate_hull = tank.get_rotate()
            direction_move = [round(i) for i in DIRECTION_MOVE_BY_ANGLE[rotate_hull]]
            self.map.map[cur_y][cur_x] = tank

            if pygame.key.get_pressed()[tank.control_keys[FORWARD]]:
                next_x += direction_move[0]
                next_y += direction_move[1]
                if self.map.is_free((next_x, next_y)):
                    if tank.move_forward():
                        self.map.map[cur_y][cur_x] = self.map.get_free_block(cur_x, cur_y)
                        self.map.map[next_y][next_x] = tank
            elif pygame.key.get_pressed()[tank.control_keys[BACK]]:
                next_x -= direction_move[0]
                next_y -= direction_move[1]
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
            set_player_coords(tank.get_position())

    def update_uncontrolled_tanks(self):
        for tank in self.uncontrolled_tanks:
            tank.update_timers(self.clock)
            if tank.is_crashed:
                continue

            destination = self.destinations[tank]
            # Для динамических целей, которые требуют обновления данных о себе
            if callable(destination):
                destination = destination()
            # Для "скриптованных" целей. Срабатывают, когда та переходит черту
            elif isinstance(destination, tuple):
                if callable(destination[0]):
                    destination = destination[0](*destination[1])
            # нахождение цели
            if destination != None:
                path, status = self.find_path(tank.get_position(), destination)

            # Поскольку бот соображает слишком быстро, задержка через рандом должна снизить его скорость
            if random() > 1 - tank.accuracy:
                self.calculate_uncontrolled_tank_turret(tank)

            if random() > 1 - tank.speed:
                if destination != None:
                    if len(path) > 3:
                        self.calculate_uncontrolled_tank_move(path, destination, tank)
            else:
                x, y = tank.get_position()
                self.map.map[y][x] = tank

    def calculate_uncontrolled_tank_turret(self, tank):
        def break_check(cell):
            if cell not in self.map.unbreak_tiles:
                if isinstance(cell, Tank):
                    if cell.__repr__() == 'Player' and tank.team == 'green':
                        return True
                return False
            return True

        cur_x, cur_y = tank.get_position()
        rotate_turret = tank.get_rotate()[0]

        down_y_axis = [self.map.map[y][cur_x] for y in range(cur_y, len(self.map.map))]
        up_y_axis = [self.map.map[y][cur_x] for y in range(cur_y, 0, -1)]
        left_x_axis = [self.map.map[cur_y][x] for x in range(cur_x, 0, -1)]
        right_x_axis = [self.map.map[cur_y][x] for x in range(cur_x, len(self.map.map[0]))]

        for cell in left_x_axis:  # 90
            if break_check(cell):
                break
            if isinstance(cell, Tank):
                if cell.team != tank.team:
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
            if break_check(cell):
                break
            if isinstance(cell, Tank):
                if cell.team != tank.team:
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
            if break_check(cell):
                break
            if isinstance(cell, Tank):
                if cell.team != tank.team:
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
            if break_check(cell):
                break
            if isinstance(cell, Tank):
                if cell.team != tank.team:
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
        cur_x, cur_y = next_x, next_y = tank.get_position()
        rotate_hull = tank.get_rotate()[1]
        next_step = path[2]
        direction_move = self.calculate_direction(tank.get_position(), next_step)
        next_x += direction_move[0]
        next_y += direction_move[1]
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


def show_message(screen, message):
    font = pygame.font.Font(None, 50)
    text = font.render(message, True, (50, 70, 0))
    text_x = WINDOW_WIDTH // 2 - text.get_width() // 2
    text_y = WINDOW_HEIGHT // 2 - text.get_height() // 2
    text_w = text.get_width()
    text_h = text.get_height()
    pygame.draw.rect(screen, (200, 150, 50), (text_x - 10, text_y - 10,
                                              text_w + 20, text_h + 20))
    screen.blit(text, (text_x, text_y))


class LevelLoader:
    def init_reasons_and_missions(self, game):
        self.stand_on_control_point = lambda: game.map.get_type_of_tile(get_player_coords()[0],
                                                           get_player_coords()[1]) == 'free_control_point'

        self.all_bots_are_dead = lambda: len(game.uncontrolled_tanks) == 0
        self.player_are_dead = lambda: game.controlled_tanks[0].is_crashed

    def init_lvl1_scene(self, clock):
        # Формирование кадра(команды рисования на холсте):
        main_map = Map("1_lvl.tmx")
        all_sprites = pygame.sprite.Group()  # создадим группу, содержащую все спрайты        

        bullets = []
        game = Game(main_map, bullets, clock, sprites_group=[all_sprites])

        self.init_reasons_and_missions(game)
        game.missions = [self.all_bots_are_dead]
        game.defeat_reasons = [self.player_are_dead]
        return game

    def init_lvl2_scene(self, clock):
        # Формирование кадра(команды рисования на холсте):
        main_map = Map("2_lvl.tmx")
        all_sprites = pygame.sprite.Group()  # создадим группу, содержащую все спрайты

        bullets = []

        game = Game(main_map, bullets, clock, sprites_group=[all_sprites])

        self.init_reasons_and_missions(game)
        game.missions = [lambda: game.map.is_free((38, 9))]
        game.defeat_reasons = [self.player_are_dead, lambda: game.map.is_free((1, 9))]
        return game

    def init_lvl3_scene(self, clock):
        # Формирование кадра(команды рисования на холсте):
        main_map = Map("3_lvl.tmx")
        all_sprites = pygame.sprite.Group()  # создадим группу, содержащую все спрайты

        bullets = []

        game = Game(main_map, bullets, clock, sprites_group=[all_sprites])

        self.init_reasons_and_missions(game)
        game.missions = [lambda: len(game.uncontrolled_tanks) == 0]
        game.defeat_reasons = [lambda: game.controlled_tanks[0].is_crashed]
        return game

    def init_lvl4_scene(self, clock):
        # Формирование кадра(команды рисования на холсте):
        main_map = Map("4_lvl.tmx")
        all_sprites = pygame.sprite.Group()  # создадим группу, содержащую все спрайты

        bullets = []

        game = Game(main_map, bullets, clock, sprites_group=[all_sprites])

        self.init_reasons_and_missions(game)
        game.missions = []
        game.defeat_reasons = [lambda: game.controlled_tanks[0].is_crashed]
        return game

    def init_lvl5_scene(self, clock):
        # Формирование кадра(команды рисования на холсте):
        main_map = Map("5_lvl.tmx")
        all_sprites = pygame.sprite.Group()  # создадим группу, содержащую все спрайты

        bullets = []

        game = Game(main_map, bullets, clock, sprites_group=[all_sprites])

        self.init_reasons_and_missions(game)
        game.missions = [self.stand_on_control_point]
        game.defeat_reasons = [self.player_are_dead]
        return game

    def init_lvl6_scene(self, clock):
        # Формирование кадра(команды рисования на холсте):
        main_map = Map("6_lvl.tmx")
        all_sprites = pygame.sprite.Group()  # создадим группу, содержащую все спрайты

        bullets = []

        game = Game(main_map, bullets, clock, sprites_group=[all_sprites])

        self.init_reasons_and_missions(game)
        game.missions = [self.stand_on_control_point]
        game.defeat_reasons = [self.player_are_dead]
        return game

    def init_lvl7_scene(self, clock):
        # Формирование кадра(команды рисования на холсте):
        main_map = Map("7_lvl.tmx")
        all_sprites = pygame.sprite.Group()  # создадим группу, содержащую все спрайты

        bullets = []

        game = Game(main_map, bullets, clock, sprites_group=[all_sprites])

        self.init_reasons_and_missions(game)
        game.missions = [self.stand_on_control_point]
        game.defeat_reasons = [self.player_are_dead]
        return game


def main():

    pygame.display.set_caption("TANK BATTLES")

    lvl_loader = LevelLoader()
    lvl_count = 1

    # Главный игровой цикл:
    clock = pygame.time.Clock()
    game = lvl_loader.init_lvl1_scene(clock)

    running = True
    while running:
        # Цикл приема и обработки сообщений:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    lvl_count += 1
                    if lvl_count > 10:
                        lvl_count = 1
                    game = getattr(lvl_loader, f'init_lvl{lvl_count}_scene')(clock)
                elif event.key == pygame.K_h:
                    game.controlled_tanks[0].health = 999
            # ...

        if game.end_count == 5:
            pygame.time.delay(3000)
            if game.end_game_and_return_status(screen) == 'win':
                lvl_count += 1
            game = getattr(lvl_loader, f'init_lvl{lvl_count}_scene')(clock)

        game.render(screen)
        game.update_controlled_tanks()
        game.update_uncontrolled_tanks()
        game.end_game_and_return_status(screen)

        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()


if __name__ == "__main__":
    main()
