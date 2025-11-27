"""
Game Selector - Choose and analyze past games
Save as: analysis/game_selector.py
"""

import pygame
import os
import glob
import json
from datetime import datetime
from typing import List, Tuple, Optional

# Initialize Pygame
pygame.init()

# Constants
WIDTH = 800
HEIGHT = 600
BG_COLOR = (30, 30, 30)
PANEL_BG = (50, 50, 50)
HOVER_BG = (70, 70, 70)
SELECTED_BG = (90, 90, 110)
TEXT_COLOR = (255, 255, 255)
ACCENT_COLOR = (100, 200, 255)

class GameInfo:
    """Store information about a saved game"""
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.filename = os.path.basename(filepath)
        self.analysis_exists = os.path.exists(filepath.replace(".txt", "_analysis.json"))
        
        # Parse date from filename (format: YYYY-MM-DD_HH-MM-SS.txt)
        try:
            date_str = self.filename.replace(".txt", "")
            self.date = datetime.strptime(date_str, "%Y-%m-%d_%H-%M-%S")
            self.display_date = self.date.strftime("%B %d, %Y - %I:%M %p")
        except:
            self.date = datetime.now()
            self.display_date = "Unknown Date"
        
        # Load game result if available
        self.result = "Unknown"
        self.event = "Bullet: 1 min"
        try:
            with open(filepath, 'r') as f:
                content = f.read()
                if '[Result "' in content:
                    result_start = content.find('[Result "') + 9
                    result_end = content.find('"]', result_start)
                    self.result = content[result_start:result_end]
                if '[Event "' in content:
                    event_start = content.find('[Event "') + 8
                    event_end = content.find('"]', event_start)
                    self.event = content[event_start:event_end]
        except:
            pass
        
        # Load ELO if analysis exists
        self.estimated_elo = None
        if self.analysis_exists:
            try:
                analysis_file = filepath.replace(".txt", "_analysis.json")
                with open(analysis_file, 'r') as f:
                    analysis = json.load(f)
                    self.estimated_elo = analysis.get("estimated_elo")
            except:
                pass

class GameSelector:
    """Interactive game selector interface"""
    
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("IntelliChess - Game Selector")
        self.clock = pygame.time.Clock()
        
        # Load fonts
        try:
            font_path = os.path.join("gui", "font", "Orbitron-Bold.ttf")
            self.title_font = pygame.font.Font(font_path, 36)
            self.text_font = pygame.font.Font(font_path, 20)
            self.small_font = pygame.font.Font(font_path, 16)
        except:
            self.title_font = pygame.font.SysFont('Arial', 36, bold=True)
            self.text_font = pygame.font.SysFont('Arial', 20)
            self.small_font = pygame.font.SysFont('Arial', 16)
        
        # Load games
        self.games: List[GameInfo] = []
        self.load_games()
        
        # UI state
        self.selected_index = 0
        self.hover_index = -1
        self.scroll_offset = 0
        self.item_height = 100
        self.visible_items = (HEIGHT - 150) // self.item_height
    
    def load_games(self):
        """Load all saved games"""
        game_files = glob.glob("games/*[!_analysis].txt")
        
        if not game_files:
            return
        
        # Sort by date (newest first)
        game_files.sort(key=os.path.getctime, reverse=True)
        
        for filepath in game_files:
            self.games.append(GameInfo(filepath))
    
    def draw_game_item(self, game: GameInfo, y_pos: int, is_selected: bool, is_hover: bool):
        """Draw a single game item"""
        # Background
        if is_selected:
            color = SELECTED_BG
        elif is_hover:
            color = HOVER_BG
        else:
            color = PANEL_BG
        
        item_rect = pygame.Rect(40, y_pos, WIDTH - 80, self.item_height - 10)
        pygame.draw.rect(self.screen, color, item_rect, border_radius=10)
        
        # Border for selected
        if is_selected:
            pygame.draw.rect(self.screen, ACCENT_COLOR, item_rect, 3, border_radius=10)
        
        # Date
        date_text = self.text_font.render(game.display_date, True, TEXT_COLOR)
        self.screen.blit(date_text, (60, y_pos + 15))
        
        # Result
        result_colors = {
            "1-0": (150, 255, 150),
            "0-1": (255, 150, 150),
            "1/2-1/2": (200, 200, 200),
            "*": (180, 180, 180)
        }
        result_color = result_colors.get(game.result, (180, 180, 180))
        result_text = self.small_font.render(f"Result: {game.result}", True, result_color)
        self.screen.blit(result_text, (60, y_pos + 50))
        
        # Analysis status
        if game.analysis_exists:
            status_text = self.small_font.render("Analysis Available", True, (150, 255, 150))
            self.screen.blit(status_text, (250, y_pos + 50))
            
            if game.estimated_elo:
                elo_text = self.small_font.render(f"ELO: {game.estimated_elo}", True, ACCENT_COLOR)
                self.screen.blit(elo_text, (450, y_pos + 50))
        else:
            status_text = self.small_font.render("Not Analyzed", True, (255, 200, 100))
            self.screen.blit(status_text, (250, y_pos + 50))
    
    def draw(self):
        """Draw the interface"""
        self.screen.fill(BG_COLOR)
        
        # Title
        title = self.title_font.render("Select a Game to Analyze", True, TEXT_COLOR)
        title_rect = title.get_rect(center=(WIDTH // 2, 50))
        self.screen.blit(title, title_rect)
        
        # Draw games list
        if not self.games:
            no_games = self.text_font.render("No games found in 'games' folder", True, (200, 200, 200))
            no_games_rect = no_games.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            self.screen.blit(no_games, no_games_rect)
        else:
            # Calculate visible range
            start_idx = self.scroll_offset
            end_idx = min(start_idx + self.visible_items, len(self.games))
            
            y_pos = 120
            for i in range(start_idx, end_idx):
                game = self.games[i]
                is_selected = (i == self.selected_index)
                is_hover = (i == self.hover_index)
                
                self.draw_game_item(game, y_pos, is_selected, is_hover)
                y_pos += self.item_height
            
            # Draw scrollbar if needed
            if len(self.games) > self.visible_items:
                scrollbar_height = max(20, int(self.visible_items * HEIGHT / len(self.games)))
                scrollbar_y = 120 + int(self.scroll_offset * (HEIGHT - 200) / len(self.games))
                scrollbar_rect = pygame.Rect(WIDTH - 25, scrollbar_y, 10, scrollbar_height)
                pygame.draw.rect(self.screen, (150, 150, 150), scrollbar_rect, border_radius=5)
        
        # Instructions
        instructions = [
            "↑↓ Navigate | Enter: Analyze | A: Analyze All | Esc: Exit"
        ]
        
        y_offset = HEIGHT - 40
        for instruction in instructions:
            text = self.small_font.render(instruction, True, (180, 180, 180))
            text_rect = text.get_rect(center=(WIDTH // 2, y_offset))
            self.screen.blit(text, text_rect)
            y_offset += 25
        
        pygame.display.flip()
    
    def handle_selection(self):
        """Handle game selection"""
        if not self.games or self.selected_index < 0 or self.selected_index >= len(self.games):
            return
        
        game = self.games[self.selected_index]
        
        # Check if analysis exists
        if not game.analysis_exists:
            print(f"\nAnalyzing {game.filename}...")
            self.analyze_game(game.filepath)
        
        # Launch viewer
        self.launch_viewer(game.filepath)
    
    def analyze_game(self, pgn_file: str):
        """Analyze a game"""
        import sys
        import shutil
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        
        def find_stockfish():
            """Find Stockfish executable"""
            # Check system PATH
            path = shutil.which("stockfish")
            if path:
                return path
                
            # Check common locations
            common_paths = [
                "stockfish.exe",
                "stockfish",
                "engine/stockfish.exe",
                "engine/stockfish",
                "bin/stockfish.exe",
                "bin/stockfish"
            ]
            
            for p in common_paths:
                if os.path.exists(p):
                    return os.path.abspath(p)
                    
            return None
        
        try:
            # Import handling both direct run and module run
            try:
                from game_analyzer import ChessGameAnalyzer
            except ImportError:
                from analysis.game_analyzer import ChessGameAnalyzer
            
            stockfish_path = find_stockfish()
            if stockfish_path:
                print(f"Found Stockfish at: {stockfish_path}")
            else:
                print("Stockfish not found, will try Lichess cloud analysis")
            
            analyzer = ChessGameAnalyzer(stockfish_path=stockfish_path)
            analysis = analyzer.analyze_pgn_file(pgn_file)
            
            if "error" not in analysis:
                # Save analysis
                output_file = pgn_file.replace(".txt", "_analysis.json")
                with open(output_file, 'w') as f:
                    json.dump(analysis, f, indent=2)
                
                print(f"Analysis saved to: {output_file}")
                
                # Reload games to update analysis status
                self.games.clear()
                self.load_games()
            else:
                print(f"Analysis failed: {analysis['error']}")
        except Exception as e:
            print(f"Error analyzing game: {e}")
            import traceback
            traceback.print_exc()
    
    def analyze_all_games(self):
        """Analyze all games without analysis"""
        games_to_analyze = [g for g in self.games if not g.analysis_exists]
        
        if not games_to_analyze:
            print("\nAll games already analyzed!")
            return
        
        print(f"\nAnalyzing {len(games_to_analyze)} games...")
        
        for i, game in enumerate(games_to_analyze, 1):
            print(f"\n[{i}/{len(games_to_analyze)}] Analyzing {game.filename}...")
            self.analyze_game(game.filepath)
        
        print("\nAll games analyzed!")
    
    def launch_viewer(self, pgn_file: str):
        """Launch the analysis viewer"""
        analysis_file = pgn_file.replace(".txt", "_analysis.json")
        
        if not os.path.exists(analysis_file):
            print(f"Analysis file not found: {analysis_file}")
            return
        
        # Import handling both direct run and module run
        try:
            from analysis_viewer import AnalysisViewer
        except ImportError:
            from analysis.analysis_viewer import AnalysisViewer
        
        try:
            viewer = AnalysisViewer(pgn_file, analysis_file)
            viewer.run()
            
            # Redraw after viewer closes
            self.draw()
        except Exception as e:
            print(f"Viewer error: {e}")
            import traceback
            traceback.print_exc()
    
    def run(self):
        """Main loop"""
        running = True
        
        while running:
            self.draw()
            self.clock.tick(60)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    
                    elif event.key == pygame.K_UP:
                        if self.selected_index > 0:
                            self.selected_index -= 1
                            if self.selected_index < self.scroll_offset:
                                self.scroll_offset = self.selected_index
                    
                    elif event.key == pygame.K_DOWN:
                        if self.selected_index < len(self.games) - 1:
                            self.selected_index += 1
                            if self.selected_index >= self.scroll_offset + self.visible_items:
                                self.scroll_offset = self.selected_index - self.visible_items + 1
                    
                    elif event.key == pygame.K_RETURN:
                        self.handle_selection()
                    
                    elif event.key == pygame.K_a:
                        self.analyze_all_games()
                
                elif event.type == pygame.MOUSEWHEEL:
                    if event.y > 0 and self.scroll_offset > 0:
                        self.scroll_offset -= 1
                    elif event.y < 0 and self.scroll_offset < len(self.games) - self.visible_items:
                        self.scroll_offset += 1
                
                elif event.type == pygame.MOUSEMOTION:
                    x, y = event.pos
                    if 40 <= x <= WIDTH - 40 and 120 <= y <= HEIGHT - 80:
                        item_index = (y - 120) // self.item_height + self.scroll_offset
                        if 0 <= item_index < len(self.games):
                            self.hover_index = item_index
                        else:
                            self.hover_index = -1
                    else:
                        self.hover_index = -1
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.hover_index >= 0:
                        self.selected_index = self.hover_index
                        self.handle_selection()
        
        pygame.quit()


def main():
    """Launch the game selector"""
    print("\n" + "="*60)
    print("IntelliChess Game Selector")
    print("="*60 + "\n")
    
    selector = GameSelector()
    selector.run()


if __name__ == "__main__":
    main()