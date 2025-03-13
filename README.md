# Mind Maze!
## Description
Mind Maze is a procedurally generated maze game built using Python and Pygame. Players navigate through the maze from a first-person perspective, solving increasingly complex labyrinths and answering Computer Science questions along the way. The game dynamically generates new mazes upon completion, providing a challenge until all available questions have been posed. The game will feature a system that punishes the player for incorrect questions and can result in a game over.
## Features
•	Procedural maze generation

•	First-person perspective navigation

•	Sprite-based rendering with sprite sheets

•	Dynamic difficulty scaling

•	Mini-map for guidance

•	Interactive player controls

##Installation
###Requirements
Ensure you have Python installed on your system. You will also need the Pygame library.

1.	Install Python (if not already installed) from python.org

2.	Install Pygame using pip:
pip install pygame

##How to Play
1.	Run the game by executing the following command:

python mind_maze.py

2.	Controls:

  • Arrow Keys:

  • Left Arrow: Turn left

  • Right Arrow: Turn right

  • Up Arrow: Move forward

  • Spacebar: Check position or advance when at the maze exit

  • Q: Quit the game

3.	Navigate through the maze and reach the end point marked in red.

4.	Once you reach the exit, a new maze is generated with increased complexity.

## File Structure
•	mind_maze.py - Main game file

•	arrow-sheet.png - Sprite sheet for directional indicators

•	maze-sheet.png - Sprite sheet for maze rendering

•	walls-sheet.png - Sprite sheet for walls and backgrounds

•	Multiple choice questions for opening doors

•	Health system for if player gets questions wrong

## Future Improvements
•	Implement sound effects and background music?

•	Locked doors

