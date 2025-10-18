import pygame
import time
from utils import load_font
import os
font = load_font(size=60)
FONT_PATH = os.path.join(os.path.dirname(__file__), "font", "Orbitron-Bold.ttf")

# Load safely
if os.path.exists(FONT_PATH):
    font = pygame.font.Font(FONT_PATH, 60)
else:
    print(f"[Warning] Font not found at {FONT_PATH}, using default system font.")
    font = pygame.font.SysFont("arial", 60)
class ChessTimer:
    def __init__(self, total_time):
        self.total_time = total_time  # total time per player (in seconds)
        self.remaining_white = total_time
        self.remaining_black = total_time
        self.last_time_update = time.time()
        self.text_color = "white"
        self.is_running = True

    def switch_turn(self):
        self.text_color = "black" if self.text_color == "white" else "white"
        self.last_time_update = time.time()

    def update(self):
        if not self.is_running:
            return
        now = time.time()
        elapsed = now - self.last_time_update
        self.last_time_update = now

        if self.text_color == "white":
            self.remaining_white -= elapsed
        else:
            self.remaining_black -= elapsed

        # Prevent negative time
        self.remaining_white = max(self.remaining_white, 0)
        self.remaining_black = max(self.remaining_black, 0)

    def draw(self, screen, font):
        screen_width, screen_height = screen.get_size()

        # Board + margins info
        BOARD_HEIGHT = 8 * 60
        MARGIN_TOP = 60
        MARGIN_BOTTOM = 60

        def format_time(seconds):
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes:02}:{secs:02}"

        text_color = (255, 255, 255)

        # Render text
        white_text = font.render(f"Player: {format_time(self.remaining_white)}", True, text_color)
        black_text = font.render(f"Computer: {format_time(self.remaining_black)}", True, text_color)

        # Position rectangles
        black_rect = black_text.get_rect(center=(screen_width // 2, MARGIN_TOP // 2))
        white_rect = white_text.get_rect(center=(screen_width // 2, MARGIN_TOP + BOARD_HEIGHT + MARGIN_BOTTOM // 2))

        # === Draw clean background for both timers first ===
        bg_color = (40, 40, 40)  # dark background (same as board margin)
        padding_x = 12
        padding_y = 6

        for rect in [black_rect, white_rect]:
            bg_rect = pygame.Rect(
                rect.left - padding_x,
                rect.top - padding_y,
                rect.width + 2 * padding_x,
                rect.height + 2 * padding_y
            )
            pygame.draw.rect(screen, bg_color, bg_rect, border_radius=8)

         # === Then highlight only the active player's timer ===
        highlight_color = (70, 70, 70)  # soft gray like chess.com
        if self.text_color == "white":
            active_rect = white_rect
        else:
            active_rect = black_rect

        highlight_rect = pygame.Rect(
            active_rect.left - padding_x,
            active_rect.top - padding_y,
            active_rect.width + 2 * padding_x,
            active_rect.height + 2 * padding_y
        )
        pygame.draw.rect(screen, highlight_color, highlight_rect, border_radius=8)

        # === Draw text on top ===
        screen.blit(black_text, black_rect)
        screen.blit(white_text, white_rect)
