from random import randint
from pygame.locals import *
import json

import pygame.event

# Constants
CONFIGURATION_FILE = 'configs/64_64_maze.json'
# CONFIGURATION_FILE = ['configs/8_8_maze.json', 'configs/16_16_maze.json', 'configs/32_32_maze.json']
USE_MULTIPLE_CONFIG = True


class Game:
    def __init__(self):
        self._running = True
        self.player_asset = None
        self.walls_assets = None
        self.screen = None
        self.engine = None
        self.config = {}

        self.player_position = (0, 0)

    def load_configuration(self):
        config_to_use = None
        if not isinstance(CONFIGURATION_FILE, list):
            config_to_use = CONFIGURATION_FILE
        elif isinstance(CONFIGURATION_FILE, list):
            if not USE_MULTIPLE_CONFIG:
                config_to_use = CONFIGURATION_FILE[0]
            else:
                config_to_use = CONFIGURATION_FILE[randint(0,  len(CONFIGURATION_FILE) - 1)]
        self.config = ConfigGenerator.load_config_from_json(config_to_use)

    def prepare_game(self):
        """
        Prepare the assets and the game
        :return (None):
        """
        pygame.init()
        self.engine = Maze(self.config['MAZE_SIZE'][0], self.config['MAZE_SIZE'][1])

        self.screen = pygame.display.set_mode((self.config['SCREEN'][0], self.config['SCREEN'][1]), pygame.HWSURFACE)
        pygame.display.set_caption('Labyrinthe')
        self.screen.fill((255, 255, 255))
        self.load_assets()
        self.engine.set_random_edges()
        self.player_position = self.engine.edges[0]

    def load_assets(self):
        self.player_asset = pygame.image.load('assets/player.png')
        self.player_asset = pygame.transform.scale(self.player_asset, (self.config['PLAYER_SIZE'], self.config['PLAYER_SIZE']))

        self.walls_assets = pygame.image.load('assets/base_wall.png')
        self.walls_assets = pygame.transform.scale(self.walls_assets, (self.config['WALL_SIZE'], self.config['WALL_SIZE']))

    def execute(self):
        """
        Run the game core
        :return (None):
        """
        self.load_configuration()
        self.prepare_game()
        while self._running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                elif event.type == pygame.KEYDOWN:
                    key_pressed = pygame.key.get_pressed()
                    directions = self.engine.get_directions(self.player_position)
                    direction = ''

                    if key_pressed[K_RIGHT]:
                        direction = 'e'
                    elif key_pressed[K_DOWN]:
                        direction = 's'
                    elif key_pressed[K_UP]:
                        direction = 'n'
                    elif key_pressed[K_LEFT]:
                        direction = 'o'
                    elif key_pressed[K_r]:
                        self.__reset_maze()

                    if direction and direction in directions:
                        self.player_position = directions[direction]
                        if self.player_position == self.engine.edges[1]:
                            self.__reset_maze()
            self.__render()

    def __reset_maze(self):
        """
        Reset the maze
        :return (None):
        """
        if USE_MULTIPLE_CONFIG:
            previous_config = self.config
            self.load_configuration()
            if previous_config['WALL_SIZE'] != self.config['WALL_SIZE']:
                self.walls_assets = pygame.transform.scale(pygame.image.load('assets/base_wall.png'),
                                                           (self.config['WALL_SIZE'], self.config['WALL_SIZE']))
            if previous_config['PLAYER_SIZE'] != self.config['PLAYER_SIZE']:
                self.player_asset = pygame.transform.scale(pygame.image.load('assets/player.png'),
                                                           (self.config['PLAYER_SIZE'], self.config['PLAYER_SIZE']))

        self.engine.maze = Maze.create_tiles(self.config['MAZE_SIZE'][0], self.config['MAZE_SIZE'][1])
        self.engine.create_maze()
        self.engine.edges = []
        self.engine.set_random_edges()
        self.player_position = self.engine.edges[0]

    def __render(self):
        """
        Make a rendering of the maze
        :return (None):
        """
        self.screen.fill((255, 255, 255))
        player_rect = self.player_asset.get_rect(center=(
            int(self.config['BASE_POSITION'][0] + self.player_position[1] * (self.config['WALL_SIZE'] * 2) + self.config['WALL_SIZE'] + self.config['WALL_SIZE'] / 2),
            int(self.config['BASE_POSITION'][1] + self.player_position[0] * (self.config['WALL_SIZE'] * 2) + self.config['WALL_SIZE'] + self.config['WALL_SIZE'] / 2)
        ))
        self.screen.blit(self.player_asset, player_rect)

        x = self.config['BASE_POSITION'][0]
        y = self.config['BASE_POSITION'][1]
        # Head part
        for i in range(len(self.engine.maze[0])):
            self.screen.blit(self.walls_assets, (x, y))
            x += self.config['WALL_SIZE']
            self.screen.blit(self.walls_assets, (x, y))
            x += self.config['WALL_SIZE']
        self.screen.blit(self.walls_assets, (x, y))

        x = self.config['BASE_POSITION'][0]
        y += self.config['WALL_SIZE']
        for j in range(len(self.engine.maze)):
            if not (j, 0) in self.engine.edges:
                self.screen.blit(self.walls_assets, (x, y))

            x += self.config['WALL_SIZE']
            for z, val in enumerate(self.engine.maze[j]):
                x += self.config['WALL_SIZE']
                if val['e'] and (not (j, z) in self.engine.edges or (len(self.engine.maze[j]) - 1 != z)):
                    self.screen.blit(self.walls_assets, (x, y))
                x += self.config['WALL_SIZE']

            x = self.config['BASE_POSITION'][0]
            y += self.config['WALL_SIZE']

            for z, val in enumerate(self.engine.maze[j]):
                self.screen.blit(self.walls_assets, (x, y))
                x += self.config['WALL_SIZE']
                if val['s']:
                    self.screen.blit(self.walls_assets, (x, y))
                x += self.config['WALL_SIZE']
                if z == len(self.engine.maze[j]) - 1:
                    self.screen.blit(self.walls_assets, (x, y))
            x = self.config['BASE_POSITION'][0]
            y += self.config['WALL_SIZE']
        pygame.display.flip()


class Maze:
    def __init__(self, columns, lines, edges=[]):
        self.maze = Maze.create_tiles(columns, lines)
        self.edges = edges
        self.create_maze()

    def create_maze(self):
        """
        Creates a maze
        :return (None):
        """
        self.prepare_maze()

        while not self.creation_is_finished():
            rand_cell = self.select_random_cell()
            adjacent_cells = self.adjacent_cells(rand_cell)
            if len(adjacent_cells) <= 0:
                continue

            adjacent_cell = adjacent_cells[randint(0, len(adjacent_cells) - 1)]
            if self.maze[rand_cell[0]][rand_cell[1]]['v'] == self.maze[adjacent_cell[0]][adjacent_cell[1]]['v']:
                continue

            self.open_wall(adjacent_cell, rand_cell)
            self.affect_values(self.maze[rand_cell[0]][rand_cell[1]]['v'],
                               self.maze[adjacent_cell[0]][adjacent_cell[1]]['v'])
        self.affect_values('', self.maze[0][0]['v'])

    @staticmethod
    def create_tiles(lines=2, columns=2):
        """
        Returns an empty maze
        :param (int) lines: number of rows
        :param (int) columns: number of columns
        :return (list of list of dict): Example: [[{ 'v': '', 'e': 1, 's': 1 }], [{ 'v': '', 'e': 1, 's': 1 }]]

        >>> Maze.create_tiles()
        [[{'v': ' ', 'e': 1, 's': 1}, {'v': ' ', 'e': 1, 's': 1}], [{'v': ' ', 'e': 1, 's': 1}, {'v': ' ', 'e': 1, 's': 1}]]

        >>> Maze.create_tiles(3, 3)
        [[{'v': ' ', 'e': 1, 's': 1}, {'v': ' ', 'e': 1, 's': 1}, {'v': ' ', 'e': 1, 's': 1}], [{'v': ' ', 'e': 1, 's': 1}, {'v': ' ', 'e': 1, 's': 1}, {'v': ' ', 'e': 1, 's': 1}], [{'v': ' ', 'e': 1, 's': 1}, {'v': ' ', 'e': 1, 's': 1}, {'v': ' ', 'e': 1, 's': 1}]]

        """
        return [[{'v': ' ', 'e': 1, 's': 1} for _ in range(columns)] for _ in range(lines)]

    def prepare_maze(self):
        columns = len(self.maze[0])
        for line_index in range(len(self.maze)):
            for column_index in range(len(self.maze[line_index])):
                self.maze[line_index][column_index]['v'] = chr(48 + line_index * columns + column_index)

    def destroy_wall(self, cell, direction):
        """
        Modifies the direction key value of the cell in the matrix passed in parameter
        :param (tuple) cell: position of the cell in the (l,c) matrix
        :param (string) direction: Direction of the wall to be removed 's' or 'e'
        :return:
        """
        if direction in ['s', 'e']:
            self.maze[cell[0]][cell[1]][direction] = 0

    def open_wall(self, cell_1, cell_2):
        """
        Changes the value of the direction keys of the cell(s) in the maze
        :param (tuple) cell_1: Position of the first cell
        :param (tuple) cell_2: Position of the second cell
        :return (None):
        """
        if cell_1[0] == cell_2[0]:
            if cell_1[1] < cell_2[1]:
                self.destroy_wall(cell_1, 'e')
            else:
                self.destroy_wall(cell_2, 'e')
        else:
            if cell_1[0] < cell_2[0]:
                self.destroy_wall(cell_1, 's')
            else:
                self.destroy_wall(cell_2, 's')

    def adjacent_cells(self, cell):
        """
        Get all adjacent cells
        :param (tuple) cell: Position of the cell
        :return (list of tuple):

        >>> maze = Maze(3, 3)
        >>> maze.adjacent_cells((1, 1))
        [(1, 0), (1, 2), (0, 1), (2, 1)]

        >>> maze.adjacent_cells((1, 0))
        [(1, 1), (0, 0), (2, 0)]

        >>> maze.adjacent_cells((0, 2))
        [(0, 1), (1, 2)]

        >>> maze.adjacent_cells((2, 0))
        [(2, 1), (1, 0)]

        >>> maze.adjacent_cells((0, 1))
        [(0, 0), (0, 2), (1, 1)]
        """
        positions = []
        for i in range(-1, 2, 2):
            position = (cell[0], cell[1] + i)
            if position[0] < 0 or position[1] < 0 or position[0] >= len(self.maze) or position[1] >= len(self.maze[0]):
                continue
            positions.append(position)

        for i in range(-1, 2, 2):
            position = (cell[0] + i, cell[1])
            if position[0] < 0 or position[1] < 0 or position[0] >= len(self.maze) or position[1] >= len(self.maze[0]):
                continue
            positions.append(position)
        return positions

    def select_random_cell(self):
        """
        Returns a random cell from the maze
        :return (tuple): Position of random cell
        """
        selection = randint(0, len(self.maze) - 1)
        return selection, randint(0, len(self.maze[selection]) - 1)

    def affect_values(self, new_value, last_value):
        """
        Assigns all last_value values with new_value
        :param (string) new_value:
        :param (string) last_value:
        :return (None):
        """
        lines = len(self.maze)
        columns = len(self.maze[0])
        for line in range(lines):
            for row in range(columns):
                if self.maze[line][row]['v'] == last_value:
                    self.maze[line][row]['v'] = new_value

    def get_directions(self, position):
        """
        Returns the possible moves
        :param (dict) position: The actual position
        :return:
        """
        positions = {}
        cells = self.adjacent_cells(position)
        for cell in cells:
            direction = None
            if cell[0] > position[0] and not self.maze[position[0]][position[1]]['s']:
                direction = 's'
            elif cell[0] < position[0] and not self.maze[position[0] - 1][position[1]]['s']:
                direction = 'n'
            elif cell[1] > position[1] and not self.maze[position[0]][position[1]]['e']:
                direction = 'e'
            elif cell[1] < position[1] and not self.maze[position[0]][position[1] - 1]['e']:
                direction = 'o'

            if direction:
                positions[direction] = cell
        return positions

    def set_random_edges(self):
        """
        Set random edges for the maze
        :return (None):
        """
        self.edges.append((randint(0, len(self.maze) - 1), 0))
        self.edges.append((randint(0, len(self.maze) - 1), len(self.maze[0]) - 1))

    def creation_is_finished(self):
        """
        Test if all cells are the same
        :return (boolean):

        >>> maze = Maze(3, 3)
        >>> maze.creation_is_finished()
        True

        >>> maze.maze[2][2]['v'] = 'x'
        >>> maze.creation_is_finished()
        False

        """
        first_value = self.maze[0][0]
        for line in self.maze:
            for cell in line:
                if cell['v'] != first_value['v']:
                    return False
        return True


class ConfigGenerator:
    @staticmethod
    def load_config_from_json(path):
        try:
            data = json.load(open(path))
            return ConfigGenerator.__parse_data(data)
        except json.decoder.JSONDecodeError:
            print('ERROR, Invalid JSON format')
        except (FileNotFoundError, IOError):
            print('ERROR, Wrong file or file path')

    @staticmethod
    def __parse_data(data):
        config = {
            'SCREEN': (1024, 1024),
            'WALL_SIZE': 64,
            'MAZE_SIZE': (16, 16),
            'BASE_POSITION': 'CENTER',
            'PLAYER_SIZE': 48
        }

        for parameter in config.keys():
            value = config[parameter]
            if parameter in data:
                value = data[parameter]
                config[parameter] = value

            if parameter == 'BASE_POSITION':
                if value == 'CENTER':
                    config[parameter] = (
                        int((config['SCREEN'][0] - ((config['MAZE_SIZE'][1] + 1) * config['WALL_SIZE'] * 2)) / 2 + config['WALL_SIZE'] / 2),
                        int((config['SCREEN'][1] - ((config['MAZE_SIZE'][0] + 1) * config['WALL_SIZE'] * 2)) / 2 + config['WALL_SIZE'] / 2)
                    )
                else:
                    config[parameter] = tuple(value)
        return config


app = Game()
app.execute()
