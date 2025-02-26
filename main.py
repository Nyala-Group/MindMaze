import pygame
import random

pygame.init()
pygame.display.set_caption("Mind Maze!")

# Constants
WIDTH = 610
HEIGHT = 400
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
GREEN = (100, 180, 0)
RED = (255, 0, 0)
BLACK = (0, 0, 0)
DARK_WHITE = (50, 50, 50)

BLOCK_WIDTH = 10
BLOCK_HEIGHT = 10

DEFAULT_FONT = pygame.font.Font(pygame.font.get_default_font(), 15)

questionsTotal = 0
questionsRight = 0
questionsAnswered = []
QUESTION_FILES = [
    "Q_A_test.txt",
]
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
        self.walls_rect.x = 210
        self.walls_rect.y = 0

        self.toggleAltHallway = True

        self.mazeLevel = 1
        self.scorePercent = (questionsRight / questionsTotal) * 100

        self.dir = [-1, 0]

        self.walls = []

        self.wallView = "111011010000"

        newMaze = Maze(10)
        self.maze, self.mazeEnd = newMaze.generate()

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

    def mazeGenerate(self):
        self.mazeLevel += 1
        self.dir = [-1, 0]
        newMaze = Maze(10)
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
            self.screen.blit(self.walls_sheet[1], self.walls_rect)
            self.screen.blit(self.walls_sheet[4], self.walls_rect)
        # wall to player front right+2
        if self.wallView[10] == "1":
            # render its front face and side face
            self.screen.blit(self.walls_sheet[2], self.walls_rect)
            self.screen.blit(self.walls_sheet[5], self.walls_rect)
        # render wall infront of player
        if self.wallView[9] == "1":
            self.screen.blit(self.walls_sheet[3], self.walls_rect)

        # row 2 ---------------------------------------------------------------
        # wall to player front left+1
        if self.wallView[5] == "1":
            # render its front face and side face
            self.screen.blit(self.walls_sheet[7], self.walls_rect)
            self.screen.blit(self.walls_sheet[9], self.walls_rect)
        # wall to player front right+1
        if self.wallView[7] == "1":
            # render its front face and side face
            self.screen.blit(self.walls_sheet[8], self.walls_rect)
            self.screen.blit(self.walls_sheet[10], self.walls_rect)
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
        self.screen.blit(levelText, (10, 210))

        # Render text to show score
        scoreText = DEFAULT_FONT.render(
            f"Score: {self.scorePercent:.2f}%", False, WHITE
        )
        self.screen.blit(scoreText, (10, 235))

        # Render mini map green arrow character
        self.screen.blit(self.arrow_img, self.arrow_rect)

        self.clock.tick(60)
        pygame.display.flip()

    # these last four functions give our character its line of sight checkUp(),checkDown(), checkRight(), checkLeft()
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

        # now we have built the correct image key for our character facing down
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

        # now we have built the correct image key for our character facing down
        return imageKey

    def checkLeft(self):
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

        # check front-left + 2 of player
        if pos[0] - 3 >= 0 and pos[1] - 1 >= 0:
            if self.maze[pos[0] - 3][pos[1] - 1] == 0:
                imageKey[8] = 0

        # check front-right + 2 of player
        if pos[0] - 3 >= 0 and pos[1] + 1 < self.mazeHeight:
            if self.maze[pos[0] - 3][pos[1] + 1] == 0:
                imageKey[10] = 0

        # check front + 2
        if pos[0] - 3 >= 0:
            if self.maze[pos[0] - 3][pos[1]] == 0:
                imageKey[9] = 0

        # check front + 3
        if pos[0] - 4 >= 0:
            if self.maze[pos[0] - 4][pos[1]] == 0:
                imageKey[11] = 0

        # now we have built the correct image key for our character facing down
        return imageKey

    def questionPrompt(self):
        # Move the question selection thing to a one-time process in the space key detection and input the question and answer dict in here as args?
        finishedSheet = True
        fileNum = 0
        while finishedSheet:
            qFile = QUESTION_FILES[fileNum]
            numQsInFile = 0
            with open(qFile, "r") as qfile:
                lines = qfile.readlines()
                numQsInFile = len(lines) // 5

            for i in range(numQsInFile):
                if (fileNum, (i + 1)) not in questionsAnswered:
                    finishedSheet = False
                    break

                fileNum += 1

        while True:
            chosenQuestion = random.randint(0, (numQsInFile - 1))
            if (fileNum, chosenQuestion) not in questionsAnswered:
                break

        questionsAnswered.append((fileNum, chosenQuestion))

        with open(qFile, "r") as qFILE:
            lines = qFILE.readlines()

        qLine = chosenQuestion * 5
        question = lines[qLine]
        correctAnswer = lines[qLine + 1]
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
            answerChars[possChars[i]] = wrongAnswers[i]

        # Display question and answers - Perhaps in a pop-up?

        questionText = f"{question}a. {answerChars["a"]}b. {answerChars["b"]}c. {answerChars["c"]}d. {answerChars["d"]}"
        qWidth, qHeight = DEFAULT_FONT.size(question)
        qHeight *= 5
        qBkgTopLeftY = 10
        qBkgTopLeftX = (WIDTH // 2) - (qWidth // 2)
        qBkgRect = pygame.Rect(
            qBkgTopLeftX,
            qBkgTopLeftY,
            (qWidth + 20),
            (qHeight + 20),
        )
        qText = DEFAULT_FONT.render(questionText, False, WHITE)

        """
        Need to finish this function.
        Render the question background Rect in BLACK,
        then render the question text on top of that in WHITE
        Check for user key press of a, b, c, or d and correlate that with the correct character stored in corrChar
        if right, return True
        if wrong, return False
        """
        answered = False
        return answered
        # The following code is broken, completely freezes the game.
        while not answered:
            pygame.draw.rect(
                self.screen,
                BLACK,
                qBkgRect,
            )
            self.screen.blit(qText, ((qBkgTopLeftX + 10), 20))
            self.clock.tick()


game = Game()
# Main game loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                game.turnLeft()

            if event.key == pygame.K_RIGHT:
                game.turnRight()

            if event.key == pygame.K_UP:
                # alternate image displayed for long hallways
                game.toggleAltHallway = not game.toggleAltHallway
                game.moveForward(game.dir)

            if event.key == pygame.K_SPACE:
                pos = (
                    game.arrow_rect.y // BLOCK_WIDTH,
                    game.arrow_rect.x // BLOCK_HEIGHT,
                )
                if pos == game.mazeEnd:
                    # This is where questions will be presented, in a while loop.
                    # questionAnswered = False
                    # while not questionAnswered:
                    # Present question
                    # If True, break.
                    # If False, continue.
                    questionActive = True

            if event.key == pygame.K_q:
                pygame.quit()

            if event.key == pygame.K_z:
                # Debug re-generate maze to quicken testing
                game.mazeGenerate()

    game.play_step()
    if questionActive:
        game.questionPrompt()
