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
from gui.statistics_graphs import GameMetrics, display_game_statistics, save_metrics

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

# Scroll positions
moves_scroll_offset = 0
analysis_scroll_offset = 0


class AnalysisEngine(ChessEngine):
    """Extended chess engine that outputs detailed analysis"""
    def __init__(self, metrics=None):
        super().__init__()
        self.current_depth = 0
        self.nodes_searched = 0
        self.start_time = None
        self.metrics = metrics
        
    def iterative_deepening_search(self, board, max_time):
        """Override to capture depth output"""
        global analysis_lines
        
        start_time = time.time()
        self.best_move_found = None
        self.nodes_searched = 0
        
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None
        
        self.best_move_found = legal_moves[0]
        best_eval = 0
        
        # Aspiration window parameters
        window_size = 50
        
        for depth in range(1, 50):
            elapsed = time.time() - start_time
            
            if elapsed >= max_time * 0.90:
                break
            
            # Set aspiration window around previous eval
            alpha = best_eval - window_size
            beta = best_eval + window_size
            
            try:
                # Try search with narrow window
                eval_score, move = self.pvs_root(
                    board, depth, alpha, beta, start_time, max_time
                )
                
                # If we failed high or low, research with full window
                if eval_score <= alpha or eval_score >= beta:
                    eval_score, move = self.pvs_root(
                        board, depth, float('-inf'), float('inf'), 
                        start_time, max_time
                    )
                
                if move is not None:
                    self.best_move_found = move
                    best_eval = eval_score
                    
                    elapsed = time.time() - start_time
                    
                    # Capture the depth output
                    depth_info = (f"Depth {depth}: Eval={eval_score:+.2f}, "
                          f"Move={move}, Nodes={self.nodes_searched}, "
                          f"Time={elapsed:.2f}s, NPS={int(self.nodes_searched/elapsed) if elapsed > 0 else 0}")
                    
                    print(depth_info)
                    
                    # Add to analysis lines
                    analysis_lines.append(f"info string {depth_info}")
                    
                    # Record metrics if available
                    if self.metrics:
                        self.metrics.add_depth_data(depth, self.nodes_searched, elapsed, eval_score)
                    
                    # Also add UCI-style format
                    # Handle mate scores (infinity values)
                    if abs(eval_score) > 9000:
                        # Mate score
                        mate_in = int((10000 - abs(eval_score)) / 2) if abs(eval_score) < 10000 else 1
                        score_str = f"mate {mate_in if eval_score > 0 else -mate_in}"
                    else:
                        # Normal centipawn score
                        cp_score = int(eval_score * 100)
                        score_str = f"cp {cp_score}"
                    
                    time_ms = int(elapsed * 1000)
                    nps = int(self.nodes_searched/elapsed) if elapsed > 0 else 0
                    analysis_lines.append(
                        f"info depth {depth} score {score_str} nodes {self.nodes_searched} nps {nps} time {time_ms} pv {move.uci()}"
                    )
                
                # Mate found
                if abs(eval_score) > 9000:
                    mate_msg = f"Found forced mate! Eval: {eval_score}"
                    print(mate_msg)
                    analysis_lines.append(f"info string {mate_msg}")
                    break
                    
            except TimeoutError:
                timeout_msg = f"Search stopped at depth {depth} due to time limit"
                print(timeout_msg)
                analysis_lines.append(f"info string {timeout_msg}")
                break
        
        total_time = time.time() - start_time
        nps = int(self.nodes_searched / total_time) if total_time > 0 else 0
        
        final_msg = (f"Final move: {self.best_move_found}, Total nodes: {self.nodes_searched}, "
              f"Time: {total_time:.2f}s, NPS: {nps}")
        print(final_msg)
        analysis_lines.append(f"info string {final_msg}")
        
        return self.best_move_found


class BotMoveThread(threading.Thread):
    """Thread to calculate bot move without blocking UI"""
    def __init__(self, board, opening_book, endgame_engine, metrics=None):
        super().__init__(daemon=True)
        self.board = board.copy()
        self.opening_book = opening_book
        self.endgame_engine = endgame_engine
        self.metrics = metrics
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
            
            # Use engine with analysis output
            analysis_lines.append("info string Starting engine analysis...")
            
            engine = AnalysisEngine(metrics=self.metrics)
            
            start_time = time.time()
            best_move = engine.get_best_move(self.board, max_time=20.0)
            total_time = time.time() - start_time
            
            if self.metrics:
                self.metrics.add_move_time(total_time)
            
            if best_move:
                analysis_lines.append(f"bestmove {best_move.uci()}")
                self.result = best_move
            
            self.finished = True
            return
                
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            analysis_lines.append(f"info string {error_msg}")
            print(error_msg)
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


def wrap_text(text, font, max_width):
    """Wrap text to fit within max_width"""
    words = text.split(' ')
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        test_surface = font.render(test_line, True, (255, 255, 255))
        
        if test_surface.get_width() <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
                current_line = [word]
            else:
                # Word is too long, split it
                lines.append(word)
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines


def draw_move_history(screen, board, font, scroll_offset):
    """Draw move history panel with scrolling"""
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
    
    # Create a surface for scrolling
    content_y = MOVES_PANEL_TOP + 45
    line_height = 25
    panel_height = MOVES_PANEL_HEIGHT - 60
    
    # Calculate total content height
    total_content_height = len(move_pairs) * line_height
    max_scroll = max(0, total_content_height - panel_height)
    
    # Clamp scroll offset
    scroll_offset = max(0, min(scroll_offset, max_scroll))
    
    # Create clipping rect for scrollable area
    clip_rect = pygame.Rect(SIDEBAR_LEFT + 10, content_y, SIDEBAR_WIDTH - 60, panel_height)
    screen.set_clip(clip_rect)
    
    # Draw moves with scroll offset
    y_offset = content_y - scroll_offset
    x_offset = SIDEBAR_LEFT + 15
    
    for pair in move_pairs:
        move_text = " ".join(pair)
        text_surface = move_font.render(move_text, True, (220, 220, 220))
        screen.blit(text_surface, (x_offset, y_offset))
        y_offset += line_height
    
    # Remove clipping
    screen.set_clip(None)
    
    # Draw scrollbar if needed
    if total_content_height > panel_height:
        scrollbar_height = max(20, int(panel_height * panel_height / total_content_height))
        scrollbar_y = content_y + int(scroll_offset * panel_height / total_content_height)
        scrollbar_rect = pygame.Rect(
            SIDEBAR_LEFT + SIDEBAR_WIDTH - 50,
            scrollbar_y,
            8,
            scrollbar_height
        )
        pygame.draw.rect(screen, (150, 150, 150), scrollbar_rect, border_radius=4)
    
    return scroll_offset


def draw_analysis_panel(screen, font, scroll_offset):
    """Draw analysis panel with text wrapping and scrolling"""
    global analysis_lines
    
    panel_rect = pygame.Rect(SIDEBAR_LEFT, ANALYSIS_PANEL_TOP, SIDEBAR_WIDTH - 40, ANALYSIS_PANEL_HEIGHT)
    pygame.draw.rect(screen, (50, 50, 50), panel_rect, border_radius=10)
    pygame.draw.rect(screen, (100, 100, 100), panel_rect, 2, border_radius=10)
    
    # Title
    title_font = pygame.font.Font(None, 28)
    title = title_font.render("Engine Analysis", True, (255, 255, 255))
    screen.blit(title, (SIDEBAR_LEFT + 10, ANALYSIS_PANEL_TOP + 10))
    
    # Analysis info - Use smaller font for better fit
    try:
        info_font = pygame.font.SysFont('courier', 12)
    except:
        info_font = pygame.font.Font(None, 14)
    
    content_y = ANALYSIS_PANEL_TOP + 45
    x_offset = SIDEBAR_LEFT + 10
    line_height = 16
    panel_height = ANALYSIS_PANEL_HEIGHT - 60
    max_text_width = SIDEBAR_WIDTH - 70
    
    if analysis_lines:
        # Process all lines and wrap them
        wrapped_lines = []
        
        for line in analysis_lines:
            # Determine color based on line type
            if "currmove" in line:
                color = (180, 180, 180)
            elif line.startswith("info depth") and "score cp" in line:
                color = (150, 255, 150)
            elif line.startswith("bestmove"):
                color = (255, 255, 100)
            elif line.startswith("info string"):
                line = line.replace("info string ", "")
                color = (180, 180, 255)
            elif "nodes" in line and "nps" in line and "time" in line:
                color = (200, 200, 255)
            else:
                color = (200, 200, 200)
            
            # Wrap long lines
            text_lines = wrap_text(line, info_font, max_text_width)
            for text_line in text_lines:
                wrapped_lines.append((text_line, color))
        
        # Calculate total content height
        total_content_height = len(wrapped_lines) * line_height
        max_scroll = max(0, total_content_height - panel_height)
        
        # Clamp scroll offset
        scroll_offset = max(0, min(scroll_offset, max_scroll))
        
        # Auto-scroll to bottom when new content arrives
        if len(wrapped_lines) > 0:
            scroll_offset = max_scroll
        
        # Create clipping rect for scrollable area
        clip_rect = pygame.Rect(SIDEBAR_LEFT + 10, content_y, SIDEBAR_WIDTH - 60, panel_height)
        screen.set_clip(clip_rect)
        
        # Draw wrapped lines with scroll offset
        y_offset = content_y - scroll_offset
        
        for text_line, color in wrapped_lines:
            text_surface = info_font.render(text_line, True, color)
            screen.blit(text_surface, (x_offset, y_offset))
            y_offset += line_height
        
        # Remove clipping
        screen.set_clip(None)
        
        # Draw scrollbar if needed
        if total_content_height > panel_height:
            scrollbar_height = max(20, int(panel_height * panel_height / total_content_height))
            scrollbar_y = content_y + int(scroll_offset * panel_height / total_content_height)
            scrollbar_rect = pygame.Rect(
                SIDEBAR_LEFT + SIDEBAR_WIDTH - 50,
                scrollbar_y,
                8,
                scrollbar_height
            )
            pygame.draw.rect(screen, (150, 150, 150), scrollbar_rect, border_radius=4)
        
        return scroll_offset
    else:
        text = info_font.render("Waiting for move...", True, (150, 150, 150))
        screen.blit(text, (x_offset, content_y))
        return 0


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
    global analysis_lines, moves_scroll_offset, analysis_scroll_offset
    isGameOver = False

    BOT_PLAYS_WHITE = getTurnFromButton()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Intellichess")
    clock = pygame.time.Clock()  

    font = load_font(size=60)

    images = loadImages(SQUARESIZE)
    selected_time = show_menu(screen)
    timer = ChessTimer(total_time=selected_time)
    
    # Initialize metrics
    metrics = GameMetrics()

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
    
    # Reset scroll positions
    moves_scroll_offset = 0
    analysis_scroll_offset = 0

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

        # Draw panels with scrolling
        moves_scroll_offset = draw_move_history(screen, board, font, moves_scroll_offset)
        analysis_scroll_offset = draw_analysis_panel(screen, font, analysis_scroll_offset)

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
            save_metrics(metrics, "last_game_metrics.json")
            display_game_statistics(metrics)
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
                save_metrics(metrics, "last_game_metrics.json")
                display_game_statistics(metrics)
                isGameOver = True

            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEWHEEL:
                # Handle scrolling for both panels
                mouse_x, mouse_y = pygame.mouse.get_pos()
                
                # Check if mouse is over moves panel
                if (SIDEBAR_LEFT <= mouse_x <= SIDEBAR_LEFT + SIDEBAR_WIDTH and
                    MOVES_PANEL_TOP <= mouse_y <= MOVES_PANEL_TOP + MOVES_PANEL_HEIGHT):
                    moves_scroll_offset -= event.y * 25
                
                # Check if mouse is over analysis panel
                elif (SIDEBAR_LEFT <= mouse_x <= SIDEBAR_LEFT + SIDEBAR_WIDTH and
                      ANALYSIS_PANEL_TOP <= mouse_y <= ANALYSIS_PANEL_TOP + ANALYSIS_PANEL_HEIGHT):
                    analysis_scroll_offset -= event.y * 25

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
                        if metrics:
                            metrics.start_new_move()
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
                moves_scroll_offset = 0
                analysis_scroll_offset = 0

        if not board.is_game_over() and not waiting_for_bot:
            if (board.turn == chess.WHITE and BOT_PLAYS_WHITE) or \
               (board.turn == chess.BLACK and not BOT_PLAYS_WHITE):
                
                bot_thread = BotMoveThread(board, opening_book, endgame_engine, metrics)
                bot_thread.start()
                waiting_for_bot = True

    pygame.quit()


if __name__ == "__main__":
    main()