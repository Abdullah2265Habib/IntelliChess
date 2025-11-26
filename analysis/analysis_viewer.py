"""
Enhanced GUI for viewing chess game analysis with arrows, threats, and eval bar
Replace analysis/analysis_viewer.py with this file
"""

import pygame
import chess
import chess.pgn
import json
import os
import sys
from typing import Dict, List, Optional
import io
import math

# Import your existing modules
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from gui.utils import loadImages

# Constants
BOARD_SIZE = 640
SQUARESIZE = BOARD_SIZE // 8
EVAL_BAR_WIDTH = BOARD_SIZE // 10  # 1/10 of board width
SIDEBAR_WIDTH = 500
WIDTH = EVAL_BAR_WIDTH + 20 + BOARD_SIZE + SIDEBAR_WIDTH + 60
HEIGHT = BOARD_SIZE + 120

# Colors
BEIGE = (238, 238, 210)
BROWN = (118, 150, 86)
GREEN_ARROW = (0, 200, 0, 200)
RED_ARROW = (200, 0, 0, 200)
BLUE_ARROW = (0, 100, 255, 200)
YELLOW_HIGHLIGHT = (255, 255, 0, 100)
BG_COLOR = (30, 30, 30)
PANEL_BG = (50, 50, 50)
TEXT_COLOR = (255, 255, 255)

# Eval bar colors
EVAL_WHITE = (240, 240, 240)
EVAL_BLACK = (40, 40, 40)

class AnalysisViewer:
    """Interactive viewer for analyzed chess games"""
    
    def __init__(self, pgn_path: str, analysis_path: str):
        pygame.init()
        
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Game Analysis Viewer")
        
        self.clock = pygame.time.Clock()
        self.images = loadImages(SQUARESIZE)
        
        # Load classification icons
        self.load_classification_icons()
        
        # Load game and analysis
        self.load_game(pgn_path)
        self.load_analysis(analysis_path)
        
        # Viewing state
        self.current_move = 0
        self.board = chess.Board()
        self.show_best_move = True
        self.show_threats = True
        
        # Fonts
        try:
            font_path = os.path.join("gui", "font", "Orbitron-Bold.ttf")
            self.title_font = pygame.font.Font(font_path, 32)
            self.text_font = pygame.font.Font(font_path, 20)
            self.small_font = pygame.font.Font(font_path, 16)
        except:
            self.title_font = pygame.font.SysFont('Arial', 32)
            self.text_font = pygame.font.SysFont('Arial', 20)
            self.small_font = pygame.font.SysFont('Arial', 16)
    
    def load_classification_icons(self):
        """Load move classification icons from gui/img/"""
        self.class_icons = {}
        icon_size = 40
        
        classifications = [
            "brilliant", "great", "best", "excellent", 
            "good", "book", "inaccuracy", "mistake", "blunder"
        ]
        
        for classification in classifications:
            try:
                icon_path = os.path.join("gui", "img", f"{classification}.png")
                if os.path.exists(icon_path):
                    icon = pygame.image.load(icon_path)
                    icon = pygame.transform.scale(icon, (icon_size, icon_size))
                    self.class_icons[classification] = icon
                else:
                    # Create fallback colored square if image not found
                    icon = pygame.Surface((icon_size, icon_size))
                    color_map = {
                        "brilliant": (255, 215, 0),
                        "great": (100, 255, 100),
                        "best": (0, 255, 0),
                        "excellent": (150, 255, 150),
                        "good": (200, 255, 200),
                        "book": (180, 180, 255),
                        "inaccuracy": (255, 200, 0),
                        "mistake": (255, 150, 0),
                        "blunder": (255, 0, 0)
                    }
                    icon.fill(color_map.get(classification, (150, 150, 150)))
                    self.class_icons[classification] = icon
            except Exception as e:
                print(f"Error loading icon for {classification}: {e}")
    
    def load_game(self, pgn_path: str):
        """Load PGN game file"""
        with open(pgn_path, 'r') as f:
            pgn_text = f.read()
        
        pgn_io = io.StringIO(pgn_text)
        self.game = chess.pgn.read_game(pgn_io)
        self.moves = list(self.game.mainline_moves())
    
    def load_analysis(self, analysis_path: str):
        """Load analysis JSON file"""
        with open(analysis_path, 'r') as f:
            self.analysis = json.load(f)
    
    def draw_eval_bar(self):
        """Draw evaluation bar on the left side"""
        bar_x = 20
        bar_y = 60
        bar_width = EVAL_BAR_WIDTH
        bar_height = BOARD_SIZE
        
        # Background border
        pygame.draw.rect(self.screen, (100, 100, 100), 
                        pygame.Rect(bar_x - 2, bar_y - 2, bar_width + 4, bar_height + 4),
                        border_radius=8)
        
        # Get current evaluation
        current_eval = 0
        if self.current_move < len(self.analysis.get("detailed_moves", [])):
            move_data = self.analysis["detailed_moves"][self.current_move]
            current_eval = move_data.get("eval", 0)
        
        # Clamp evaluation for display (-10 to +10)
        clamped_eval = max(-10, min(10, current_eval))
        
        # Calculate bar split (0 is middle, positive is white advantage)
        # Convert eval to percentage (0 to 1, where 0.5 is equal)
        eval_percentage = (clamped_eval + 10) / 20
        white_height = int(bar_height * eval_percentage)
        black_height = bar_height - white_height
        
        # Draw black advantage (top)
        pygame.draw.rect(self.screen, EVAL_BLACK,
                        pygame.Rect(bar_x, bar_y, bar_width, black_height))
        
        # Draw white advantage (bottom)
        pygame.draw.rect(self.screen, EVAL_WHITE,
                        pygame.Rect(bar_x, bar_y + black_height, bar_width, white_height))
        
        # Draw center line
        center_y = bar_y + bar_height // 2
        pygame.draw.line(self.screen, (150, 150, 150), 
                        (bar_x, center_y), (bar_x + bar_width, center_y), 2)
        
        # Draw eval text
        eval_text = f"{current_eval:+.1f}"
        if abs(current_eval) > 9:
            eval_text = f"M{int(abs(current_eval) - 9)}" if current_eval > 0 else f"-M{int(abs(current_eval) - 9)}"
        
        text_color = (255, 255, 255) if abs(clamped_eval) < 2 else ((255, 255, 255) if current_eval > 0 else (0, 0, 0))
        eval_surface = self.small_font.render(eval_text, True, text_color)
        eval_rect = eval_surface.get_rect(center=(bar_x + bar_width // 2, bar_y + bar_height // 2))
        
        # Draw background for text
        bg_rect = pygame.Rect(eval_rect.x - 5, eval_rect.y - 3, eval_rect.width + 10, eval_rect.height + 6)
        pygame.draw.rect(self.screen, (80, 80, 80), bg_rect, border_radius=5)
        
        self.screen.blit(eval_surface, eval_rect)
    
    def draw_board(self):
        """Draw the chess board"""
        board_left = EVAL_BAR_WIDTH + 40
        
        for rank in range(8):
            for file in range(8):
                color = BEIGE if (rank + file) % 2 == 0 else BROWN
                pygame.draw.rect(
                    self.screen, color,
                    pygame.Rect(board_left + file * SQUARESIZE, 60 + rank * SQUARESIZE, 
                               SQUARESIZE, SQUARESIZE)
                )
    
    def draw_pieces(self):
        """Draw chess pieces on the board"""
        board_left = EVAL_BAR_WIDTH + 40
        
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                col = chess.square_file(square)
                row = 7 - chess.square_rank(square)
                img = self.images.get(piece.symbol())
                
                if isinstance(img, pygame.Surface):
                    self.screen.blit(img, (board_left + col * SQUARESIZE, 60 + row * SQUARESIZE))
    
    def draw_thick_arrow(self, from_square: int, to_square: int, color: tuple, width: int = 12):
        """Draw a thick translucent arrow from one square to another"""
        board_left = EVAL_BAR_WIDTH + 40
        
        from_col = chess.square_file(from_square)
        from_row = 7 - chess.square_rank(from_square)
        to_col = chess.square_file(to_square)
        to_row = 7 - chess.square_rank(to_square)
        
        start_x = board_left + from_col * SQUARESIZE + SQUARESIZE // 2
        start_y = 60 + from_row * SQUARESIZE + SQUARESIZE // 2
        end_x = board_left + to_col * SQUARESIZE + SQUARESIZE // 2
        end_y = 60 + to_row * SQUARESIZE + SQUARESIZE // 2
        
        # Create transparent surface for arrow
        arrow_surface = pygame.Surface((BOARD_SIZE, BOARD_SIZE), pygame.SRCALPHA)
        
        # Calculate arrow angle and shorten it slightly
        dx = end_x - start_x
        dy = end_y - start_y
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance < 1:
            return
        
        # Shorten arrow to not overlap pieces
        shorten_by = SQUARESIZE * 0.3
        ratio = (distance - shorten_by) / distance
        
        end_x_short = start_x + dx * ratio
        end_y_short = start_y + dy * ratio
        
        # Adjust coordinates relative to surface
        start_x_rel = start_x - board_left
        start_y_rel = start_y - 60
        end_x_rel = end_x_short - board_left
        end_y_rel = end_y_short - 60
        
        # Draw thick arrow line
        pygame.draw.line(arrow_surface, color, 
                        (start_x_rel, start_y_rel), 
                        (end_x_rel, end_y_rel), width)
        
        # Draw arrowhead
        angle = math.atan2(end_y_short - start_y, end_x_short - start_x)
        arrow_size = 25
        
        arrow_points = [
            (end_x_rel, end_y_rel),
            (end_x_rel - arrow_size * math.cos(angle - math.pi/6),
             end_y_rel - arrow_size * math.sin(angle - math.pi/6)),
            (end_x_rel - arrow_size * math.cos(angle + math.pi/6),
             end_y_rel - arrow_size * math.sin(angle + math.pi/6))
        ]
        pygame.draw.polygon(arrow_surface, color, arrow_points)
        
        self.screen.blit(arrow_surface, (board_left, 60))
    
    def draw_move_classification(self):
        """Draw the current move's classification icon"""
        if self.current_move >= len(self.analysis.get("detailed_moves", [])):
            return
        
        move_data = self.analysis["detailed_moves"][self.current_move]
        classification = move_data.get("classification", "unknown")
        
        # Get icon
        icon = self.class_icons.get(classification)
        if not icon:
            return
        
        # Draw icon in top-left corner
        icon_x = EVAL_BAR_WIDTH + 50
        icon_y = 15
        
        # Background
        bg_rect = pygame.Rect(icon_x - 5, icon_y - 5, icon.get_width() + 10, icon.get_height() + 10)
        pygame.draw.rect(self.screen, (50, 50, 50), bg_rect, border_radius=8)
        pygame.draw.rect(self.screen, (100, 100, 100), bg_rect, 2, border_radius=8)
        
        self.screen.blit(icon, (icon_x, icon_y))
        
        # Classification text
        class_text = classification.capitalize()
        text = self.text_font.render(class_text, True, TEXT_COLOR)
        self.screen.blit(text, (icon_x + icon.get_width() + 15, icon_y + 8))
    
    def draw_threats(self):
        """Draw threat arrows (opponent's best attacking moves)"""
        if not self.show_threats:
            return
        
        # For now, we'll skip threats as the analysis doesn't include them
        # You can extend the analyzer to detect hanging pieces and attacks
        pass
    
    def draw_sidebar(self):
        """Draw the analysis sidebar"""
        sidebar_x = EVAL_BAR_WIDTH + BOARD_SIZE + 60
        
        # Background
        pygame.draw.rect(self.screen, PANEL_BG, 
                        pygame.Rect(sidebar_x, 20, SIDEBAR_WIDTH - 40, HEIGHT - 40),
                        border_radius=10)
        
        # Title
        title = self.title_font.render("Game Analysis", True, TEXT_COLOR)
        self.screen.blit(title, (sidebar_x + 20, 30))
        
        y_offset = 80
        
        # Game info
        game_info = self.analysis.get("game_info", {})
        info_lines = [
            f"Event: {game_info.get('event', 'Unknown')}",
            f"Date: {game_info.get('date', 'Unknown')}",
            f"Result: {game_info.get('result', 'Unknown')}"
        ]
        
        for line in info_lines:
            text = self.small_font.render(line, True, (200, 200, 200))
            self.screen.blit(text, (sidebar_x + 20, y_offset))
            y_offset += 25
        
        y_offset += 20
        
        # Move classifications summary with icons
        classifications = self.analysis.get("move_classifications", {})
        
        class_display = [
            ("brilliant", classifications.get("brilliant", 0)),
            ("great", classifications.get("great", 0)),
            ("best", classifications.get("best", 0)),
            ("excellent", classifications.get("excellent", 0)),
            ("good", classifications.get("good", 0)),
            ("book", classifications.get("book", 0)),
            ("inaccuracy", classifications.get("inaccuracy", 0)),
            ("mistake", classifications.get("mistake", 0)),
            ("blunder", classifications.get("blunder", 0))
        ]
        
        for class_name, count in class_display:
            # Draw small icon
            icon = self.class_icons.get(class_name)
            if icon:
                small_icon = pygame.transform.scale(icon, (20, 20))
                self.screen.blit(small_icon, (sidebar_x + 20, y_offset))
            
            # Draw text
            label = class_name.capitalize()
            text = self.small_font.render(f"{label}: {count}", True, (220, 220, 220))
            self.screen.blit(text, (sidebar_x + 50, y_offset))
            y_offset += 25
        
        y_offset += 20
        
        # Estimated ELO
        elo = self.analysis.get("estimated_elo", 0)
        elo_text = self.text_font.render(f"Estimated ELO: {elo}", True, (255, 215, 0))
        self.screen.blit(elo_text, (sidebar_x + 20, y_offset))
        
        y_offset += 50
        
        # Current move info
        if self.current_move < len(self.analysis.get("detailed_moves", [])):
            move_data = self.analysis["detailed_moves"][self.current_move]
            
            move_info = self.text_font.render(
                f"Move {move_data['move_number']}: {move_data['move']}", 
                True, (255, 255, 255)
            )
            self.screen.blit(move_info, (sidebar_x + 20, y_offset))
            y_offset += 30
            
            eval_text = self.small_font.render(
                f"Evaluation: {move_data.get('eval', 0):+.2f}", 
                True, (200, 200, 200)
            )
            self.screen.blit(eval_text, (sidebar_x + 20, y_offset))
            y_offset += 25
            
            if move_data.get('best_move'):
                best_text = self.small_font.render(
                    f"Best move: {move_data['best_move']}", 
                    True, (150, 255, 150)
                )
                self.screen.blit(best_text, (sidebar_x + 20, y_offset))
        
        # Controls
        y_offset = HEIGHT - 140
        controls = [
            "← → : Navigate moves",
            "Space: Toggle best move arrow",
            "T: Toggle threats",
            "R: Reset to start",
            "ESC: Exit"
        ]
        
        for control in controls:
            text = self.small_font.render(control, True, (180, 180, 180))
            self.screen.blit(text, (sidebar_x + 20, y_offset))
            y_offset += 22
    
    def draw_best_move_arrow(self):
        """Draw arrow showing the best move"""
        if not self.show_best_move:
            return
        
        if self.current_move >= len(self.analysis.get("detailed_moves", [])):
            return
        
        move_data = self.analysis["detailed_moves"][self.current_move]
        best_move_uci = move_data.get("best_move")
        
        if best_move_uci:
            try:
                move = chess.Move.from_uci(best_move_uci)
                self.draw_thick_arrow(move.from_square, move.to_square, GREEN_ARROW, width=15)
            except:
                pass
    
    def update_board_position(self):
        """Update board to current move position"""
        self.board = chess.Board()
        for i in range(self.current_move):
            if i < len(self.moves):
                self.board.push(self.moves[i])
    
    def run(self):
        """Main game loop"""
        running = True
        
        while running:
            self.screen.fill(BG_COLOR)
            
            # Draw everything
            self.draw_eval_bar()
            self.draw_board()
            self.draw_pieces()
            self.draw_threats()
            self.draw_best_move_arrow()
            self.draw_move_classification()
            self.draw_sidebar()
            
            pygame.display.flip()
            self.clock.tick(60)
            
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    
                    elif event.key == pygame.K_RIGHT:
                        if self.current_move < len(self.moves):
                            self.current_move += 1
                            self.update_board_position()
                    
                    elif event.key == pygame.K_LEFT:
                        if self.current_move > 0:
                            self.current_move -= 1
                            self.update_board_position()
                    
                    elif event.key == pygame.K_SPACE:
                        self.show_best_move = not self.show_best_move
                    
                    elif event.key == pygame.K_t:
                        self.show_threats = not self.show_threats
                    
                    elif event.key == pygame.K_r:
                        self.current_move = 0
                        self.update_board_position()
        
        pygame.quit()


def main():
    """Launch the analysis viewer"""
    import glob
    
    # Find the most recent game and its analysis
    games = glob.glob("games/*[!_analysis].txt")
    
    if not games:
        print("No games found in 'games' folder")
        return
    
    latest_game = max(games, key=os.path.getctime)
    analysis_file = latest_game.replace(".txt", "_analysis.json")
    
    if not os.path.exists(analysis_file):
        print(f"Analysis file not found: {analysis_file}")
        print("Please run the analyzer first:")
        print(f"  python -m analysis.game_analyzer {latest_game}")
        return
    
    print(f"Loading game: {latest_game}")
    print(f"Loading analysis: {analysis_file}")
    
    viewer = AnalysisViewer(latest_game, analysis_file)
    viewer.run()


if __name__ == "__main__":
    main()