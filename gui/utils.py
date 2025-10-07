# import pygame

# SQUARESIZE = 60
# WHITE = (255, 255, 255)
# BROWN = (181, 136, 99)
# BEIGE = (240, 217, 181)

# def loadImages(squareSize):
#     pieces = {}
#     for piece in ['P', 'N', 'B', 'R', 'Q', 'K']:
#         try:
#             pieces[piece] = pygame.transform.scale(pygame.image.load(f'img/w{piece}.png'), (squareSize, squareSize))
#             pieces[piece.lower()] = pygame.transform.scale(pygame.image.load(f'img/b{piece}.png'), (squareSize, squareSize))
#         except:
#             font = pygame.font.SysFont('Arial', 36)
#             pieces[piece] = font.render(piece, True, (0, 0, 0))
#             pieces[piece.lower()] = font.render(piece.lower(), True, (0, 0, 0))
#     return pieces

# def mouseToSquare(pos, squareSize):
#     col = pos[0] // squareSize
#     row = 7 - (pos[1] // squareSize)
#     import chess
#     return chess.square(col, row)



import pygame

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
    col = pos[0] // squareSize
    row = 7 - (pos[1] // squareSize)
    import chess
    return chess.square(col, row)