"""
GUI for viewing chess game analysis with visual arrows and threats
Add this to your gui folder as 'analysis_viewer.py'
"""

import pygame
import chess
import chess.pgn
import json
import os
import sys
from typing import Dict, List, Optional
import io

# Import your existing modules
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from gui.utils import loadImages

# Constants
BOARD_SIZE = 640
SQUARESIZE = BOARD_SIZE // 8
SIDEBAR_WIDTH = 500
WIDTH = BOARD_SIZE + SIDEBAR_WIDTH + 60
HEIGHT = BOARD_SIZE + 120

# Colors
BEIGE = (238, 238, 210)
BROWN = (118, 150, 86)
GREEN_ARROW = (0, 200, 0, 180)
RED_ARROW = (200, 0, 0, 180)
BLUE_ARROW = (0, 100, 255, 180)
YELLOW_HIGHLIGHT = (255, 255, 0, 100)
BG_COLOR = (30, 30, 30)
PANEL_BG = (50, 50, 50)
TEXT_COLOR = (255, 255, 255)

class AnalysisViewer:
    """Interactive viewer for analyzed chess games"""
    
    def __init__(self, pgn_path: str, analysis_path: str):
        pygame.init()
        
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Game Analysis Viewer")
        
        self.clock = pygame.time.Clock()
        self.images = loadImages(SQUARESIZE)
        
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
    
    def draw_board(self):
        """Draw the chess board"""
        for rank in range(8):
            for file in range(8):
                color = BEIGE if (rank + file) % 2 == 0 else BROWN
                pygame.draw.rect(
                    self.screen, color,
                    pygame.Rect(30 + file * SQUARESIZE, 60 + rank * SQUARESIZE, 
                               SQUARESIZE, SQUARESIZE)
                )
    
    def draw_pieces(self):
        """Draw chess pieces on the board"""
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                col = chess.square_file(square)
                row = 7 - chess.square_rank(square)
                img = self.images.get(piece.symbol())
                
                if isinstance(img, pygame.Surface):
                    self.screen.blit(img, (30 + col * SQUARESIZE, 60 + row * SQUARESIZE))
    
    def draw_arrow(self, from_square: int, to_square: int, color: tuple):
        """Draw an arrow from one square to another"""
        from_col = chess.square_file(from_square)
        from_row = 7 - chess.square_rank(from_square)
        to_col = chess.square_file(to_square)
        to_row = 7 - chess.square_rank(to_square)
        
        start_x = 30 + from_col * SQUARESIZE + SQUARESIZE // 2
        start_y = 60 + from_row * SQUARESIZE + SQUARESIZE // 2
        end_x = 30 + to_col * SQUARESIZE + SQUARESIZE // 2
        end_y = 60 + to_row * SQUARESIZE + SQUARESIZE // 2
        
        # Create transparent surface for arrow
        arrow_surface = pygame.Surface((BOARD_SIZE, BOARD_SIZE), pygame.SRCALPHA)
        
        # Draw arrow line
        pygame.draw.line(arrow_surface, color, 
                        (start_x - 30, start_y - 60), 
                        (end_x - 30, end_y - 60), 8)
        
        # Draw arrowhead
        import math
        angle = math.atan2(end_y - start_y, end_x - start_x)
        arrow_size = 20
        
        arrow_points = [
            (end_x - 30, end_y - 60),
            (end_x - 30 - arrow_size * math.cos(angle - math.pi/6),
             end_y - 60 - arrow_size * math.sin(angle - math.pi/6)),
            (end_x - 30 - arrow_size * math.cos(angle + math.pi/6),
             end_y - 60 - arrow_size * math.sin(angle + math.pi/6))
        ]
        pygame.draw.polygon(arrow_surface, color, arrow_points)
        
        self.screen.blit(arrow_surface, (30, 60))
    
    def draw_move_classification(self):
        """Draw the current move's classification"""
        if self.current_move >= len(self.analysis.get("detailed_moves", [])):
            return
        
        move_data = self.analysis["detailed_moves"][self.current_move]
        classification = move_data.get("classification", "unknown")
        
        # Classification colors and emojis
        class_info = {
            "brilliant": ("⭐ Brilliant", (255, 215, 0)),
            "great": ("🌟 Great", (100, 255, 100)),
            "best": ("✅ Best", (0, 255, 0)),
            "excellent": ("👍 Excellent", (150, 255, 150)),
            "good": ("✓ Good", (200, 255, 200)),
            "book": ("📖 Book", (180, 180, 255)),
            "inaccuracy": ("⚠️ Inaccuracy", (255, 200, 0)),
            "mistake": ("❌ Mistake", (255, 150, 0)),
            "blunder": ("💥 Blunder", (255, 0, 0))
        }
        
        label, color = class_info.get(classification, ("Unknown", (150, 150, 150)))
        
        # Draw classification badge
        badge_rect = pygame.Rect(30, 20, 200, 35)
        pygame.draw.rect(self.screen, color, badge_rect, border_radius=8)
        pygame.draw.rect(self.screen, (255, 255, 255), badge_rect, 2, border_radius=8)
        
        text = self.text_font.render(label, True, (0, 0, 0))
        text_rect = text.get_rect(center=badge_rect.center)
        self.screen.blit(text, text_rect)
    
    def draw_sidebar(self):
        """Draw the analysis sidebar"""
        sidebar_x = BOARD_SIZE + 60
        
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
        
        # Move classifications summary
        classifications = self.analysis.get("move_classifications", {})
        
        class_display = [
            ("⭐ Brilliant", classifications.get("brilliant", 0)),
            ("🌟 Great", classifications.get("great", 0)),
            ("✅ Best", classifications.get("best", 0)),
            ("👍 Excellent", classifications.get("excellent", 0)),
            ("✓ Good", classifications.get("good", 0)),
            ("📖 Book", classifications.get("book", 0)),
            ("⚠️ Inaccuracy", classifications.get("inaccuracy", 0)),
            ("❌ Mistake", classifications.get("mistake", 0)),
            ("💥 Blunder", classifications.get("blunder", 0))
        ]
        
        for label, count in class_display:
            text = self.small_font.render(f"{label}: {count}", True, (220, 220, 220))
            self.screen.blit(text, (sidebar_x + 20, y_offset))
            y_offset += 25
        
        y_offset += 20
        
        # Estimated ELO
        elo = self.analysis.get("estimated_elo", 0)
        elo_text = self.text_font.render(f"🎯 Estimated ELO: {elo}", True, (255, 215, 0))
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
        y_offset = HEIGHT - 120
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
                self.draw_arrow(move.from_square, move.to_square, GREEN_ARROW)
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
            self.draw_board()
            self.draw_pieces()
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