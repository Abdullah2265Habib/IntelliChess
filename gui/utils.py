import pygame

SQUARE_SIZE = 60
WHITE = (255, 255, 255)
BROWN = (181, 136, 99)
BEIGE = (240, 217, 181)

def loadImages(square_size):
    pieces = {}
    for piece in ['P', 'N', 'B', 'R', 'Q', 'K']:
        try:
            pieces[piece] = pygame.transform.scale(pygame.image.load(f'w{piece}.png'), (square_size, square_size))
            pieces[piece.lower()] = pygame.transform.scale(pygame.image.load(f'b{piece}.png'), (square_size, square_size))
        except:
            font = pygame.font.SysFont('Arial', 36)
            pieces[piece] = font.render(piece, True, (0, 0, 0))
            pieces[piece.lower()] = font.render(piece.lower(), True, (0, 0, 0))
    return pieces

def mouseToSquarequare(pos, square_size):
    col = pos[0] // square_size
    row = 7 - (pos[1] // square_size)
    import chess
    return chess.square(col, row)
