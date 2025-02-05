import pygame
import random

pygame.init()
pygame.display.set_caption("Mind Maze!")

# Constants
BLOCK_WIDTH = 10
BLOCK_HEIGHT = 10

MAZE_SIZE = 16

MARGIN = 10

HEIGHT = 400 + MARGIN
WIDTH = HEIGHT + (BLOCK_WIDTH * (2 * MAZE_SIZE + 1))
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
GREEN = (100, 180, 0)
RED = (255, 0, 0)
BLACK = (0, 0, 0)
DARK_WHITE = (50, 50, 50)


class SpriteSheet(object):
    def __init__(self, file_name):
        try:
            self.sprite_sheet = pygame.image.load(file_name).convert()
        except pygame.error:
            print("Could not load Image!")

    def get_image(self, x, y, width, height):
        image = pygame.Surface([width, height]).convert()
        image.blit(self.sprite_sheet, (0, 0), (x, y, width, height))
        image.set_colorkey(BLACK)
        return image

    # helper func - makes an array from sprite sheet
    def make_sprite_array(self, x, y, width, height, numImages, imgPerRow, scale=1):
        spriteList = []
        imgInRowCount = 0
        for i in range(numImages):
            imgInRowCount += 1
            image = self.get_image(x, y, width, height)
            image = pygame.transform.scale(image, (width * scale, height * scale))
            spriteList.append(image)

            # grab images in row
            if imgInRowCount < imgPerRow:
                x += width
            # move down a colm and start at beginning of row
            if imgInRowCount >= imgPerRow:
                y += height
                x = 0
                imgInRowCount = 0

        return spriteList


class Maze:
    def __init__(self, size):
        self.size = size
        self.grid = [[1 for _ in range(size * 2 + 1)] for _ in range(size * 2 + 1)]
        self.visited = [[False for _ in range(size)] for _ in range(size)]
        self.stack = []

    def in_bounds(self, x, y):
        return 0 <= x < self.size and 0 <= y < self.size

    def get_neighbors(self, x, y):
        neighbors = []
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        random.shuffle(directions)
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if self.in_bounds(nx, ny) and not self.visited[ny][nx]:
                neighbors.append((nx, ny))
        return neighbors

    def find_dead_ends(self):
        # A function to find dead ends within the maze by checking that only one neighbor for a checked cell is marked as a path
        dead_ends = []
        for y in range(1, self.size * 2, 2):
            for x in range(1, self.size * 2, 2):
                if self.grid[y][x] == 0:
                    neighbors = sum(
                        1
                        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]
                        if self.grid[y + dy][x + dx] == 1
                    )
                    if neighbors == 3:
                        dead_ends.append((x, y))
        return dead_ends

    def carve_path(self, x1, y1, x2, y2):
        gx1, gy1 = x1 * 2 + 1, y1 * 2 + 1
        gx2, gy2 = x2 * 2 + 1, y2 * 2 + 1
        self.grid[(gy1 + gy2) // 2][(gx1 + gx2) // 2] = 0
        self.grid[gy2][gx2] = 0

    def generate(self):
        start_x, start_y = 0, 0
        self.grid[start_y * 2 + 1][start_x * 2 + 1] = 0
        self.visited[start_y][start_x] = True
        self.stack.append((start_x, start_y))

        while self.stack:
            x, y = self.stack[-1]
            neighbors = self.get_neighbors(x, y)
            if neighbors:
                nx, ny = random.choice(neighbors)
                self.carve_path(x, y, nx, ny)
                self.visited[ny][nx] = True
                self.stack.append((nx, ny))
            else:
                self.stack.pop()

        dead_ends = self.find_dead_ends()
        if dead_ends:
            self.end = dead_ends[random.randint(-((len(dead_ends) // 4)), -1)]
        else:
            self.end = (self.size * 2 - 1, self.size * 2 - 1)

        return self.grid, self.end


class Game(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.flags = pygame.RESIZABLE

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), self.flags)
        self.clock = pygame.time.Clock()

        self.frame_itter = 0

        arrow_sheet = SpriteSheet("arrow-sheet.png")
        self.arrow_sheet = arrow_sheet.make_sprite_array(0, 0, 10, 10, 4, 4)
        self.arrow_img = self.arrow_sheet[1]
        self.arrow_rect = self.arrow_img.get_rect()
        self.arrow_rect.x = BLOCK_WIDTH * 1
        self.arrow_rect.y = BLOCK_HEIGHT * 1

        maze_sheet = SpriteSheet("maze-sheet.png")
        self.maze_sheet = maze_sheet.make_sprite_array(0, 0, 200, 200, 41, 41, 2)
        self.maze_img = self.maze_sheet[0]
        self.maze_rect = self.maze_img.get_rect()
        self.maze_rect.x = BLOCK_WIDTH * (2 * MAZE_SIZE + 1)
        self.maze_rect.y = 0

        self.dir = [-1, 0]

        self.walls = []

        # self.maze = [
        #     [1,1,1,1,1,1,1],
        #     [1,0,1,0,0,1,1],
        #     [1,0,1,1,0,1,1],
        #     [1,0,0,0,0,0,1],
        #     [1,1,1,0,1,1,1],
        #     [1,0,0,0,0,1,1],
        #     [1,1,1,1,1,1,1]]

        newMaze = Maze(MAZE_SIZE)
        self.maze, self.mazeEnd = newMaze.generate()

        # this is a mapping of our players line of sight corrisponding to the correct index of an image sheet
        # the order is regardless of direction its: left of player, right, left+1, front, right+1, left+2, front+2, right+2
        # 1's are walls and 0's are floor each image at the index is the same
        self.imageTable = {
            "11101101": 0,
            "11101111": 1,
            "11111111": 2,
            "11101001": 3,
            "11001111": 4,
            "01111111": 5,
            "11101100": 6,
            "11100111": 7,
            "10111111": 8,
            "11101000": 9,
            "11000111": 10,
            "00111111": 11,
            "11000101": 12,
            "00101111": 13,
            "00011111": 14,
            "10101001": 15,
            "01101100": 16,
            "10101101": 17,
            "01101101": 18,
            "11001100": 19,
            "11100001": 20,
            "10110111": 21,
            "01011111": 22,
            "01100101": 23,
            "10001101": 24,
            "00101000": 25,
            "00110111": 26,
            "11100101": 27,
            "11001101": 28,
            "10101111": 29,
            "01101111": 30,
            "11000110": 31,
            "11000011": 32,
            "00101001": 33,
            "00101100": 34,
            "01101000": 35,
            "10101000": 36,
            "00010111": 37,
            "01101001": 38,
            "10101100": 39,
            "00101101": 40,
        }

        self.mazeHeight = len(self.maze)
        self.mazeWidth = len(self.maze[0])

        self.buildWalls(self.maze)

        # possition mini map in the top left of screen
        self.miniMapBG = (
            0,
            0,
            BLOCK_WIDTH * self.mazeWidth,
            BLOCK_HEIGHT * self.mazeHeight,
        )

    # checks our direction and approprately turns left
    def turnLeft(self):
        # facing right
        if self.dir == [1, 0]:
            self.dir = [0, -1]
        # facing left
        elif self.dir == [-1, 0]:
            self.dir = [0, 1]
        # facing down
        elif self.dir == [0, 1]:
            self.dir = [1, 0]
        # facing up
        elif self.dir == [0, -1]:
            self.dir = [-1, 0]

    # checks our direction and approprately turns right
    def turnRight(self):
        # facing right
        if self.dir == [1, 0]:
            self.dir = [0, 1]
        # facing left
        elif self.dir == [-1, 0]:
            self.dir = [0, -1]
        # facing down
        elif self.dir == [0, 1]:
            self.dir = [-1, 0]
        # facing up
        elif self.dir == [0, -1]:
            self.dir = [1, 0]

    # make a string out of the check direction funtions that return lists
    def makeKey(self, grid):
        key = ""
        for i in grid:
            key += str(i)
        return key

    # fuction to print out the 1's and 0's of a map
    def printMap(self, maze):
        printedMap = ""
        for i in range(len(maze)):
            for j in range(len(maze)):
                printedMap += str(maze[i][j])
            print(printedMap)
            printedMap = ""

    # check for ever 1 in matrix and assign it a block
    def buildWalls(self, maze):
        for i in range(len(maze)):
            for j in range(len(maze)):
                if maze[i][j] == 1:
                    self.walls.append(
                        (BLOCK_WIDTH * i, BLOCK_HEIGHT * j, BLOCK_WIDTH, BLOCK_HEIGHT)
                    )

    def moveForward(self, direction):
        # get current possiton
        pos = [self.arrow_rect.x // BLOCK_WIDTH, self.arrow_rect.y // BLOCK_HEIGHT]
        # add direction we are facing
        newPos = [pos[0] + direction[0], pos[1] + direction[1]]
        # check if new possition will put us out of bounds
        if (
            newPos[0] >= 0
            and newPos[0] < self.mazeWidth
            and newPos[1] >= 0
            and newPos[1] < self.mazeHeight
        ):
            # check if new possiton is a wall or not
            if self.maze[newPos[0]][newPos[1]] != 1:
                # move mini map character
                self.arrow_rect.x = newPos[0] * BLOCK_WIDTH
                self.arrow_rect.y = newPos[1] * BLOCK_HEIGHT

    def moveBackward(self, direction):
        # get current possiton
        pos = [self.arrow_rect.x // BLOCK_WIDTH, self.arrow_rect.y // BLOCK_HEIGHT]
        # subtract direction we are facing
        newPos = [pos[0] - direction[0], pos[1] - direction[1]]
        # check if new possition will put us out of bounds
        if (
            newPos[0] >= 0
            and newPos[0] < self.mazeWidth
            and newPos[1] >= 0
            and newPos[1] < self.mazeHeight
        ):
            # check if new possiton is a wall or not
            if self.maze[newPos[0]][newPos[1]] != 1:
                # move mini map character
                self.arrow_rect.x = newPos[0] * BLOCK_WIDTH
                self.arrow_rect.y = newPos[1] * BLOCK_HEIGHT

    def play_step(self):
        self.ui()

        # RIGHT
        if self.dir == [1, 0]:
            self.arrow_img = self.arrow_sheet[2]
            index = self.imageTable[self.makeKey(self.checkRight())]
            self.maze_img = self.maze_sheet[index]

        # LEFT
        elif self.dir == [-1, 0]:
            self.arrow_img = self.arrow_sheet[3]
            index = self.imageTable[self.makeKey(self.checkLeft())]
            self.maze_img = self.maze_sheet[index]

        # DOWN
        elif self.dir == [0, 1]:
            self.arrow_img = self.arrow_sheet[0]
            index = self.imageTable[self.makeKey(self.checkDown())]
            self.maze_img = self.maze_sheet[index]

        # UP
        elif self.dir == [0, -1]:
            self.arrow_img = self.arrow_sheet[1]
            index = self.imageTable[self.makeKey(self.checkUp())]
            self.maze_img = self.maze_sheet[index]

    def ui(self):
        # Render
        self.screen.fill(BLACK)

        # Render 3d maze
        self.screen.blit(self.maze_img, self.maze_rect)

        # Render white background for mini map
        pygame.draw.rect(
            self.screen,
            WHITE,
            (
                self.miniMapBG[0],
                self.miniMapBG[1],
                self.miniMapBG[2],
                self.miniMapBG[3],
            ),
        )
        # Render each 2d wall for mini map
        for wall in self.walls:
            pygame.draw.rect(self.screen, BLACK, (wall[0], wall[1], wall[2], wall[3]))

        # Render the end point in red
        end_y, end_x = self.mazeEnd
        pygame.draw.rect(
            self.screen,
            RED,
            pygame.Rect(
                end_x * BLOCK_WIDTH, end_y * BLOCK_HEIGHT, BLOCK_WIDTH, BLOCK_HEIGHT
            ),
        )

        # Render mini map green arrow character
        self.screen.blit(self.arrow_img, self.arrow_rect)

        self.clock.tick(60)
        pygame.display.flip()

    # these last four functions give our character its line of sight checkUp(),checkDown(), checkRight(), checkLeft()
    def checkUp(self):
        # grab our current position
        pos = [self.arrow_rect.x // BLOCK_WIDTH, self.arrow_rect.y // BLOCK_HEIGHT]
        imageKey = [1, 1, 1, 1, 1, 1, 1, 1]
        # check left of player
        if pos[0] - 1 >= 0:
            if self.maze[pos[0] - 1][pos[1]] == 0:
                imageKey[0] = 0

        # check right of player
        if pos[0] + 1 < self.mazeWidth:
            if self.maze[pos[0] + 1][pos[1]] == 0:
                imageKey[1] = 0

        # check front-left of player
        if pos[0] - 1 >= 0 and pos[1] - 1 < self.mazeHeight:
            if self.maze[pos[0] - 1][pos[1] - 1] == 0:
                imageKey[2] = 0

        # check front-right of player
        if pos[0] + 1 < self.mazeWidth and pos[1] - 1 >= 0:
            if self.maze[pos[0] + 1][pos[1] - 1] == 0:
                imageKey[4] = 0

        # check front of player if wall the rest of indexes are 1's
        if pos[1] - 1 >= 0:
            if self.maze[pos[0]][pos[1] - 1] == 0:
                imageKey[3] = 0
            else:
                # if our path is blocked the rest should remain as 1's
                return imageKey

        # check front-left + 1 of player
        if pos[0] - 1 >= 0 and pos[1] - 2 >= 0:
            if self.maze[pos[0] - 1][pos[1] - 2] == 0:
                imageKey[5] = 0

        # check front-right + 1 of player
        if pos[0] + 1 < self.mazeWidth and pos[1] - 2 >= 0:
            if self.maze[pos[0] + 1][pos[1] - 2] == 0:
                imageKey[7] = 0

        # check front + 1
        if pos[1] - 2 >= 0:
            if self.maze[pos[0]][pos[1] - 2] == 0:
                imageKey[6] = 0
        # now we have built the correct image key for our character facing down
        return imageKey

    def checkDown(self):
        # grab our current position
        pos = [self.arrow_rect.x // BLOCK_WIDTH, self.arrow_rect.y // BLOCK_HEIGHT]
        imageKey = [1, 1, 1, 1, 1, 1, 1, 1]
        # check left of player
        if pos[0] + 1 >= 0:
            if self.maze[pos[0] + 1][pos[1]] == 0:
                imageKey[0] = 0

        # check right of player
        if pos[0] - 1 < self.mazeWidth:
            if self.maze[pos[0] - 1][pos[1]] == 0:
                imageKey[1] = 0

        # check front-left of player
        if pos[0] + 1 >= 0 and pos[1] + 1 < self.mazeHeight:
            if self.maze[pos[0] + 1][pos[1] + 1] == 0:
                imageKey[2] = 0

        # check front-right of player
        if pos[0] - 1 < self.mazeWidth and pos[1] + 1 < self.mazeHeight:
            if self.maze[pos[0] - 1][pos[1] + 1] == 0:
                imageKey[4] = 0

        # check front of player if wall the rest of indexes are 1's
        if pos[1] + 1 < self.mazeHeight:
            if self.maze[pos[0]][pos[1] + 1] == 0:
                imageKey[3] = 0
            else:
                # if our path is blocked the rest should remain as 1's
                return imageKey

        # check front-left + 1 of player
        if pos[0] + 1 >= 0 and pos[1] + 2 < self.mazeHeight:
            if self.maze[pos[0] + 1][pos[1] + 2] == 0:
                imageKey[5] = 0

        # check front-right + 1 of player
        if pos[0] - 1 < self.mazeWidth and pos[1] + 2 < self.mazeHeight:
            if self.maze[pos[0] - 1][pos[1] + 2] == 0:
                imageKey[7] = 0

        # check front + 1
        if pos[1] + 2 < self.mazeHeight:
            if self.maze[pos[0]][pos[1] + 2] == 0:
                imageKey[6] = 0
        # now we have built the correct image key for our character facing down
        return imageKey

    def checkRight(self):
        pos = [self.arrow_rect.x // BLOCK_WIDTH, self.arrow_rect.y // BLOCK_HEIGHT]
        imageKey = [1, 1, 1, 1, 1, 1, 1, 1]
        # check left of player
        if pos[1] - 1 >= 0:
            if self.maze[pos[0]][pos[1] - 1] == 0:
                imageKey[0] = 0

        # check right of player
        if pos[1] + 1 < self.mazeHeight:
            if self.maze[pos[0]][pos[1] + 1] == 0:
                imageKey[1] = 0

        # check front-left of player
        if pos[0] + 1 < self.mazeWidth and pos[1] - 1 >= 0:
            if self.maze[pos[0] + 1][pos[1] - 1] == 0:
                imageKey[2] = 0

        # check front-right of player
        if pos[0] + 1 < self.mazeWidth and pos[1] + 1 < self.mazeHeight:
            if self.maze[pos[0] + 1][pos[1] + 1] == 0:
                imageKey[4] = 0

        # check front of player if wall the rest of indexes are 1's
        if pos[0] + 1 < self.mazeWidth:
            if self.maze[pos[0] + 1][pos[1]] == 0:
                imageKey[3] = 0
            else:
                # if our path is blocked the rest should remain as 1's
                return imageKey

        # check front-left + 1 of player
        if pos[0] + 2 < self.mazeWidth and pos[1] - 1 >= 0:
            if self.maze[pos[0] + 2][pos[1] - 1] == 0:
                imageKey[5] = 0

        # check front-right + 1 of player
        if pos[0] + 2 < self.mazeWidth and pos[1] + 1 < self.mazeHeight:
            if self.maze[pos[0] + 2][pos[1] + 1] == 0:
                imageKey[7] = 0

        # check front + 1
        if pos[0] + 2 < self.mazeWidth:
            if self.maze[pos[0] + 2][pos[1]] == 0:
                imageKey[6] = 0
        # now we have built the correct image key for our character facing down
        return imageKey

    def checkLeft(self):
        pos = [self.arrow_rect.x // BLOCK_WIDTH, self.arrow_rect.y // BLOCK_HEIGHT]
        imageKey = [1, 1, 1, 1, 1, 1, 1, 1]
        # check left of player
        if pos[1] - 1 >= 0:
            if self.maze[pos[0]][pos[1] - 1] == 0:
                imageKey[0] = 0

        # check right of player
        if pos[1] + 1 < self.mazeHeight:
            if self.maze[pos[0]][pos[1] + 1] == 0:
                imageKey[1] = 0

        # check front-left of player
        if pos[0] - 1 >= 0 and pos[1] - 1 >= 0:
            if self.maze[pos[0] - 1][pos[1] - 1] == 0:
                imageKey[2] = 0

        # check front-right of player
        if pos[0] - 1 >= 0 and pos[1] + 1 < self.mazeHeight:
            if self.maze[pos[0] - 1][pos[1] + 1] == 0:
                imageKey[4] = 0

        # check front of player if wall the rest of indexes are 1's
        if pos[0] - 1 >= 0:
            if self.maze[pos[0] - 1][pos[1]] == 0:
                imageKey[3] = 0
            else:
                # if our path is blocked the rest should remain as 1's
                return imageKey

        # check front-left + 1 of player
        if pos[0] - 2 >= 0 and pos[1] - 1 >= 0:
            if self.maze[pos[0] - 2][pos[1] - 1] == 0:
                imageKey[5] = 0

        # check front-right + 1 of player
        if pos[0] - 2 >= 0 and pos[1] + 1 < self.mazeHeight:
            if self.maze[pos[0] - 2][pos[1] + 1] == 0:
                imageKey[7] = 0

        # check front + 1
        if pos[0] - 2 >= 0:
            if self.maze[pos[0] - 2][pos[1]] == 0:
                imageKey[6] = 0
        # now we have built the correct image key for our character facing down
        return imageKey


game = Game()
# Main game loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                game.turnLeft()

            if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                game.turnRight()

            if event.key == pygame.K_UP or event.key == pygame.K_w:
                game.moveForward(game.dir)

            if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                game.moveBackward(game.dir)

            if event.key == pygame.K_q:
                pygame.quit()

    game.play_step()
