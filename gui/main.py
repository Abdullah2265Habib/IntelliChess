import pygame
import chess
import random
import sys
import os

from utils import loadImages, mouseToSquare
from board import displayBoard, drawPieces, highlightValidMoves, drawValidMoves

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from pgn.savePGN import saveGamePGN

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'engine')))
from engine.opening_book.opening_book import OpeningBook

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

def getGameStatus(board, opening_book = None):
    if board.is_checkmate():
        status = "Checkmate! " + ("Black" if board.turn else "White") + " wins!"
    elif board.is_stalemate():
        status = "Stalemate! Draw!"
    elif board.is_insufficient_material():
        status = "Draw by insufficient material!"
    elif board.is_check():
        status = "Check!"
    else:
        status = "2-Player Chess - " + ("White's turn" if board.turn else "Black's turn")

    # Add opening name if in opening phase
    if opening_book and board.ply() < 10:
        try:
            opening_name = opening_book.get_opening_name(board)
            if opening_name != "Unknown Opening":
                status += f" | {opening_name}"
        except:
            pass  # Ignore errors

    return status
#getting random bot moves
def getBotMove(board, opening_book=None):
    if opening_book and board.ply() < 20:
        opening_move = opening_book.get_opening_move(board)
        if opening_move:
            return opening_move
    
    # Fall back to random move if no opening book move found
    return random.choice(list(board.legal_moves))
def main():
    isGameOver = False

    BOT_PLAYS_WHITE = False  #or true if i want bot to go first
    pygame.init()
    board = chess.Board()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    images = loadImages(SQUARESIZE)
    selectedSquare = None
    running = True

    try:
        base_dir =os.path.join("engine", "opening_book", "dataset")
        opening_book=OpeningBook(base_dir=base_dir,max_ply= 10)
    except Exception as e:
        opening_book= None
        print("nothing here X(")
    running = True
    while running:

        displayBoard(screen)
        if selectedSquare is not None:
            highlightValidMoves(screen, selectedSquare)
            drawValidMoves(screen, board, selectedSquare)
        drawPieces(screen, board, images)
    
        status_text = getGameStatus(board, opening_book)
        pygame.display.set_caption(status_text)
    
        pygame.display.flip()
        clock.tick(60)

        for event in pygame.event.get():
            if board.is_game_over() and not isGameOver:
                saveGamePGN(board)
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
                board.push(getBotMove(board, opening_book))
                selectedSquare = None
            elif board.turn == chess.BLACK and not BOT_PLAYS_WHITE:
                pygame.time.wait(300)
                board.push(getBotMove(board, opening_book))
                selectedSquare = None


    pygame.quit()

if __name__ == "__main__":
    import os
    print("Current directory:", os.getcwd())
    print("Files in engine/opening_book/:")
    engine_path = os.path.join(os.path.dirname(__file__), '..', 'engine', 'opening_book')
    if os.path.exists(engine_path):
        print(os.listdir(engine_path))
    else:
        print("Path doesn't exist:", engine_path)
    main()