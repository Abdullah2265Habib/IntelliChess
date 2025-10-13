import pygame
import chess

# === Constants ===
SQUARESIZE = 60
MARGIN_TOP = 60     # space for top timer
MARGIN_BOTTOM = 60  # space for bottom timer
BOARD_OFFSET_Y = MARGIN_TOP  # board starts after top space here we shift the boardfrom (0,0 to 60 px down)

CIRCLECOLOR = (0, 0, 0, 80)
HIGHLIGHTCOLOR = (255, 255, 0, 100)
BEIGE = (238, 238, 210)
BROWN = (118, 150, 86)
TIMER_BG = (40, 40, 40)
TIMER_TEXT = (255, 255, 255)


# === Board Drawing ===
def displayBoard(screen):
    #in chess board, rank is a set of horizantal rows which are represented by a number like 1,2,3,4,5,6,7,8
    #file is the set of vertical column which are represented by alphabets like a,b,c,d,e,f,g,h
    # 
    # both rank and file is combined to completely define a move. like ( 1.e4 e5 2.Nc3 Nf6 ....etc)  

    for rank in range(8):
        for file in range(8):
            if((rank + file) % 2 == 0):
                color =BEIGE
            else:
                color =BROWN

            pygame.draw.rect(
                screen,
                color,
                pygame.Rect(
                    file * SQUARESIZE,
                    BOARD_OFFSET_Y + rank * SQUARESIZE,# rank * SQUARESIZE from this to BOARD_OFFSET_Y + rank * SQUARESIZE to change the coordinates of board
                    SQUARESIZE,
                    SQUARESIZE
                )
            )


def drawPieces(screen, board, images):
    """
    Draws chess pieces on the board (with offset).
    """
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            col = chess.square_file(square)
            row = 7 - chess.square_rank(square)
            img_or_text = images.get(piece.symbol())
            y_pos = BOARD_OFFSET_Y + row * SQUARESIZE  # Change the y position of board

            if isinstance(img_or_text, pygame.Surface):
                screen.blit(img_or_text, (col * SQUARESIZE, y_pos))  # In place of row*SQUARESIZE since rows starting point change so we rewrite it with new 
            else:
                text_rect = img_or_text.get_rect(
                    center=(
                        col * SQUARESIZE + SQUARESIZE // 2,  #here // is used to typcast the type from float to int 
                        y_pos + SQUARESIZE // 2  # row * SQUARESIZE here again changes
                    )
                )
                screen.blit(img_or_text, text_rect)


def highlightValidMoves(screen, square):
    """
    Highlights the selected square.
    """
    if square is not None:
        col = chess.square_file(square)
        row = 7 - chess.square_rank(square)
        surface = pygame.Surface((SQUARESIZE, SQUARESIZE), pygame.SRCALPHA)
        pygame.draw.rect(surface, HIGHLIGHTCOLOR, (0, 0, SQUARESIZE, SQUARESIZE))
        screen.blit(surface, (col * SQUARESIZE, BOARD_OFFSET_Y + row * SQUARESIZE))


def drawValidMoves(screen, board, selectedSquare):
    """
    Draws small circles on legal move destination squares.
    """
    if selectedSquare is None:
        return

    for move in board.legal_moves:
        if move.from_square == selectedSquare:
            col = chess.square_file(move.to_square)
            row = 7 - chess.square_rank(move.to_square)
            surface = pygame.Surface((SQUARESIZE, SQUARESIZE), pygame.SRCALPHA)
            pygame.draw.circle(
                surface, CIRCLECOLOR,
                (SQUARESIZE // 2, SQUARESIZE // 2),
                SQUARESIZE // 6
            )
            screen.blit(surface, (col * SQUARESIZE, BOARD_OFFSET_Y + row * SQUARESIZE)) 