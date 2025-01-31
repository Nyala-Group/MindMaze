# Nyala Group MindMaze
# Chief Programmer - Lucas Ramage
# General Programmer - Michael Galloway

import pygame
import random

# Define constants
CELL_SIZE = 20
MARGIN = 10
WALL_COLOR = (0, 0, 0)
PATH_COLOR = (255, 255, 255)
START_COLOR = (0, 255, 0)
END_COLOR = (255, 0, 0)


class Maze:
    # A class to handle all of the maze generation
    def __init__(self, size):
        # Initialize based on the size parameter, making a square grid
        self.size = size
        self.grid = [[0 for _ in range(size * 2 + 1)] for _ in range(size * 2 + 1)]
        self.visited = [[False for _ in range(size)] for _ in range(size)]
        self.stack = []

    def in_bounds(self, x, y):
        # Make sure the generation algorithm does not go out of bounds
        return 0 <= x < self.size and 0 <= y < self.size

    def get_neighbors(self, x, y):
        # A function to get the neighbor cells for a given cell
        neighbors = []
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        random.shuffle(
            directions
        )  # Shuffles the directions to increase the randomness of the maze
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
                if self.grid[y][x] == 1:
                    neighbors = sum(
                        1
                        for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]
                        if self.grid[y + dy][x + dx] == 1
                    )
                    if neighbors == 1:
                        dead_ends.append((x, y))
        return dead_ends

    def carve_path(self, x1, y1, x2, y2):
        # A function to carve a path, setting a given point as a path and setting the cell between the given point and the second point as a path
        gx1, gy1 = x1 * 2 + 1, y1 * 2 + 1
        gx2, gy2 = x2 * 2 + 1, y2 * 2 + 1
        self.grid[(gy1 + gy2) // 2][(gx1 + gx2) // 2] = 1
        self.grid[gy2][gx2] = 1

    def generate(self):
        # A function that handles the maze generation
        start_x, start_y = 0, 0  # Start at top-left corner
        self.grid[start_x * 2 + 1][
            start_y * 2 + 1
        ] = 1  # Sets the top left corner as a path
        self.visited[start_y][start_x] = True  # Marks the top left corner as visited
        self.stack.append((start_x, start_y))  # Appends the start cell to the stack

        while self.stack:
            x, y = self.stack[-1]  # Select the first item in the stack (Or the last)
            neighbors = self.get_neighbors(
                x, y
            )  # Get all the neighbors of the selected cell
            if neighbors:
                nx, ny = random.choice(neighbors)  # Choose a random neighbor
                self.carve_path(
                    x, y, nx, ny
                )  # Carve a path between the selected cell and the selected neighbor
                self.visited[ny][nx] = True  # Mark the neighbor as visited
                self.stack.append((nx, ny))  # Append the neighbor to the stack
            else:
                self.stack.pop()  # Pop the last item from the stack if there are no remaining unvisited neighbors

        # Assign start and end points after generating the maze
        dead_ends = self.find_dead_ends()  # Get all of the dead ends within the maze
        if dead_ends:
            self.start = dead_ends[random.randint(0, (len(dead_ends) // 10))]
            self.end = dead_ends[random.randint(-((len(dead_ends) // 4)), -1)]
        else:
            self.start = (1, 1)
            self.end = (self.size * 2 - 1, self.size * 2 - 1)


# Pygame rendering function
def draw_maze(screen, maze):
    expanded_size = maze.size * 2 + 1
    for y in range(expanded_size):
        for x in range(expanded_size):
            color = PATH_COLOR if maze.grid[y][x] == 1 else WALL_COLOR
            rect = pygame.Rect(
                x * CELL_SIZE + MARGIN, y * CELL_SIZE + MARGIN, CELL_SIZE, CELL_SIZE
            )
            pygame.draw.rect(screen, color, rect)

    start_x, start_y = maze.start
    end_x, end_y = maze.end
    pygame.draw.rect(
        screen,
        START_COLOR,
        pygame.Rect(
            start_x * CELL_SIZE + MARGIN,
            start_y * CELL_SIZE + MARGIN,
            CELL_SIZE,
            CELL_SIZE,
        ),
    )
    pygame.draw.rect(
        screen,
        END_COLOR,
        pygame.Rect(
            end_x * CELL_SIZE + MARGIN, end_y * CELL_SIZE + MARGIN, CELL_SIZE, CELL_SIZE
        ),
    )


# Pygame setup
def main():
    grid_size = 16  # Default grid size
    maze = Maze(grid_size)
    maze.generate()
    expanded_size = grid_size * 2 + 1
    screen_size = (
        expanded_size * CELL_SIZE + 2 * MARGIN,
        expanded_size * CELL_SIZE + 2 * MARGIN,
    )

    pygame.init()
    screen = pygame.display.set_mode(screen_size)
    pygame.display.set_caption("Maze Generator")
    clock = pygame.time.Clock()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_z:
                maze = Maze(grid_size)
                maze.generate()
        screen.fill(WALL_COLOR)
        draw_maze(screen, maze)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        clock.tick(30)

    pygame.quit()


if __name__ == "__main__":
    main()
