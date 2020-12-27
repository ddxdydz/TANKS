import os
import sys
import pygame
from queue import Queue
from random import random, choice
import pytmx

WINDOW_SIZE = WINDOW_WIDTH, WINDOW_HEIGHT = 600, 600
TILE_SIZE = 40
FPS = 15
MAPS_DIR = "maps"
player_coords = (0, 0)

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

DIRECTION_MOVE_BY_ANGLE = {0: (0, -1), 90: (-1, 0), 180: (0, 1), 270: (1, 0)}


def get_player_coords():
    return player_coords


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
        for y in range(self.height):
            for x in range(self.width):
                type_of_tile = check_prop(x, y, 0)['type']
                id_of_tyle = self.tiled_map.get_tile_id(x, y)
                if type_of_tile == 'free' and id_of_tyle not in self.free_tiles:
                    self.free_tiles.append(id_of_tyle)
                elif type_of_tile == 'break' and id_of_tyle not in self.break_tiles:
                    self.break_tiles.append(id_of_tyle)

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
                        gid = self.free_tiles[0]
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

    def get_tile_id(self, position):
        return self.map[position[1]][position[0]]

    def is_free(self, position):
        return self.get_tile_id(position) in self.free_tiles

    def find_player(self):
        for y in range(self.height):
            for x in range(self.width):
                if self.map[y][x].__repr__() == 'Player':
                    return x, y

    def give_tanks_list_and_destinations(self, tank_turret, tank_hull, crash_tank, bullet, sprite_group):
        destinations = dict()
        tank_list = []
        for tile_object in self.tiled_map.tmx_data.objects:
            if 'Tank' in tile_object.name:
                rotate_turret, rotate_hull = tile_object.properties['rotate_turret'],\
                                             tile_object.properties['rotate_hull']
                destination = tile_object.properties['destination']
                x, y = int(tile_object.x // TILE_SIZE), int(tile_object.y // TILE_SIZE)
                tank_list.append(Tank((x, y), tank_turret, tank_hull, crash_tank, bullet,
                                      rotate_turret=rotate_turret, rotate_hull=rotate_hull, group=sprite_group))
                if destination == 'self':
                    destinations[tank_list[-1]] = (x, y)
                elif destination == 'player':
                    destinations[tank_list[-1]] = get_player_coords

        return tank_list, destinations


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


class Tank(pygame.sprite.Sprite):
    def __init__(self, position, image_turret, image_hull, crash_tank_image_turret, dict_id_bullets,
                 rotate_turret=0, rotate_hull=0, control_keys=CONTROL_KEYS_V1, group=None, is_player=False):
        super().__init__()

        self.is_player = is_player

        self.crash_tank_image_turret = crash_tank_image_turret
        self.dict_id_bullets = dict_id_bullets

        # init turret
        self.tank_turret = pygame.sprite.Sprite()
        self.tank_turret.image = image_turret
        self.tank_turret.rect = self.tank_turret.image.get_rect()
        self.tank_turret.rect.x, self.tank_turret.rect.y = \
            position[0] * TILE_SIZE, position[1] * TILE_SIZE

        # init hull
        self.image = image_hull
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

    def update_timers(self, clock):
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
            direction_move = DIRECTION_MOVE_BY_ANGLE[self.rotate_hull]
            self.set_position((self.x + direction_move[0], self.y + direction_move[1]))
            self.current_move_forward_cooldown = self.move_forward_cooldown
            return True
        return False

    def move_back(self):
        if self.current_move_back_cooldown <= 0:
            direction_move = DIRECTION_MOVE_BY_ANGLE[self.rotate_hull]
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

    def destroy_the_tank(self):
        self.is_crashed = True
        self.tank_turret.image = pygame.transform.rotate(
            self.crash_tank_image_turret, self.get_rotate()[1])

    def clear_the_tank(self):
        self.group.remove(self)
        self.group.remove(self.tank_turret)

    def __repr__(self):
        if self.is_player:
            return 'Player'
        else:
            return 'Tank'


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

    def render(self, screen):
        self.group.draw(screen)


class Game:
    def __init__(self, map, controlled_tanks, uncontrolled_tanks,
                 bullets, clock, destinations, sprites_group=[]):
        self.map = map
        self.clock = clock

        self.sprites_group = sprites_group
        self.controlled_tanks = controlled_tanks
        self.uncontrolled_tanks = uncontrolled_tanks

        self.destinations = destinations

        self.camera = self.map.camera

        self.bullets = bullets

    def render(self, screen):
        self.map.camera = self.camera
        self.map.render(screen)
        self.update_bullets(screen)

        for bullet in self.bullets:
            self.camera.apply(bullet)
            bullet.render(screen)

    def update_bullets(self, screen):
        for bullet in self.bullets:
            bullet.next_move()
            bullet_x, bullet_y = bullet.get_position()
            if not self.map.is_free((bullet_x, bullet_y)):
                del self.bullets[self.bullets.index(bullet)]
                if isinstance(self.map.map[bullet_y][bullet_x], Tank):
                    tank = self.map.map[bullet_y][bullet_x]
                    if tank.is_crashed:
                        self.map.map[bullet_y][bullet_x] = self.map.free_tiles[0]
                        tank.clear_the_tank()
                    else:
                        tank.destroy_the_tank()
                elif self.map.map[bullet_y][bullet_x] in self.map.break_tiles:
                    self.map.map[bullet_y][bullet_x] = self.map.free_tiles[0]

    def update_controlled_tanks(self):
        for tank in self.controlled_tanks:
            tank.update_timers(self.clock)
            if tank.is_crashed:
                continue
            # cur_x, cur_y = next_x, next_y = tank.get_position()
            unpack_player_coords = self.map.find_player()
            if not unpack_player_coords:
                cur_x, cur_y = next_x, next_y = tank.get_position()
            else:
                cur_x, cur_y = next_x, next_y = unpack_player_coords

            rotate_turret, rotate_hull = tank.get_rotate()
            direction_move = DIRECTION_MOVE_BY_ANGLE[rotate_hull]
            self.map.map[cur_y][cur_x] = tank

            if pygame.key.get_pressed()[tank.control_keys[FORWARD]]:
                next_x += direction_move[0]
                next_y += direction_move[1]
                if self.map.is_free((next_x, next_y)):
                    if tank.move_forward():
                        self.map.map[cur_y][cur_x] = self.map.free_tiles[0]
                        self.map.map[next_y][next_x] = tank
            if pygame.key.get_pressed()[tank.control_keys[BACK]]:
                next_x -= direction_move[0]
                next_y -= direction_move[1]
                if self.map.is_free((next_x, next_y)):
                    if tank.move_back():
                        self.map.map[cur_y][cur_x] = self.map.free_tiles[0]
                        self.map.map[next_y][next_x] = tank
            if pygame.key.get_pressed()[tank.control_keys[TURN_RIGHT]]:
                tank.turn_right()
            if pygame.key.get_pressed()[tank.control_keys[TURN_LEFT]]:
                tank.turn_left()
            if pygame.key.get_pressed()[tank.control_keys[TURN_RIGHT_TURRET]]:
                tank.turn_turret_right()
            if pygame.key.get_pressed()[tank.control_keys[TURN_LEFT_TURRET]]:
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
            tank.update_timers(self.clock)
            if tank.is_crashed:
                continue

            destination = self.destinations[tank]
            # Для динамических целей, которые требуют обновления данных о себе
            if callable(destination):
                destination = destination()
            # нахождение цели
            path, status = self.find_path(tank.get_position(), destination)
            # print(path)

            self.calculate_uncontrolled_tank_turret(tank)

            if len(path) > 3 and destination != None:
                self.calculate_uncontrolled_tank_move(path, destination, tank)

    def calculate_uncontrolled_tank_turret(self, tank):
        # Поскольку бот соображает слишком быстро, задержка через рандом должна снизить его скорость
        if random() > 0.80:
            cur_x, cur_y = tank.get_position()
            rotate_turret = tank.get_rotate()[0]
            row_cells = self.map.map[cur_y].copy()
            for cell in reversed(row_cells[:cur_x]):  # 90
                if cell == 1:
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
            for cell in row_cells[cur_x:]:  # 270
                if cell == 1:
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
            for cell in reversed([self.map.map[row][cur_x] for row in range(len(self.map.map)) if row < cur_x]):  # 0
                if cell == 1:
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
            for cell in [self.map.map[row][cur_x] for row in range(len(self.map.map)) if row > cur_x]:  # 180
                if cell == 1:
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
        cur_x, cur_y = next_x, next_y = tank.get_position()
        rotate_hull = tank.get_rotate()[1]
        # Поскольку бот соображает слишком быстро, задержка через рандом должна снизить его скорость
        if random() > 0.80:
            next_step = path[2]
            direction_move = self.calculate_direction(tank.get_position(), next_step)
            next_x += direction_move[0]
            next_y += direction_move[1]
            if direction_move == (0, 1):
                if rotate_hull == 180:
                    if tank.move_forward():
                        self.map.map[cur_y][cur_x] = self.map.free_tiles[0]
                        self.map.map[next_y][next_x] = tank
                else:
                    tank.turn_left()
            if direction_move == (1, 0):
                if rotate_hull == 270:
                    if tank.move_forward():
                        self.map.map[cur_y][cur_x] = self.map.free_tiles[0]
                        self.map.map[next_y][next_x] = tank
                else:
                    tank.turn_right()
            if direction_move == (0, -1):
                if rotate_hull == 0:
                    if tank.move_forward():
                        self.map.map[cur_y][cur_x] = self.map.free_tiles[0]
                        self.map.map[next_y][next_x] = tank
                else:
                    tank.turn_right()
            if direction_move == (-1, 0):
                if rotate_hull == 90:
                    if tank.move_forward():
                        self.map.map[cur_y][cur_x] = self.map.free_tiles[0]
                        self.map.map[next_y][next_x] = tank
                else:
                    tank.turn_left()
        else:
            self.map.map[next_y][next_x] = tank

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
            # obj.rect.x += self.rect.left
        elif isinstance(obj, pygame.Rect):
            obj.width += self.rect.left
            obj.height += self.rect.top
            # obj.move(self.rect.topleft)

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


def init_test_scene(clock):
    green_tank_turret = pygame.transform.scale(load_image(
        "green_turret.png", colorkey=-1), (TILE_SIZE, TILE_SIZE))
    green_tank_hull = pygame.transform.scale(load_image(
        "green_hull.png", colorkey=-1), (TILE_SIZE, TILE_SIZE))
    red_tank_turret = pygame.transform.scale(load_image(
        "red_turret.png", colorkey=-1), (TILE_SIZE, TILE_SIZE))
    red_tank_hull = pygame.transform.scale(load_image(
        "red_hull.png", colorkey=-1), (TILE_SIZE, TILE_SIZE))
    crash_tank = pygame.transform.scale(load_image(
        "crached_turret.png", colorkey=-1), (TILE_SIZE, TILE_SIZE))
    bullet_0 = pygame.transform.scale(load_image(
        "bullet_0.png", colorkey=-1), (TILE_SIZE, TILE_SIZE))

    # Формирование кадра(команды рисования на холсте):
    main_map = Map("1_lvl.tmx")
    all_sprites = pygame.sprite.Group()  # создадим группу, содержащую все спрайты

    controlled_tanks = [
        Tank((7, 1), green_tank_turret, green_tank_hull, crash_tank, {0: bullet_0},
             rotate_turret=0, rotate_hull=180, group=all_sprites,
             control_keys=CONTROL_KEYS_V1)]

    bullets = []
    # Цели, которые по-разному раздаются танкам-ботам
    uncontrolled_tanks, destinations = (main_map.give_tanks_list_and_destinations(red_tank_turret, red_tank_hull,
                                                                                  crash_tank, {0: bullet_0},
                                                                                  all_sprites))

    return Game(main_map, controlled_tanks, uncontrolled_tanks,
                bullets, clock, destinations, sprites_group=[all_sprites])


def init_lvl2_scene(clock):
    green_tank_turret = pygame.transform.scale(load_image(
        "green_turret.png", colorkey=-1), (TILE_SIZE, TILE_SIZE))
    green_tank_hull = pygame.transform.scale(load_image(
        "green_hull.png", colorkey=-1), (TILE_SIZE, TILE_SIZE))
    red_tank_turret = pygame.transform.scale(load_image(
        "red_turret.png", colorkey=-1), (TILE_SIZE, TILE_SIZE))
    red_tank_hull = pygame.transform.scale(load_image(
        "red_hull.png", colorkey=-1), (TILE_SIZE, TILE_SIZE))
    crash_tank = pygame.transform.scale(load_image(
        "crached_turret.png", colorkey=-1), (TILE_SIZE, TILE_SIZE))
    bullet_0 = pygame.transform.scale(load_image(
        "bullet_0.png", colorkey=-1), (TILE_SIZE, TILE_SIZE))

    # Формирование кадра(команды рисования на холсте):
    main_map = Map("2_lvl.tmx")
    all_sprites = pygame.sprite.Group()  # создадим группу, содержащую все спрайты

    controlled_tanks = [
        Tank((1, 1), green_tank_turret, green_tank_hull, crash_tank, {0: bullet_0},
             rotate_turret=0, rotate_hull=180, group=all_sprites,
             control_keys=CONTROL_KEYS_V1, is_player=True)]

    uncontrolled_tanks, destinations = (main_map.give_tanks_list_and_destinations(red_tank_turret, red_tank_hull,
                                   crash_tank, {0: bullet_0}, all_sprites))

    bullets = []

    return Game(main_map, controlled_tanks, uncontrolled_tanks,
                bullets, clock, destinations, sprites_group=[all_sprites])


def main():
    pygame.init()
    screen = pygame.display.set_mode(WINDOW_SIZE)
    pygame.display.set_caption("TANK BATTLES")

    # Главный игровой цикл:
    clock = pygame.time.Clock()
    game = init_lvl2_scene(clock)

    running = True
    while running:
        # Цикл приема и обработки сообщений:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # обработка остальных событий
            # ...

        game.render(screen)

        game.update_controlled_tanks()
        game.update_uncontrolled_tanks()

        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()


if __name__ == "__main__":
    main()
