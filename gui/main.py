import pygame
import chess
from utils import loadImages, mouseToSquare



"""The main.py will contail the loop and it will control the game
    the utils.py contains the images and we will load it into the board for piece representatino
    board.pyit will handle draweing and UI logic for the board"""

# well board.py will be slow. instead if we use bitboard it will be VERY EFFECTIVE in respect of time and analyzing.

#defining the screen :)
WIDTH, HEIGHT = 480, 480
#aagar board ka size 480 hai.......then let x=480.........size of one block will be x/8;
SQUARESIZE = WIDTH / 8  #This can return a float number if we want to increas the size of the screen, like moving towards streamlit....it will create problems :(
SQUARESIZE = int(SQUARESIZE)

# i am blank here :) first i need to make board.py to represent the chess board

