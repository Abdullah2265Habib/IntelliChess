import pygame
import chess

SQUARESIZE = 60
CIRCLECOLOR = (0, 0, 0, 80)
HIGHLIGHTCOLOR = (255, 255, 0, 100)
BEIGE = (240, 217, 181)
BROWN = (181, 136, 99)

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
            pygame.draw.rect(screen, color, pygame.Rect(file * SQUARESIZE, rank * SQUARESIZE, SQUARESIZE, SQUARESIZE))

def drawPieces(screen, board, images):
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            col = chess.square_file(square)
            row = 7 - chess.square_rank(square)
            img_or_text = images.get(piece.symbol())
            if isinstance(img_or_text, pygame.Surface):
                screen.blit(img_or_text, (col * SQUARESIZE, row * SQUARESIZE))
            else:
                text_rect = img_or_text.get_rect(center=(col * SQUARESIZE + SQUARESIZE // 2, row * SQUARESIZE + SQUARESIZE // 2))

                #// is the similar version of doing type casting from float to int

                screen.blit(img_or_text, text_rect)

def highlightValidMoves(screen, square):
    if square is not None:
        col = chess.square_file(square)
        row = 7 - chess.square_rank(square)
        surface = pygame.Surface((SQUARESIZE, SQUARESIZE), pygame.SRCALPHA)
        pygame.draw.rect(surface, HIGHLIGHTCOLOR, (0, 0, SQUARESIZE, SQUARESIZE))
        screen.blit(surface, (col * SQUARESIZE, row * SQUARESIZE))

def drawValidMoves(screen, board, selectedSquare):
    if selectedSquare is None:
        return
    for move in board.legal_moves:
        if move.from_square == selectedSquare:
            col = chess.square_file(move.to_square)
            row = 7 - chess.square_rank(move.to_square)
            surface = pygame.Surface((SQUARESIZE, SQUARESIZE), pygame.SRCALPHA)
            pygame.draw.circle(surface, CIRCLECOLOR, (SQUARESIZE // 2, SQUARESIZE // 2), SQUARESIZE // 6)
            screen.blit(surface, (col * SQUARESIZE, row * SQUARESIZE))
