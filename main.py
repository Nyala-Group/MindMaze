import pygame
import random
import sys

"""
DEV NOTES

Need to fill out the question files that are not test files.
    
Can we also figure out some way to make the player rely on the actual game screen more?
    I find myself pretty much exclusively using the minimap to navigate.
    Perhaps just removing the red endpoint marker would do it, but right now that helps with testing since there are no
    in-game door visuals yet.
    - Lucas
"""

pygame.init()
pygame.display.set_caption("Mind Maze!")

# Constants
MAZE_SIZE = 15
MINIMAP_SIZE = (2 * MAZE_SIZE + 1) * 10

WIDTH = max((400 + MINIMAP_SIZE), 610)
HEIGHT = max(540, (MINIMAP_SIZE + 140))
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
GREEN = (100, 180, 0)
RED = (255, 0, 0)
BLACK = (0, 0, 0)
DARK_WHITE = (50, 50, 50)

BLOCK_WIDTH = 10
BLOCK_HEIGHT = 10

DEFAULT_FONT = pygame.font.Font("DejavuSansMono-5m7L.ttf", 15)


questionsTotal = 0
questionsRight = 0
questionsAnswered = []
# QUESTION_FILES = ["Q_A_test.txt"]
QUESTION_FILES = ["Q_A_easy.txt", "Q_A_medium.txt", "Q_A_hard.txt"]
for file in QUESTION_FILES:
    with open(file, "r") as qFile:
        lines = qFile.readlines()
        numQuestions = len(lines) / 5
        questionsTotal += numQuestions


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

        # Choose a couple of random walls in the maze and make them paths.
        totalWalls = 0
        for y in range(self.size * 2 + 1):
            for x in range(self.size * 2 + 1):
                totalWalls += self.grid[y][x]

        total = random.randint(int(0.06 * totalWalls), int(0.12 * totalWalls))
        count = 0
        while count < total:
            randColumn = random.randint(1, (self.size * 2 - 2))
            randRow = random.randint(1, (self.size * 2 - 2))
            # Check if 3 or more neighbors are walls. If so, skip.
            nTot = sum(
                1
                for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]
                if self.grid[randColumn + dy][randRow + dx] == 1
            )
            if self.grid[randColumn][randRow] == 1 and nTot < 3:
                count += 1
                self.grid[randColumn][randRow] = 0
        """
        totalWalls = 0
        for y in range(self.size * 2 + 1):
            for x in range(self.size * 2 + 1):
                totalWalls += self.grid[y][x]
        print(f"Walls: {totalWalls}")
        """
        # Enumerate all dead ends in the maze and chose one as the end point of the maze.
        dead_ends = self.find_dead_ends()
        if dead_ends:
            self.end = dead_ends[random.randint(-((len(dead_ends) // 4)), -1)]
        else:
            self.end = (self.size * 2 - 1, self.size * 2 - 1)

        return self.grid, self.end


class Game(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()

        self.frame_itter = 0

        arrow_sheet = SpriteSheet("arrow-sheet.png")
        self.arrow_sheet = arrow_sheet.make_sprite_array(0, 0, 10, 10, 4, 4)
        self.arrow_img = self.arrow_sheet[1]
        self.arrow_rect = self.arrow_img.get_rect()
        self.arrow_rect.x = BLOCK_WIDTH * 1
        self.arrow_rect.y = BLOCK_HEIGHT * 1

        walls_sheet = SpriteSheet("walls-sheet.png")
        self.walls_sheet = walls_sheet.make_sprite_array(0, 0, 194, 194, 19, 19, 2)
        self.walls_img = self.walls_sheet[0]
        self.walls_rect = self.walls_img.get_rect()
        self.walls_rect.x = max(210, MINIMAP_SIZE)
        self.walls_rect.y = 0

        self.toggleAltHallway = True

        self.lives = 3

        self.mazeLevel = 1
        self.scorePercent = (questionsRight / questionsTotal) * 100

        self.dir = [-1, 0]

        self.walls = []

        self.wallView = "111011010000"

        self.mazeSize = MAZE_SIZE

        newMaze = Maze(self.mazeSize)
        self.maze, self.mazeEnd = newMaze.generate()

        self.mazeHeight = len(self.maze)
        self.mazeWidth = len(self.maze[0])

        self.buildWalls(self.maze)

        # position mini map in the top left of screen
        self.miniMapBG = (
            0,
            0,
            BLOCK_WIDTH * self.mazeWidth,
            BLOCK_HEIGHT * self.mazeHeight,
        )

    def mazeGenerate(self):
        self.mazeLevel += 1
        self.dir = [-1, 0]
        newMaze = Maze(self.mazeSize)
        self.maze, self.mazeEnd = newMaze.generate()
        self.walls = []
        self.buildWalls(self.maze)
        self.arrow_img = self.arrow_sheet[1]
        self.arrow_rect = self.arrow_img.get_rect()
        self.arrow_rect.x = BLOCK_WIDTH * 1
        self.arrow_rect.y = BLOCK_HEIGHT * 1

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

    """ POTENTIALLY REMOVE BELOW FUNCTION """

    # method to animate dull long hall ways
    def toggleAltWall(self, index):
        # if index is at image 0 wich is a hallway and toggleAltHallway(toggled by Up_Arrow_key) is true
        if index == 0 and self.toggleAltHallway:
            # choose alternitive hallway image
            return 41
        else:
            # other wise just return original index
            return index

    def play_step(self):
        self.ui()

        # RIGHT
        if self.dir == [1, 0]:
            self.wallView = self.makeKey(self.checkRight())
            self.arrow_img = self.arrow_sheet[
                2
            ]  # show correct mini-map arrow direction

        # LEFT
        elif self.dir == [-1, 0]:
            self.wallView = self.makeKey(self.checkLeft())
            self.arrow_img = self.arrow_sheet[
                3
            ]  # show correct mini-map arrow direction

        # DOWN
        elif self.dir == [0, 1]:
            self.wallView = self.makeKey(self.checkDown())
            self.arrow_img = self.arrow_sheet[
                0
            ]  # show correct mini-map arrow direction

        # UP
        elif self.dir == [0, -1]:
            self.wallView = self.makeKey(self.checkUp())
            self.arrow_img = self.arrow_sheet[
                1
            ]  # show correct mini-map arrow direction

    # needs to be optimized right now renders some unseen walls but works for player
    def renderWalls(self):
        # always render background roof and floor
        self.screen.blit(self.walls_sheet[0], self.walls_rect)

        # row 4 ---------------------------------------------------------------
        # render wall infront of player
        if self.wallView[11] == "1":
            self.screen.blit(self.walls_sheet[18], self.walls_rect)

        # row 3 ---------------------------------------------------------------
        # wall to player front left+2
        if self.wallView[8] == "1":
            # render its front face and side face
            self.screen.blit(self.walls_sheet[2], self.walls_rect)
            self.screen.blit(self.walls_sheet[4], self.walls_rect)
        # wall to player front right+2
        if self.wallView[10] == "1":
            # render its front face and side face
            self.screen.blit(self.walls_sheet[1], self.walls_rect)
            self.screen.blit(self.walls_sheet[5], self.walls_rect)
        # render wall infront of player
        if self.wallView[9] == "1":
            self.screen.blit(self.walls_sheet[3], self.walls_rect)

        # row 2 ---------------------------------------------------------------
        # wall to player front left+1
        if self.wallView[5] == "1":
            # render its front face and side face
            self.screen.blit(self.walls_sheet[6], self.walls_rect)
            self.screen.blit(self.walls_sheet[8], self.walls_rect)
        # wall to player front right+1
        if self.wallView[7] == "1":
            # render its front face and side face
            self.screen.blit(self.walls_sheet[7], self.walls_rect)
            self.screen.blit(self.walls_sheet[9], self.walls_rect)
        # render wall infront of player
        if self.wallView[6] == "1":
            self.screen.blit(self.walls_sheet[12], self.walls_rect)

        # row 1 in front of player --------------------------------------------
        # wall to player front left
        if self.wallView[2] == "1":
            # render its front face and side face
            self.screen.blit(self.walls_sheet[10], self.walls_rect)
            self.screen.blit(self.walls_sheet[16], self.walls_rect)
        # wall to player front right
        if self.wallView[4] == "1":
            # render its front face and side face
            self.screen.blit(self.walls_sheet[11], self.walls_rect)
            self.screen.blit(self.walls_sheet[17], self.walls_rect)
        # render wall directly infront of player
        if self.wallView[3] == "1":
            self.screen.blit(self.walls_sheet[13], self.walls_rect)

        # row 0 containging player --------------------------------------------
        # render wall to your left peripheral
        if self.wallView[0] == "1":
            self.screen.blit(self.walls_sheet[15], self.walls_rect)
        # render wall to your right peripheral
        if self.wallView[1] == "1":
            self.screen.blit(self.walls_sheet[14], self.walls_rect)

    def ui(self):
        # Render
        self.screen.fill(BLACK)

        # Render 3d maze
        self.renderWalls()

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

        # Render text to show level
        levelText = DEFAULT_FONT.render(f"Level: {self.mazeLevel}", False, WHITE)
        self.screen.blit(levelText, (10, MINIMAP_SIZE))

        # Render text to show score
        scoreText = DEFAULT_FONT.render(
            f"Score: {self.scorePercent:.2f}%", False, WHITE
        )
        self.screen.blit(scoreText, (10, (MINIMAP_SIZE + 25)))

        # Render text to show lives
        livesText = DEFAULT_FONT.render(f"Lives: " + ("♥️ " * self.lives), False, WHITE)
        self.screen.blit(livesText, (10, (MINIMAP_SIZE + 50)))

        # Render question background
        qBkgTopLeftY = max(400, MINIMAP_SIZE + 75)
        qBkgTopLeftX = 10
        qBkgRect = pygame.Rect(
            qBkgTopLeftX,
            qBkgTopLeftY,
            (WIDTH - 20),
            130,
        )
        pygame.draw.rect(
            self.screen,
            DARK_WHITE,
            qBkgRect,
        )

        # Render mini map green arrow character
        self.screen.blit(self.arrow_img, self.arrow_rect)

    # these four functions give our character its line of sight checkUp(),checkDown(), checkRight(), checkLeft()
    def checkUp(self):
        # grab our current position
        pos = [self.arrow_rect.x // BLOCK_WIDTH, self.arrow_rect.y // BLOCK_HEIGHT]
        imageKey = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]

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

        # check front-left + 2 of player
        if pos[0] - 1 >= 0 and pos[1] - 3 >= 0:
            if self.maze[pos[0] - 1][pos[1] - 3] == 0:
                imageKey[8] = 0

        # check front-right + 2 of player
        if pos[0] + 1 < self.mazeWidth and pos[1] - 3 >= 0:
            if self.maze[pos[0] + 1][pos[1] - 3] == 0:
                imageKey[10] = 0

        # check front + 2
        if pos[1] - 3 >= 0:
            if self.maze[pos[0]][pos[1] - 3] == 0:
                imageKey[9] = 0

        # check front + 3
        if pos[1] - 4 >= 0:
            if self.maze[pos[0]][pos[1] - 4] == 0:
                imageKey[11] = 0

        # now we have built the correct image key for our character facing up
        return imageKey

    def checkDown(self):
        # grab our current position
        pos = [self.arrow_rect.x // BLOCK_WIDTH, self.arrow_rect.y // BLOCK_HEIGHT]
        imageKey = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]

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

        # check front-left + 2 of player
        if pos[0] + 1 >= 0 and pos[1] + 3 < self.mazeHeight:
            if self.maze[pos[0] + 1][pos[1] + 3] == 0:
                imageKey[8] = 0

        # check front-right + 2 of player
        if pos[0] - 1 < self.mazeWidth and pos[1] + 3 < self.mazeHeight:
            if self.maze[pos[0] - 1][pos[1] + 3] == 0:
                imageKey[10] = 0

        # check front + 2
        if pos[1] + 3 < self.mazeHeight:
            if self.maze[pos[0]][pos[1] + 3] == 0:
                imageKey[9] = 0

        # check front + 3
        if pos[1] + 4 < self.mazeHeight:
            if self.maze[pos[0]][pos[1] + 4] == 0:
                imageKey[11] = 0

        # now we have built the correct image key for our character facing down
        return imageKey

    def checkRight(self):
        pos = [self.arrow_rect.x // BLOCK_WIDTH, self.arrow_rect.y // BLOCK_HEIGHT]
        imageKey = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]

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

        # check front-left + 2 of player
        if pos[0] + 3 < self.mazeWidth and pos[1] - 1 >= 0:
            if self.maze[pos[0] + 3][pos[1] - 1] == 0:
                imageKey[8] = 0

        # check front-right + 2 of player
        if pos[0] + 3 < self.mazeWidth and pos[1] + 1 < self.mazeHeight:
            if self.maze[pos[0] + 3][pos[1] + 1] == 0:
                imageKey[10] = 0

        # check front + 2
        if pos[0] + 3 < self.mazeWidth:
            if self.maze[pos[0] + 3][pos[1]] == 0:
                imageKey[9] = 0

        # check front + 3
        if pos[0] + 4 < self.mazeWidth:
            if self.maze[pos[0] + 4][pos[1]] == 0:
                imageKey[11] = 0

        # now we have built the correct image key for our character facing right
        return imageKey

    def checkLeft(self):
        pos = [self.arrow_rect.x // BLOCK_WIDTH, self.arrow_rect.y // BLOCK_HEIGHT]
        imageKey = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]

        # check left of player
        if pos[1] + 1 >= 0:
            if self.maze[pos[0]][pos[1] + 1] == 0:
                imageKey[0] = 0

        # check right of player
        if pos[1] - 1 < self.mazeHeight:
            if self.maze[pos[0]][pos[1] - 1] == 0:
                imageKey[1] = 0

        # check front-left of player
        if pos[0] - 1 >= 0 and pos[1] + 1 >= 0:
            if self.maze[pos[0] - 1][pos[1] + 1] == 0:
                imageKey[2] = 0

        # check front-right of player
        if pos[0] - 1 >= 0 and pos[1] - 1 < self.mazeHeight:
            if self.maze[pos[0] - 1][pos[1] - 1] == 0:
                imageKey[4] = 0

        # check front of player if wall the rest of indexes are 1's
        if pos[0] - 1 >= 0:
            if self.maze[pos[0] - 1][pos[1]] == 0:
                imageKey[3] = 0

        # check front-left + 1 of player
        if pos[0] - 2 >= 0 and pos[1] + 1 >= 0:
            if self.maze[pos[0] - 2][pos[1] + 1] == 0:
                imageKey[5] = 0

        # check front-right + 1 of player
        if pos[0] - 2 >= 0 and pos[1] - 1 < self.mazeHeight:
            if self.maze[pos[0] - 2][pos[1] - 1] == 0:
                imageKey[7] = 0

        # check front + 1
        if pos[0] - 2 >= 0:
            if self.maze[pos[0] - 2][pos[1]] == 0:
                imageKey[6] = 0

        # check front-left + 2 of player
        if pos[0] - 3 >= 0 and pos[1] + 1 >= 0:
            if self.maze[pos[0] - 3][pos[1] + 1] == 0:
                imageKey[8] = 0

        # check front-right + 2 of player
        if pos[0] - 3 >= 0 and pos[1] - 1 < self.mazeHeight:
            if self.maze[pos[0] - 3][pos[1] - 1] == 0:
                imageKey[10] = 0

        # check front + 2
        if pos[0] - 3 >= 0:
            if self.maze[pos[0] - 3][pos[1]] == 0:
                imageKey[9] = 0

        # check front + 3
        if pos[0] - 4 >= 0:
            if self.maze[pos[0] - 4][pos[1]] == 0:
                imageKey[11] = 0

        # now we have built the correct image key for our character facing left
        return imageKey

    # These two functions handle the question retrieval and rendering.
    def choseQuestion(self):
        finishedSheet = True
        fileNum = 0
        while finishedSheet:
            qFile = QUESTION_FILES[fileNum]
            numQsInFile = 0
            with open(qFile, "r") as qfile:
                lines = qfile.readlines()
                numQsInFile = len(lines) // 5

            for i in range(numQsInFile):
                if (fileNum, i) not in questionsAnswered:
                    finishedSheet = False
                    break

                fileNum += 1
                if fileNum == len(QUESTION_FILES):
                    pygame.quit()
                    sys.exit("YOU WIN")

        while True:
            chosenQuestion = random.randint(0, (numQsInFile - 1))
            if (fileNum, chosenQuestion) not in questionsAnswered:
                break

        questionsAnswered.append((fileNum, chosenQuestion))

        with open(qFile, "r") as qFILE:
            lines = qFILE.readlines()

        qLine = chosenQuestion * 5
        question = lines[qLine].strip()
        correctAnswer = lines[qLine + 1].strip()
        possChars = [
            "a",
            "b",
            "c",
            "d",
        ]
        corrChar = random.choice(possChars)
        possChars.remove(corrChar)
        wrongAnswers = [
            lines[qLine + 2],
            lines[qLine + 3],
            lines[qLine + 4],
        ]
        random.shuffle(possChars)
        random.shuffle(wrongAnswers)
        answerChars = {
            corrChar: correctAnswer,
        }
        for i in range(3):
            answerChars[possChars[i]] = wrongAnswers[i].strip()

        return question, answerChars, corrChar

    def questionPrompt(self, question: str, answerChars: dict):
        # Display question and answers
        qBkgTopLeftY = max(400, MINIMAP_SIZE)
        qBkgTopLeftX = 10
        qBkgRect = pygame.Rect(
            qBkgTopLeftX,
            qBkgTopLeftY,
            (WIDTH - 20),
            130,
        )
        qWidth, qHeight = DEFAULT_FONT.size(question)
        if qWidth > (WIDTH - 50):
            qWords = question.split(" ")
            maxLen = 0
            for i in range(len(qWords)):
                testWidth, testHeight = DEFAULT_FONT.size(" ".join(qWords[:i]))
                if testWidth >= (WIDTH - 50):
                    maxLen = i - 1
                    break

            firstLine = " ".join(qWords[:maxLen])
            secondLine = " ".join(qWords[maxLen:])
            qText1 = DEFAULT_FONT.render(firstLine, False, WHITE)
            qText2 = DEFAULT_FONT.render(secondLine, False, WHITE)
            ansA = DEFAULT_FONT.render(f"a. {answerChars["a"]}", False, WHITE)
            ansB = DEFAULT_FONT.render(f"b. {answerChars["b"]}", False, WHITE)
            ansC = DEFAULT_FONT.render(f"c. {answerChars["c"]}", False, WHITE)
            ansD = DEFAULT_FONT.render(f"d. {answerChars["d"]}", False, WHITE)

            self.screen.blit(qText1, ((qBkgTopLeftX + 10), (qBkgTopLeftY + 10)))
            self.screen.blit(qText2, ((qBkgTopLeftX + 10), (qBkgTopLeftY + 30)))
            self.screen.blit(ansA, ((qBkgTopLeftX + 10), (qBkgTopLeftY + 50)))
            self.screen.blit(ansB, ((qBkgTopLeftX + 10), (qBkgTopLeftY + 70)))
            self.screen.blit(ansC, ((qBkgTopLeftX + 10), (qBkgTopLeftY + 90)))
            self.screen.blit(ansD, ((qBkgTopLeftX + 10), (qBkgTopLeftY + 110)))

        else:
            qText = DEFAULT_FONT.render(question, False, WHITE)
            ansA = DEFAULT_FONT.render(f"a. {answerChars["a"]}", False, WHITE)
            ansB = DEFAULT_FONT.render(f"b. {answerChars["b"]}", False, WHITE)
            ansC = DEFAULT_FONT.render(f"c. {answerChars["c"]}", False, WHITE)
            ansD = DEFAULT_FONT.render(f"d. {answerChars["d"]}", False, WHITE)

            self.screen.blit(qText, ((qBkgTopLeftX + 10), (qBkgTopLeftY + 10)))
            self.screen.blit(ansA, ((qBkgTopLeftX + 10), (qBkgTopLeftY + 30)))
            self.screen.blit(ansB, ((qBkgTopLeftX + 10), (qBkgTopLeftY + 50)))
            self.screen.blit(ansC, ((qBkgTopLeftX + 10), (qBkgTopLeftY + 70)))
            self.screen.blit(ansD, ((qBkgTopLeftX + 10), (qBkgTopLeftY + 90)))


game = Game()
questionActive = False
question = None
answerDict = None
correctAnswer = None
# Main game loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT and questionActive == False:
                game.turnLeft()

            if event.key == pygame.K_RIGHT and questionActive == False:
                game.turnRight()

            if event.key == pygame.K_UP and questionActive == False:
                # alternate image displayed for long hallways
                game.toggleAltHallway = not game.toggleAltHallway
                game.moveForward(game.dir)

            if event.key == pygame.K_SPACE:
                pos = (
                    game.arrow_rect.y // BLOCK_WIDTH,
                    game.arrow_rect.x // BLOCK_HEIGHT,
                )
                if pos == game.mazeEnd:
                    question, answerDict, correctAnswer = game.choseQuestion()
                    questionActive = True

            if event.key == pygame.K_q:
                pygame.quit()
                sys.exit()

            if event.key == pygame.K_z:
                # Debug re-generate maze to quicken testing
                game.mazeGenerate()

            if event.key == pygame.K_a and questionActive == True:
                # Check if letter chosen is the same as the correct answer.
                # If it is, increase score, set questionActive to false, and generate a new maze
                # If not, get a new question.
                if correctAnswer == "a":
                    questionsRight += 1
                    game.scorePercent = (questionsRight / questionsTotal) * 100
                    questionActive = False
                    if game.lives < 3:
                        game.lives += 1
                    game.mazeGenerate()
                else:
                    game.lives -= 1
                    if game.lives <= 0:
                        pygame.quit()
                        # Print score and level
                        sys.exit("Game Over")
                    else:
                        question, answerDict, correctAnswer = game.choseQuestion()

            if event.key == pygame.K_b and questionActive == True:
                # Check if letter chosen is the same as the correct answer.
                # If it is, increase score, set questionActive to false, and generate a new maze
                # If not, get a new question.
                if correctAnswer == "b":
                    questionsRight += 1
                    game.scorePercent = (questionsRight / questionsTotal) * 100
                    questionActive = False
                    if game.lives < 3:
                        game.lives += 1
                    game.mazeGenerate()
                else:
                    game.lives -= 1
                    if game.lives <= 0:
                        pygame.quit()
                        # Print score and level
                        sys.exit("Game Over")
                    else:
                        question, answerDict, correctAnswer = game.choseQuestion()

            if event.key == pygame.K_c and questionActive == True:
                # Check if letter chosen is the same as the correct answer.
                # If it is, increase score, set questionActive to false, and generate a new maze
                # If not, get a new question.
                if correctAnswer == "c":
                    questionsRight += 1
                    game.scorePercent = (questionsRight / questionsTotal) * 100
                    questionActive = False
                    if game.lives < 3:
                        game.lives += 1
                    game.mazeGenerate()
                else:
                    game.lives -= 1
                    if game.lives <= 0:
                        pygame.quit()
                        # Print score and level
                        sys.exit("Game Over")
                    else:
                        question, answerDict, correctAnswer = game.choseQuestion()

            if event.key == pygame.K_d and questionActive == True:
                # Check if letter chosen is the same as the correct answer.
                # If it is, increase score, set questionActive to false, and generate a new maze
                # If not, get a new question.
                if correctAnswer == "d":
                    questionsRight += 1
                    game.scorePercent = (questionsRight / questionsTotal) * 100
                    questionActive = False
                    if game.lives < 3:
                        game.lives += 1
                    game.mazeGenerate()
                else:
                    game.lives -= 1
                    if game.lives <= 0:
                        pygame.quit()
                        # Print score and level
                        sys.exit("Game Over")
                    else:
                        question, answerDict, correctAnswer = game.choseQuestion()

    game.play_step()
    if questionActive:
        pos = (
            game.arrow_rect.y // BLOCK_WIDTH,
            game.arrow_rect.x // BLOCK_HEIGHT,
        )
        if pos == game.mazeEnd:
            game.questionPrompt(question, answerDict)
    game.clock.tick(60)
    pygame.display.flip()
