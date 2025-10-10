import pygame
import chess
from utils import loadImages, mouseToSquare
from board import displayBoard, drawPieces, highlightValidMoves, drawValidMoves
import random
#path fro PGN directory to save the game in PGN format as it is in another directory so to use it we will nedd to import it
import sys
import os
# Add root directory to system path so we can import from PGN/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pgn.savePGN import saveGamePGN


"""The main.py will contail the loop and it will control the game
    the utils.py contains the images and we will load it into the board for piece representatino
    board.pyit will handle draweing and UI logic for the board"""

# well board.py will be slow. instead if we use bitboard it will be VERY EFFECTIVE in respect of time and analyzing.

#defining the screen :)
WIDTH, HEIGHT = 480, 480
#aagar board ka size 480 hai.......then let x=480.........size of one block will be x/8;
SQUARESIZE = WIDTH / 8  #This can return a float number if we want to increas the size of the screen, like moving towards streamlit....it will create problems :(
#we can also typcast the above into int by // double division sign 
# and the other method is below
SQUARESIZE = int(SQUARESIZE)

# i am blank here :) first i need to make board.py to represent the chess board

def getGameStatus(board): #THIS FUNCTION WILL RETURN THE STATUS OF THE GAME
    if board.is_checkmate():
        return "Checkmate! " + ("Black" if board.turn else "White") + " wins!"
    elif board.is_stalemate(): # no legal modes available 
        return "Stalemate! Draw!"
    elif board.is_insufficient_material():
        return "Draw by insufficient material!"
    elif board.is_check():
        return "Check!"
    else:
        return "2-Player Chess - " + ("White's turn" if board.turn else "Black's turn")

#getting random bot moves
def getBotMove(board):
    return random.choice(list(board.legal_moves)) #legal random move
def main():
    isGameOver = False
    # who plays first black/white
    BOT_PLAYS_WHITE = False  #or true if i want bot to go first
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("2-Player Chess")
    clock = pygame.time.Clock()
    board = chess.Board()
    images = loadImages(SQUARESIZE)
    selectedSquare = None
    running = True

    while running:
        displayBoard(screen)
        if selectedSquare is not None:
            highlightValidMoves(screen, selectedSquare)
            drawValidMoves(screen, board, selectedSquare)
        drawPieces(screen, board, images)
        pygame.display.set_caption(getGameStatus(board))
        pygame.display.flip() #
        clock.tick(60)  #Frame Rate:how many times gets our screen update like 60 then 60 times
        #GPU uses it
        for event in pygame.event.get():
            if board.is_game_over() and not isGameOver:
                saveGamePGN(board)  #PGN:text format  to save the moves of a game in a file
                isGameOver = True
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and not board.is_game_over():
                square = mouseToSquare(event.pos, SQUARESIZE)
                if selectedSquare is None:
                    if board.piece_at(square) and board.piece_at(square).color == board.turn:
                        selectedSquare = square
                else:
                    move = chess.Move(selectedSquare, square)
                    if (board.piece_at(selectedSquare) and 
                        board.piece_at(selectedSquare).piece_type == chess.PAWN and 
                        chess.square_rank(square) in [0, 7]):
                        move = chess.Move(selectedSquare, square, promotion=chess.QUEEN)
                    if move in board.legal_moves:
                        board.push(move)
                    selectedSquare = None

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                selectedSquare = None

            elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                board = chess.Board()
                selectedSquare = None

        if not board.is_game_over():
            if board.turn == chess.WHITE and BOT_PLAYS_WHITE:
                pygame.time.wait(300)
                board.push(getBotMove(board))
                selectedSquare = None
            elif board.turn == chess.BLACK and not BOT_PLAYS_WHITE:
                pygame.time.wait(300)
                board.push(getBotMove(board))
                selectedSquare = None


    pygame.quit()

if __name__ == "__main__":
    main()