import pygame
import chess
import random
import sys
import os
import time

pygame.init()
from utils import load_font, loadImages
from board import displayBoard, drawPieces, highlightValidMoves, drawValidMoves
from board import MARGIN_TOP, MARGIN_BOTTOM
from timer import ChessTimer #type:ignore
from menu import show_menu 

# PGN & Opening Book imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from pgn.savePGN import saveGamePGN
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'engine')))
from engine.opening_book.opening_book import OpeningBook
"""The main.py will contail the loop and it will control the game
    the utils.py contains the images and we will load it into the board for piece representatino
    board.pyit will handle draweing and UI logic for the board"""

# well board.py will be slow. instead if we use bitboard it will be VERY EFFECTIVE in respect of time and analyzing.

#defining the screen :)
WIDTH, HEIGHT = 480, 600
#aagar board ka size 480 hai.......then let x=480.........size of one block will be x/8;
SQUARESIZE = int(WIDTH / 8)  #This can return a float number if we want to increas the size of the screen, like moving towards streamlit....it will create problems :(
BOARD_TOP = MARGIN_TOP 
BOARD_BOTTOM = BOARD_TOP + 8 * SQUARESIZE

font = load_font(size=60)

# i am blank here :) first i need to make board.py to represent the chess board
def getGameStatus(board, opening_book=None):
    if board.is_checkmate():
        status = "Checkmate! " + ("Black" if board.turn else "White") + " wins!"
    elif board.is_stalemate():
        status = "Stalemate! Draw!"
    elif board.is_insufficient_material():
        status = "Draw by insufficient material!"
    elif board.is_check():
        status = "Check!"
    else:
        status = "Intellichess - " + ("White's move" if board.turn else "Black's move")
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

    BOT_PLAYS_WHITE = False #or true if i want bot to go first
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Intellichess")
    clock = pygame.time.Clock()  

    images = loadImages(SQUARESIZE)
    selected_time = show_menu(screen)  # Lets player pick time before starting
    timer = ChessTimer(total_time=selected_time)  # Adds countdown clocks

    # Adjust Font for timer
    font_path = os.path.join("GUI", "fonts", "Orbitron-Regular.ttf")
    if not os.path.exists(font_path):
        print("Font not found, using default font instead.")
        timer_font = pygame.font.SysFont("impact", 22)
    else:
        timer_font = pygame.font.Font(font_path, 22)
    board = chess.Board()
    selectedSquare = None
    
    

    try:
        base_dir = os.path.join("engine", "opening_book", "dataset")
        opening_book = OpeningBook(base_dir=base_dir, max_ply=10)
    except Exception as e:
        opening_book = None
        print("nothing here X(")
    running = True

    while running:
        BACKGROUND_COLOR = (40, 40, 40)
        screen.fill(BACKGROUND_COLOR)

        # Draw everything
        displayBoard(screen)
        if selectedSquare is not None:
            highlightValidMoves(screen, selectedSquare)
            drawValidMoves(screen, board, selectedSquare)
        drawPieces(screen, board, images)

        # Update and display  Timers
        timer.update()
        timer.draw(screen, timer_font)

        # Ends game if time runs out: Check timeout
        if timer.remaining_white <= 0 or timer.remaining_black <= 0:
            winner = "Computer" if timer.remaining_white <= 0 else "White"
            text = timer_font.render(f"Time Out! {winner} Wins!", False, (230, 210, 40))
            screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2))
            pygame.display.flip()
            time.sleep(3)
            running = False
            continue

        # Window title
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
                x, y = event.pos 

                # Margins checks: Ignore clicks outside the chessboard area
                if not (BOARD_TOP <= y <= BOARD_BOTTOM):
                    continue

                #  Adjust Y for the top margin
                col = x // SQUARESIZE
                row = (y - BOARD_TOP) // SQUARESIZE
                square = chess.square(col, 7 - row)

                # Select or move piece
                if selectedSquare is None:
                    if board.piece_at(square) and board.piece_at(square).color == board.turn:
                        selectedSquare = square
                else:
                    move = chess.Move(selectedSquare, square)
                    if (
                        board.piece_at(selectedSquare)
                        and board.piece_at(selectedSquare).piece_type == chess.PAWN
                        and chess.square_rank(square) in [0, 7]
                    ):
                        move = chess.Move(selectedSquare, square, promotion=chess.QUEEN)

                    if move in board.legal_moves:
                        board.push(move)
                        timer.switch_turn()
                    selectedSquare = None

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                selectedSquare = None

            elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                board = chess.Board()
                timer = ChessTimer(total_time=selected_time)
                selectedSquare = None
                isGameOver = False
        if not board.is_game_over():
            if board.turn == chess.WHITE and BOT_PLAYS_WHITE:
                            pygame.time.wait(300)
                            board.push(getBotMove(board, opening_book))
                            timer.switch_turn() # add timer to switch turns
                            selectedSquare = None
            elif board.turn == chess.BLACK and not BOT_PLAYS_WHITE:
                # Simulate computer thinking time (1–3 seconds)
                start_think = time.time()
                think_duration = random.uniform(1, 3)

                while time.time() - start_think < think_duration:
                    BACKGROUND_COLOR = (40, 40, 40)
                    screen.fill(BACKGROUND_COLOR)            # to clear old frame

                    displayBoard(screen)                     # redraw the board
                    drawPieces(screen, board, images)        # redraw the pieces
                    timer.update()
                    timer.draw(screen, timer_font)           # now safe to draw text
                    pygame.display.flip()
                    clock.tick(30)


                # After thinking time, make the move
                board.push(getBotMove(board, opening_book))
                timer.switch_turn()
                selectedSquare = None


        

    pygame.quit()



if __name__ == "__main__":
    # import os
    # print("Current directory:", os.getcwd())
    # print("Files in engine/opening_book/:")
    # engine_path = os.path.join(os.path.dirname(__file__), '..', 'engine', 'opening_book')
    # if os.path.exists(engine_path):
    #     print(os.listdir(engine_path))
    # else:
    #     print("Path doesn't exist:", engine_path)
    main()