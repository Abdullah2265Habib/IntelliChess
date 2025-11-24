import pygame
import chess
import random
import sys
import os
import time
import traceback
import threading

pygame.init()
from utils import load_font, loadImages
from timer import ChessTimer
from menu import show_menu 
from turn import getTurnFromButton

# PGN & Opening Book imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from pgn.savePGN import saveGamePGN
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'engine')))
from engine.opening_book.opening_book import OpeningBook
from engine.endgame.endgame import EndgameEngine
from engine.engine import EnhancedChessEngine as ChessEngine

# New window dimensions
BOARD_SIZE = 768
SQUARESIZE = BOARD_SIZE // 8
SIDEBAR_WIDTH = 600
WIDTH = BOARD_SIZE + SIDEBAR_WIDTH
HEIGHT = BOARD_SIZE + 120

# Board positioning
BOARD_LEFT = 20
BOARD_TOP = 60
BOARD_RIGHT = BOARD_LEFT + BOARD_SIZE
BOARD_BOTTOM = BOARD_TOP + BOARD_SIZE

# Sidebar positioning
SIDEBAR_LEFT = BOARD_RIGHT + 20
MOVES_PANEL_TOP = 20
MOVES_PANEL_HEIGHT = 350
ANALYSIS_PANEL_TOP = MOVES_PANEL_TOP + MOVES_PANEL_HEIGHT + 20
ANALYSIS_PANEL_HEIGHT = HEIGHT - ANALYSIS_PANEL_TOP - 20

# Global analysis info
analysis_lines = []


class AnalysisEngine(ChessEngine):
    """Extended chess engine that outputs detailed analysis"""
    def __init__(self):
        super().__init__()
        self.current_depth = 0
        self.nodes_searched = 0
        self.start_time = None
        
    def alpha_beta_root(self, board, depth, alpha, beta, start_time, max_time):
        """Override to show all moves being explored in Stockfish style"""
        global analysis_lines
        
        best_move = None
        best_value = float('-inf')
        moves = self.order_moves(board, list(board.legal_moves))
        
        self.current_depth = depth
        self.start_time = start_time
        
        # Keep track of how often we update (to avoid flooding)
        last_update = time.time()
        
        for idx, move in enumerate(moves, 1):
            # Stockfish-style currmove output - show every move being explored
            current_time = time.time()
            if current_time - last_update > 0.05:  # Update every 50ms minimum
                elapsed_ms = int((current_time - start_time) * 1000)
                nps = int(self.nodes_searched / (elapsed_ms / 1000.0)) if elapsed_ms > 0 else 0
                analysis_lines.append(
                    f"info depth {depth} currmove {move.uci()} currmovenumber {idx}/{len(moves)} nodes {self.nodes_searched} nps {nps}"
                )
                last_update = current_time
            
            if time.time() - start_time >= max_time * 0.95:
                raise TimeoutError()
            
            board.push(move)
            try:
                value = -self.alpha_beta(board, depth - 1, -beta, -alpha, start_time, max_time)
            finally:
                board.pop()
            
            if value > best_value:
                best_value = value
                best_move = move
            
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        
        return best_value, best_move
    
    def alpha_beta(self, board, depth, alpha, beta, start_time, max_time):
        """Override to track nodes"""
        self.nodes_searched += 1
        return super().alpha_beta(board, depth, alpha, beta, start_time, max_time)


class BotMoveThread(threading.Thread):
    """Thread to calculate bot move without blocking UI"""
    def __init__(self, board, opening_book, endgame_engine):
        super().__init__(daemon=True)
        self.board = board.copy()
        self.opening_book = opening_book
        self.endgame_engine = endgame_engine
        self.result = None
        self.finished = False
        self.is_opening_move = False
        
    def run(self):
        """Calculate the best move in background"""
        global analysis_lines
        analysis_lines = []
        
        try:
            # Check for opening book move
            if self.opening_book and self.board.ply() < 20:
                opening_move = self.opening_book.get_opening_move(self.board)
                if opening_move:
                    analysis_lines.append("info string Using opening book")
                    analysis_lines.append(f"bestmove {opening_move.uci()}")
                    self.result = opening_move
                    self.is_opening_move = True
                    self.finished = True
                    return
            
            # Check for endgame tablebase move
            if self.endgame_engine and self.endgame_engine.is_endgame(self.board):
                endgame_move = self.endgame_engine.get_best_move(self.board)
                if endgame_move:
                    analysis_lines.append("info string Using endgame tablebase")
                    analysis_lines.append(f"bestmove {endgame_move.uci()}")
                    self.result = endgame_move
                    self.finished = True
                    return
            
            # Use alpha-beta search with detailed output
            analysis_lines.append("info string Starting engine analysis...")
            
            engine = AnalysisEngine()
            search_start = time.time()
            
            # Monkey-patch the engine to capture print statements
            original_print = print
            captured_depth_info = {}
            
            def custom_print(*args, **kwargs):
                message = ' '.join(str(arg) for arg in args)
                
                # Parse engine output and convert to UCI-like format
                if "Depth" in message and "Eval=" in message:
                    try:
                        parts = message.split(',')
                        depth_part = parts[0].strip()
                        eval_part = parts[1].strip() if len(parts) > 1 else ""
                        move_part = parts[2].strip() if len(parts) > 2 else ""
                        nodes_part = parts[3].strip() if len(parts) > 3 else ""
                        time_part = parts[4].strip() if len(parts) > 4 else ""
                        
                        depth = depth_part.split()[-1].rstrip(':')
                        eval_str = eval_part.split('=')[-1] if '=' in eval_part else "0.00"
                        move = move_part.split('=')[-1].strip() if '=' in move_part else ""
                        nodes = nodes_part.split('=')[-1] if '=' in nodes_part else str(engine.nodes_searched)
                        time_str = time_part.split('=')[-1].rstrip('s') if '=' in time_part else "0"
                        
                        # Convert centipawn score
                        try:
                            cp_score = int(float(eval_str) * 100)
                        except:
                            cp_score = 0
                        
                        # Calculate metrics
                        try:
                            time_ms = int(float(time_str) * 1000)
                            if time_ms == 0:
                                time_ms = max(1, int((time.time() - search_start) * 1000))
                            nps = int(int(nodes) / (time_ms / 1000.0)) if time_ms > 0 else 0
                        except:
                            time_ms = max(1, int((time.time() - search_start) * 1000))
                            nps = 0
                        
                        # Store depth info
                        captured_depth_info[depth] = {
                            'cp': cp_score,
                            'nodes': nodes,
                            'nps': nps,
                            'time': time_ms,
                            'move': move
                        }
                        
                        # Stockfish-style output
                        info_line = f"info depth {depth} seldepth {depth} score cp {cp_score} nodes {nodes} nps {nps} time {time_ms} pv {move}"
                        analysis_lines.append(info_line)
                        
                    except Exception as e:
                        analysis_lines.append(f"info string {message}")
                elif "Position is" in message or "Quick move" in message or "Final move" in message:
                    analysis_lines.append(f"info string {message}")
                
                original_print(*args, **kwargs)
            
            # Temporarily replace print
            import builtins
            builtins.print = custom_print
            
            try:
                best_move = engine.get_best_move(self.board, max_time=20.0)
                if best_move:
                    # Final summary line (Stockfish style)
                    total_time = int((time.time() - search_start) * 1000)
                    total_nodes = engine.nodes_searched
                    final_nps = int(total_nodes / (total_time / 1000.0)) if total_time > 0 else 0
                    
                    analysis_lines.append(
                        f"info nodes {total_nodes} nps {final_nps} time {total_time}"
                    )
                    analysis_lines.append(f"bestmove {best_move.uci()}")
                    self.result = best_move
            finally:
                builtins.print = original_print
            
            self.finished = True
            return
                
        except Exception as e:
            analysis_lines.append(f"info string Error: {str(e)}")
            traceback.print_exc()
        
        # Fallback to random move
        legal_moves = list(self.board.legal_moves)
        if legal_moves:
            move = random.choice(legal_moves)
            analysis_lines.append("info string Using random move")
            analysis_lines.append(f"bestmove {move.uci()}")
            self.result = move
        else:
            self.result = None
        
        self.finished = True


def draw_move_history(screen, board, font):
    """Draw move history panel on the right side"""
    panel_rect = pygame.Rect(SIDEBAR_LEFT, MOVES_PANEL_TOP, SIDEBAR_WIDTH - 40, MOVES_PANEL_HEIGHT)
    pygame.draw.rect(screen, (50, 50, 50), panel_rect, border_radius=10)
    pygame.draw.rect(screen, (100, 100, 100), panel_rect, 2, border_radius=10)
    
    # Title
    title_font = pygame.font.Font(None, 28)
    title = title_font.render("Move History", True, (255, 255, 255))
    screen.blit(title, (SIDEBAR_LEFT + 10, MOVES_PANEL_TOP + 10))
    
    # Draw moves
    move_font = pygame.font.Font(None, 22)
    moves = list(board.move_stack)
    
    # Create temporary board to convert moves to SAN
    temp_board = chess.Board()
    move_pairs = []
    
    for i, move in enumerate(moves):
        san_move = temp_board.san(move)
        temp_board.push(move)
        
        if i % 2 == 0:
            move_pairs.append([f"{i//2 + 1}.", san_move])
        else:
            move_pairs[-1].append(san_move)
    
    # Display moves
    y_offset = MOVES_PANEL_TOP + 45
    x_offset = SIDEBAR_LEFT + 15
    line_height = 25
    max_lines = (MOVES_PANEL_HEIGHT - 60) // line_height
    
    # Show last moves (scroll from bottom)
    start_idx = max(0, len(move_pairs) - max_lines)
    
    for pair in move_pairs[start_idx:]:
        move_text = " ".join(pair)
        text_surface = move_font.render(move_text, True, (220, 220, 220))
        screen.blit(text_surface, (x_offset, y_offset))
        y_offset += line_height


def draw_analysis_panel(screen, font):
    """Draw analysis panel showing bot's thinking in Stockfish style"""
    global analysis_lines
    
    panel_rect = pygame.Rect(SIDEBAR_LEFT, ANALYSIS_PANEL_TOP, SIDEBAR_WIDTH - 40, ANALYSIS_PANEL_HEIGHT)
    pygame.draw.rect(screen, (50, 50, 50), panel_rect, border_radius=10)
    pygame.draw.rect(screen, (100, 100, 100), panel_rect, 2, border_radius=10)
    
    # Title
    title_font = pygame.font.Font(None, 28)
    title = title_font.render("Engine Analysis", True, (255, 255, 255))
    screen.blit(title, (SIDEBAR_LEFT + 10, ANALYSIS_PANEL_TOP + 10))
    
    # Analysis info - Use monospace font for better alignment
    try:
        info_font = pygame.font.SysFont('courier', 13)
    except:
        info_font = pygame.font.Font(None, 15)
    
    y_offset = ANALYSIS_PANEL_TOP + 45
    x_offset = SIDEBAR_LEFT + 10
    line_height = 16
    
    if analysis_lines:
        # Show last analysis lines
        max_lines = (ANALYSIS_PANEL_HEIGHT - 60) // line_height
        display_lines = analysis_lines[-max_lines:]
        
        for line in display_lines:
            # Color code different types of lines (Stockfish style)
            if "currmove" in line:
                # Show the full currmove line with all visited nodes
                display_line = line
                color = (180, 180, 180)  # Gray for move exploration
            elif line.startswith("info depth") and "score cp" in line:
                # Highlight depth completion lines
                display_line = line
                color = (150, 255, 150)  # Green for depth summary
            elif line.startswith("bestmove"):
                display_line = line
                color = (255, 255, 100)  # Yellow for best move
            elif line.startswith("info string"):
                display_line = line.replace("info string ", "")
                color = (180, 180, 255)  # Light blue for info
            elif "nodes" in line and "nps" in line and "time" in line:
                # Summary line
                display_line = line
                color = (200, 200, 255)  # Light blue for summary
            else:
                display_line = line
                color = (200, 200, 200)  # Default gray
            
            # Truncate long lines
            max_chars = 62
            if len(display_line) > max_chars:
                display_line = display_line[:max_chars-3] + "..."
            
            text_surface = info_font.render(display_line, True, color)
            screen.blit(text_surface, (x_offset, y_offset))
            y_offset += line_height
    else:
        text = info_font.render("Waiting for move...", True, (150, 150, 150))
        screen.blit(text, (x_offset, y_offset))


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
    
    if opening_book and board.ply() < 10:
        try:
            opening_name = opening_book.get_opening_name(board)
            if opening_name != "Unknown Opening":
                status += f" | {opening_name}"
        except:
            pass
    
    if endgame_engine and endgame_engine.is_endgame(board):
        try:
            eval_text = endgame_engine.get_tablebase_evaluation(board)
            if eval_text != "Unknown":
                status += f" | {eval_text}"
        except:
            pass
    
    return status


def main():  
    global analysis_lines
    isGameOver = False

    BOT_PLAYS_WHITE = getTurnFromButton()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Intellichess")
    clock = pygame.time.Clock()  

    font = load_font(size=60)

    images = loadImages(SQUARESIZE)
    selected_time = show_menu(screen)
    timer = ChessTimer(total_time=selected_time)

    # Load fonts
    font_dir = os.path.join(os.path.dirname(__file__), "font")
    font_path = os.path.join(font_dir, "Orbitron-Bold.ttf")

    if not os.path.exists(font_path):
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
        script_dir = os.path.dirname(os.path.abspath(__file__))
        tablebase_path = os.path.join(script_dir, "..", "engine", "tablebases", "syzygy")
        tablebase_path = os.path.normpath(tablebase_path)
        endgame_engine = EndgameEngine(tablebase_path=tablebase_path)
    except Exception as e:
        endgame_engine = None
        print("Endgame engine not available:", e)
    
    running = True
    bot_thread = None
    waiting_for_bot = False

    while running:
        BACKGROUND_COLOR = (30, 30, 30)
        screen.fill(BACKGROUND_COLOR)

        # Draw board
        for rank in range(8):
            for file in range(8):
                color = (238, 238, 210) if (rank + file) % 2 == 0 else (118, 150, 86)
                pygame.draw.rect(
                    screen, color,
                    pygame.Rect(
                        BOARD_LEFT + file * SQUARESIZE,
                        BOARD_TOP + rank * SQUARESIZE,
                        SQUARESIZE, SQUARESIZE
                    )
                )
        
        # Draw highlights and pieces
        if selectedSquare is not None:
            col = chess.square_file(selectedSquare)
            row = 7 - chess.square_rank(selectedSquare)
            surface = pygame.Surface((SQUARESIZE, SQUARESIZE), pygame.SRCALPHA)
            pygame.draw.rect(surface, (255, 255, 0, 100), (0, 0, SQUARESIZE, SQUARESIZE))
            screen.blit(surface, (BOARD_LEFT + col * SQUARESIZE, BOARD_TOP + row * SQUARESIZE))
            
            # Draw valid moves
            for move in board.legal_moves:
                if move.from_square == selectedSquare:
                    col = chess.square_file(move.to_square)
                    row = 7 - chess.square_rank(move.to_square)
                    surface = pygame.Surface((SQUARESIZE, SQUARESIZE), pygame.SRCALPHA)
                    pygame.draw.circle(
                        surface, (0, 0, 0, 80),
                        (SQUARESIZE // 2, SQUARESIZE // 2),
                        SQUARESIZE // 6
                    )
                    screen.blit(surface, (BOARD_LEFT + col * SQUARESIZE, BOARD_TOP + row * SQUARESIZE))
        
        # Draw pieces
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                col = chess.square_file(square)
                row = 7 - chess.square_rank(square)
                img_or_text = images.get(piece.symbol())
                x_pos = BOARD_LEFT + col * SQUARESIZE
                y_pos = BOARD_TOP + row * SQUARESIZE
                
                if isinstance(img_or_text, pygame.Surface):
                    screen.blit(img_or_text, (x_pos, y_pos))
                else:
                    text_rect = img_or_text.get_rect(
                        center=(x_pos + SQUARESIZE // 2, y_pos + SQUARESIZE // 2)
                    )
                    screen.blit(img_or_text, text_rect)

        # Draw timers
        white_time = f"Player: {int(timer.remaining_white // 60):02}:{int(timer.remaining_white % 60):02}"
        black_time = f"Computer: {int(timer.remaining_black // 60):02}:{int(timer.remaining_black % 60):02}"
        
        white_surface = timer_font.render(white_time, True, (255, 255, 255))
        black_surface = timer_font.render(black_time, True, (255, 255, 255))
        
        white_rect = white_surface.get_rect(center=(BOARD_LEFT + BOARD_SIZE // 2, BOARD_BOTTOM + 40))
        black_rect = black_surface.get_rect(center=(BOARD_LEFT + BOARD_SIZE // 2, BOARD_TOP - 30))
        
        for rect in [white_rect, black_rect]:
            bg_rect = pygame.Rect(rect.left - 10, rect.top - 5, rect.width + 20, rect.height + 10)
            pygame.draw.rect(screen, (50, 50, 50), bg_rect, border_radius=8)
        
        if timer.text_color == "white":
            active_rect = pygame.Rect(white_rect.left - 10, white_rect.top - 5, 
                                     white_rect.width + 20, white_rect.height + 10)
        else:
            active_rect = pygame.Rect(black_rect.left - 10, black_rect.top - 5,
                                     black_rect.width + 20, black_rect.height + 10)
        pygame.draw.rect(screen, (70, 70, 70), active_rect, border_radius=8)
        
        screen.blit(white_surface, white_rect)
        screen.blit(black_surface, black_rect)

        # Draw panels
        draw_move_history(screen, board, font)
        draw_analysis_panel(screen, font)

        if waiting_for_bot:
            thinking = timer_font.render("Thinking...", True, (255, 200, 0))
            screen.blit(thinking, (BOARD_LEFT + 10, BOARD_TOP - 30))

        timer.update()

        if timer.remaining_white <= 0 or timer.remaining_black <= 0:
            winner = "Black" if timer.remaining_white <= 0 else "White"
            text = timer_font.render(f"Time Out! {winner} Wins!", False, (230, 210, 40))
            screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2))
            pygame.display.flip()
            time.sleep(3)
            saveGamePGN(board)
            running = False
            continue

        status_text = getGameStatus(board, opening_book, endgame_engine)
        pygame.display.set_caption(status_text)

        pygame.display.flip()
        clock.tick(60)

        if waiting_for_bot and bot_thread and bot_thread.finished:
            move = bot_thread.result
            if move:
                board.push(move)
                timer.switch_turn()
            selectedSquare = None
            waiting_for_bot = False
            bot_thread = None

        for event in pygame.event.get():
            if board.is_game_over() and not isGameOver:
                saveGamePGN(board)
                isGameOver = True

            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and not board.is_game_over() and not waiting_for_bot:
                x, y = event.pos 

                if not (BOARD_LEFT <= x <= BOARD_RIGHT and BOARD_TOP <= y <= BOARD_BOTTOM):
                    continue

                col = (x - BOARD_LEFT) // SQUARESIZE
                row = (y - BOARD_TOP) // SQUARESIZE
                square = chess.square(col, 7 - row)

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
                waiting_for_bot = False
                bot_thread = None
                analysis_lines = []

        if not board.is_game_over() and not waiting_for_bot:
            if (board.turn == chess.WHITE and BOT_PLAYS_WHITE) or \
               (board.turn == chess.BLACK and not BOT_PLAYS_WHITE):
                
                bot_thread = BotMoveThread(board, opening_book, endgame_engine)
                bot_thread.start()
                waiting_for_bot = True

    pygame.quit()


if __name__ == "__main__":
    main()