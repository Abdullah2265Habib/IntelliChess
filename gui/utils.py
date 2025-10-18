import pygame
import os
SQUARESIZE = 60
WHITE = (255, 255, 255)
BROWN = (181, 136, 99)
BEIGE = (240, 217, 181)
def loadImages(squareSize):
    pieces = {}
    for piece in ['P', 'N', 'B', 'R', 'Q', 'K']:
        try:
            # Load white piece (uppercase)
            pieces[piece] = pygame.transform.scale(
                pygame.image.load(f'gui/img/w{piece}.png'), 
                (squareSize, squareSize)
            )
            # Load black piece (uppercase)
            pieces[piece.lower()] = pygame.transform.scale(
                pygame.image.load(f'gui/img/b{piece}.png'), 
                (squareSize, squareSize)
            )
        except pygame.error:
            try:
                pieces[piece] = pygame.transform.scale(
                    pygame.image.load(f'img/w{piece.lower()}.png'), 
                    (squareSize, squareSize)
                )
                pieces[piece.lower()] = pygame.transform.scale(
                    pygame.image.load(f'img/b{piece.lower()}.png'), 
                    (squareSize, squareSize)
                )
            except pygame.error:
                print(f"Could not load images for {piece}")
                font = pygame.font.SysFont('Arial', 36)
                pieces[piece] = font.render(piece, True, (0, 0, 0))
                pieces[piece.lower()] = font.render(piece.lower(), True, (0, 0, 0))
    return pieces

def mouseToSquare(pos, squareSize):
    from board import BOARD_OFFSET_Y   # import the offset as now the top margin in 60px
    col = pos[0] // squareSize
    # This ensures that the click coordinates line up perfectly with where your chessboard actually starts on screen (after the 60px timer bar).
    adjusted_y = pos[1] - BOARD_OFFSET_Y  # shift click down
    if adjusted_y < 0 or adjusted_y >= 8 * squareSize:
        return None  # click outside the board
    row = 7 - (pos[1] // squareSize)
    import chess
    return chess.square(col, row)

# Function of load font added as i add a new file of fonts to make our appplication more realistic i used gaming fonts
def load_font(name="Orbitron-Bold.ttf", size=32):
    if not pygame.font.get_init():
        pygame.font.init()
    FONT_PATH = os.path.join(os.path.dirname(__file__), "font", "Orbitron-Bold.ttf")
    #font = pygame.font.Font(FONT_PATH, 50)
    if not os.path.exists(FONT_PATH):  #checks for font file first
        print(f"[Warning] Font not found at {FONT_PATH}, using default.")
        return pygame.font.SysFont("arial", size) #if the font isnot found chnage the font to Arial without creating error
    return pygame.font.Font(FONT_PATH, size)