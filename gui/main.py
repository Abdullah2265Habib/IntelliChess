import pygame
import chess
import random
import sys
import os
import time
import traceback

pygame.init()
from utils import load_font, loadImages
from board import displayBoard, drawPieces, highlightValidMoves, drawValidMoves
from board import MARGIN_TOP, MARGIN_BOTTOM
from timer import ChessTimer
from menu import show_menu 
from turn import getTurnFromButton

# PGN & Opening Book imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from pgn.savePGN import saveGamePGN
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'engine')))
#from engine.opening_book.opening_book import OpeningBook
from engine.opening_book.opening_book import OpeningBook
from engine.endgame.endgame import EndgameEngine
from engine.engine import get_bot_move
# Alpha-Beta Pruning imports
from engine.alphabeta_pruning import minimax_with_alphabeta, return_bestMove_and_bestValue

WIDTH, HEIGHT = 480, 600
SQUARESIZE = int(WIDTH / 8)  
BOARD_TOP = MARGIN_TOP 
BOARD_BOTTOM = BOARD_TOP + 8 * SQUARESIZE

def getGameStatus(board, opening_book=None, endgame_engine=None):
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
            pass
    
    # Add endgame evaluation if in endgame
    if endgame_engine and endgame_engine.is_endgame(board):
        try:
            eval_text = endgame_engine.get_tablebase_evaluation(board)
            if eval_text != "Unknown":
                status += f" | {eval_text}"
        except:
            pass
    
    return status

def getBotMove(board, opening_book=None, endgame_engine=None):
 
     # 1. Opening book moves for first 20 plies
    if opening_book and board.ply() < 20:
        opening_move = opening_book.get_opening_move(board)
        if opening_move:
            print("Using opening book move")
            return opening_move
    # 2. Endgame tablebases
    if endgame_engine and endgame_engine.is_endgame(board):
        endgame_move = endgame_engine.get_best_move(board)
        if endgame_move:
            print("Using endgame engine move")
            return endgame_move
    # 3. Alpha-beta for midgame
    try:
        print("Using alpha-beta")
        # call get_bot_move defensively in case signature is different in your engine
        try:
            best_move = get_bot_move(board, opening_book, endgame_engine)
        except TypeError:
            best_move = get_bot_move(board)
        if best_move is not None:
            return best_move
    except Exception as e:
        # Print full traceback + helpful debug info so you can trace "list index out of range"
        print("Alpha-beta error:", e)
        traceback.print_exc()
        try:
            print("Board FEN:", board.fen())
            legal_moves = list(board.legal_moves)
            print("Legal moves count:", len(legal_moves))
        except Exception:
            pass
    
    # Fallback to random move (guard against empty move list)
    legal_moves = list(board.legal_moves)
    if legal_moves:
        print("Using random move")
        return random.choice(legal_moves)
    else:
        print("No legal moves available to pick as fallback")
        return None


def main():  
    isGameOver = False

    BOT_PLAYS_WHITE = getTurnFromButton()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Intellichess")
    clock = pygame.time.Clock()  

    font = load_font(size=60)

    images = loadImages(SQUARESIZE)
    selected_time = show_menu(screen)  # Lets player pick time before starting
    timer = ChessTimer(total_time=selected_time)  # Adds countdown clocks

    # Adjust Font for timer
    #font_path = os.path.join("GUI", "font", "Orbitron-Bold.ttf")
    font_dir = os.path.join(os.path.dirname(__file__), "font")
    font_path = os.path.join(font_dir, "Orbitron-Bold.ttf")

    if not os.path.exists(font_path):
        print("Font not found, using default font instead.")
        timer_font = pygame.font.SysFont("impact", 22)
    else:
        timer_font = pygame.font.Font(font_path, 22)
    board = chess.Board()
    selectedSquare = None
    
    # Initialize opening book
    try:
        base_dir = os.path.join("engine", "opening_book", "dataset")
        opening_book = OpeningBook(base_dir=base_dir, max_ply=10)
    except Exception as e:
        opening_book = None
        print("Opening book not available:", e)
    
    # Initialize endgame engine
    try:
        # Get the script's directory and construct absolute path
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # Go up one level from gui/ to project root, then to engine/tablebases/syzygy
        tablebase_path = os.path.join(script_dir, "..", "engine", "tablebases", "syzygy")
        tablebase_path = os.path.normpath(tablebase_path)
        
        print(f"Looking for tablebases at: {tablebase_path}")
        endgame_engine = EndgameEngine(tablebase_path=tablebase_path)
    except Exception as e:
        endgame_engine = None
        print("Endgame engine not available:", e)
    
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

        # Update and display Timers
        timer.update()
        timer.draw(screen, timer_font)

        # Check for time-out: if either player's time runs out, end the game
        if timer.remaining_white <= 0 or timer.remaining_black <= 0:
            winner = "Black" if timer.remaining_white <= 0 else "White"
            text = timer_font.render(f"Time Out! {winner} Wins!", False, (230, 210, 40))
            screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2))
            pygame.display.flip()
            time.sleep(3)  # Pause to display the message

            # Save the PGN before exiting
            saveGamePGN(board)
            running = False  # End the game
            continue  # Exit to the next loop iteration to stop the game

        # Update the window title
        status_text = getGameStatus(board, opening_book, endgame_engine)
        pygame.display.set_caption(status_text)

        # Display endgame info if in endgame
        if endgame_engine and endgame_engine.is_endgame(board):
            try:
                eval_text = endgame_engine.get_tablebase_evaluation(board)
                if eval_text != "Unknown":
                    eval_surface = timer_font.render(f"Tablebase: {eval_text}", True, (100, 200, 100))
                    screen.blit(eval_surface, (10, HEIGHT - 30))
            except:
                pass

        pygame.display.flip()
        clock.tick(60)

        # Event handling loop
        for event in pygame.event.get():
            if board.is_game_over() and not isGameOver:
                saveGamePGN(board)  # Save PGN when the game is over (checkmate, stalemate, etc.)
                isGameOver = True

            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and not board.is_game_over():
                x, y = event.pos 

                # Margins checks: Ignore clicks outside the chessboard area
                if not (BOARD_TOP <= y <= BOARD_BOTTOM):
                    continue

                # Adjust Y for the top margin
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
                move = getBotMove(board, opening_book, endgame_engine)
                if move:
                    board.push(move)
                    timer.switch_turn()
                selectedSquare = None
            elif board.turn == chess.BLACK and not BOT_PLAYS_WHITE:
                start_think = time.time()
                think_duration = random.uniform(1, 3)
 
                while time.time() - start_think < think_duration:
                    BACKGROUND_COLOR = (40, 40, 40)
                    screen.fill(BACKGROUND_COLOR)
 
                    displayBoard(screen)  
                    drawPieces(screen, board, images)  
                    timer.update()
                    timer.draw(screen, timer_font)  
                    pygame.display.flip()
                    clock.tick(30)
                move = getBotMove(board, opening_book, endgame_engine)
                if move:
                    board.push(move)
                    timer.switch_turn()
                selectedSquare = None

    pygame.quit()



if __name__ == "__main__":
    main()