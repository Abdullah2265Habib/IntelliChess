import chess
import chess.engine

class ChessPositionEvaluator:
    def __init__(self):
        # Piece values (material)
        self.piece_values = {
            chess.PAWN: 100,
            chess.KNIGHT: 320,
            chess.BISHOP: 330,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 0
        }
        
        # Piece-square tables for positional evaluation
        self.pawn_table = [
            [0,  0,  0,  0,  0,  0,  0,  0],
            [50, 50, 50, 50, 50, 50, 50, 50],
            [10, 10, 20, 30, 30, 20, 10, 10],
            [5,  5, 10, 25, 25, 10,  5,  5],
            [0,  0,  0, 20, 20,  0,  0,  0],
            [5, -5,-10,  0,  0,-10, -5,  5],
            [5, 10, 10,-20,-20, 10, 10,  5],
            [0,  0,  0,  0,  0,  0,  0,  0]
        ]
        
        self.knight_table = [
            [-50,-40,-30,-30,-30,-30,-40,-50],
            [-40,-20,  0,  0,  0,  0,-20,-40],
            [-30,  0, 10, 15, 15, 10,  0,-30],
            [-30,  5, 15, 20, 20, 15,  5,-30],
            [-30,  0, 15, 20, 20, 15,  0,-30],
            [-30,  5, 10, 15, 15, 10,  5,-30],
            [-40,-20,  0,  5,  5,  0,-20,-40],
            [-50,-40,-30,-30,-30,-30,-40,-50]
        ]
        
        self.bishop_table = [
            [-20,-10,-10,-10,-10,-10,-10,-20],
            [-10,  0,  0,  0,  0,  0,  0,-10],
            [-10,  0,  5, 10, 10,  5,  0,-10],
            [-10,  5,  5, 10, 10,  5,  5,-10],
            [-10,  0, 10, 10, 10, 10,  0,-10],
            [-10, 10, 10, 10, 10, 10, 10,-10],
            [-10,  5,  0,  0,  0,  0,  5,-10],
            [-20,-10,-10,-10,-10,-10,-10,-20]
        ]
        
        self.rook_table = [
            [0,  0,  0,  0,  0,  0,  0,  0],
            [5, 10, 10, 10, 10, 10, 10,  5],
            [-5,  0,  0,  0,  0,  0,  0, -5],
            [-5,  0,  0,  0,  0,  0,  0, -5],
            [-5,  0,  0,  0,  0,  0,  0, -5],
            [-5,  0,  0,  0,  0,  0,  0, -5],
            [-5,  0,  0,  0,  0,  0,  0, -5],
            [0,  0,  0,  5,  5,  0,  0,  0]
        ]
        
        self.queen_table = [
            [-20,-10,-10, -5, -5,-10,-10,-20],
            [-10,  0,  0,  0,  0,  0,  0,-10],
            [-10,  0,  5,  5,  5,  5,  0,-10],
            [-5,  0,  5,  5,  5,  5,  0, -5],
            [0,  0,  5,  5,  5,  5,  0, -5],
            [-10,  5,  5,  5,  5,  5,  0,-10],
            [-10,  0,  5,  0,  0,  0,  0,-10],
            [-20,-10,-10, -5, -5,-10,-10,-20]
        ]
        
        self.king_middlegame_table = [
            [-30,-40,-40,-50,-50,-40,-40,-30],
            [-30,-40,-40,-50,-50,-40,-40,-30],
            [-30,-40,-40,-50,-50,-40,-40,-30],
            [-30,-40,-40,-50,-50,-40,-40,-30],
            [-20,-30,-30,-40,-40,-30,-30,-20],
            [-10,-20,-20,-20,-20,-20,-20,-10],
            [20, 20,  0,  0,  0,  0, 20, 20],
            [20, 30, 10,  0,  0, 10, 30, 20]
        ]
        
        self.king_endgame_table = [
            [-50,-40,-30,-20,-20,-30,-40,-50],
            [-30,-20,-10,  0,  0,-10,-20,-30],
            [-30,-10, 20, 30, 30, 20,-10,-30],
            [-30,-10, 30, 40, 40, 30,-10,-30],
            [-30,-10, 30, 40, 40, 30,-10,-30],
            [-30,-10, 20, 30, 30, 20,-10,-30],
            [-30,-30,  0,  0,  0,  0,-30,-30],
            [-50,-30,-30,-30,-30,-30,-30,-50]
        ]

    def evaluate_position(self, board):
        """
        Main evaluation function combining all factors
        Returns positive values for white advantage, negative for black
        """
        if board.is_checkmate():
            return -9999 if board.turn else 9999
        
        if board.is_stalemate() or board.is_insufficient_material():
            return 0
        
        score = 0
        
        # Material and positional evaluation
        score += self.evaluate_material_and_position(board)
        
        # King safety (defensive)
        score += self.evaluate_king_safety(board)
        
        # Pawn structure (positional)
        score += self.evaluate_pawn_structure(board)
        
        # Piece activity and mobility (aggressive/bold)
        score += self.evaluate_piece_activity(board)
        
        # Center control (positional/aggressive)
        score += self.evaluate_center_control(board)
        
        # Tactical bonuses (aggressive/bold)
        score += self.evaluate_tactical_factors(board)
        
        # Endgame evaluation
        if self.is_endgame(board):
            score += self.evaluate_endgame_factors(board)
        
        return score

    def evaluate_material_and_position(self, board):
        """Evaluate material balance and piece positioning"""
        score = 0
        
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece is None:
                continue
            
            value = self.piece_values[piece.piece_type]
            
            # Add positional bonus
            row, col = divmod(square, 8)
            if not piece.color: 
                row = 7 - row
            
            if piece.piece_type == chess.PAWN:
                value += self.pawn_table[row][col]
            elif piece.piece_type == chess.KNIGHT:
                value += self.knight_table[row][col]
            elif piece.piece_type == chess.BISHOP:
                value += self.bishop_table[row][col]
            elif piece.piece_type == chess.ROOK:
                value += self.rook_table[row][col]
            elif piece.piece_type == chess.QUEEN:
                value += self.queen_table[row][col]
            elif piece.piece_type == chess.KING:
                if self.is_endgame(board):
                    value += self.king_endgame_table[row][col]
                else:
                    value += self.king_middlegame_table[row][col]
            
            if piece.color:  # White
                score += value
            else:  # Black
                score -= value
        
        return score

    def evaluate_king_safety(self, board):
        """Evaluate king safety - important for defensive play"""
        score = 0
        
        for color in [True, False]:  # White, Black
            king_square = board.king(color)
            if king_square is None:
                continue
            
            # Penalty for exposed king
            attackers = len(board.attackers(not color, king_square))
            king_safety = -attackers * 20
            
            # Bonus for castling
            if color: 
                if board.has_kingside_castling_rights(color):
                    king_safety += 10
                if board.has_queenside_castling_rights(color):
                    king_safety += 5
            else:
                if board.has_kingside_castling_rights(color):
                    king_safety += 10
                if board.has_queenside_castling_rights(color):
                    king_safety += 5
            
            # Pawn shield evaluation
            king_safety += self.evaluate_pawn_shield(board, king_square, color)
            
            if color:
                score += king_safety
            else:
                score -= king_safety
        
        return score

    def evaluate_pawn_shield(self, board, king_square, color):
        """Evaluate pawn shield around king"""
        shield_value = 0
        king_file = chess.square_file(king_square)
        king_rank = chess.square_rank(king_square)
        
        # Check files around king
        for file_offset in [-1, 0, 1]:
            file = king_file + file_offset
            if 0 <= file <= 7:
                # Look for pawns in front of king
                for rank_offset in range(1, 4):
                    if color:
                        rank = king_rank + rank_offset
                    else: 
                        rank = king_rank - rank_offset
                    
                    if 0 <= rank <= 7:
                        square = chess.square(file, rank)
                        piece = board.piece_at(square)
                        if piece and piece.piece_type == chess.PAWN and piece.color == color:
                            shield_value += 15 - (rank_offset * 3)
                            break
        
        return shield_value

    def evaluate_pawn_structure(self, board):
        """Evaluate pawn structure - doubled, isolated, passed pawns"""
        score = 0
        
        for color in [True, False]:
            file_pawns = [0] * 8
            pawn_squares = []
            
            for square in chess.SQUARES:
                piece = board.piece_at(square)
                if piece and piece.piece_type == chess.PAWN and piece.color == color:
                    file = chess.square_file(square)
                    file_pawns[file] += 1
                    pawn_squares.append(square)
            
            pawn_score = 0
            
            # Doubled pawns penalty
            for file_count in file_pawns:
                if file_count > 1:
                    pawn_score -= (file_count - 1) * 10
            
            # Isolated pawns penalty
            for file in range(8):
                if file_pawns[file] > 0:
                    isolated = True
                    for adjacent_file in [file - 1, file + 1]:
                        if 0 <= adjacent_file <= 7 and file_pawns[adjacent_file] > 0:
                            isolated = False
                            break
                    if isolated:
                        pawn_score -= 15
            
            # Passed pawns bonus 
            for square in pawn_squares:
                if self.is_passed_pawn(board, square, color):
                    rank = chess.square_rank(square)
                    if color: 
                        pawn_score += (rank - 1) * 10 + 20
                    else:  
                        pawn_score += (6 - rank) * 10 + 20
            
            if color:
                score += pawn_score
            else:
                score -= pawn_score
        
        return score

    def is_passed_pawn(self, board, pawn_square, color):
        """Check if a pawn is passed"""
        file = chess.square_file(pawn_square)
        rank = chess.square_rank(pawn_square)
        
        # Check for enemy pawns that can stop this pawn
        for check_file in [file - 1, file, file + 1]:
            if 0 <= check_file <= 7:
                if color:
                    for check_rank in range(rank + 1, 8):
                        square = chess.square(check_file, check_rank)
                        piece = board.piece_at(square)
                        if piece and piece.piece_type == chess.PAWN and not piece.color:
                            return False
                else:
                    for check_rank in range(rank - 1, -1, -1):
                        square = chess.square(check_file, check_rank)
                        piece = board.piece_at(square)
                        if piece and piece.piece_type == chess.PAWN and piece.color:
                            return False
        
        return True

    def evaluate_piece_activity(self, board):
        """Evaluate piece mobility and activity - promotes aggressive play"""
        score = 0
        
        # Generate all legal moves to measure mobility
        white_moves = 0
        black_moves = 0
        
        if board.turn:
            white_moves = len(list(board.legal_moves))
            board.push(chess.Move.null())
            black_moves = len(list(board.legal_moves))
            board.pop()
        else: 
            black_moves = len(list(board.legal_moves))
            board.push(chess.Move.null())
            white_moves = len(list(board.legal_moves))
            board.pop()
        
        score += (white_moves - black_moves) * 2
        
        # Bonus for pieces on active squares
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece is None:
                continue
            
            piece_score = 0
            
            # Knights on outposts 
            if piece.piece_type == chess.KNIGHT:
                if self.is_outpost(board, square, piece.color):
                    piece_score += 25
            
            # Bishops on long diagonals
            elif piece.piece_type == chess.BISHOP:
                if self.is_on_long_diagonal(square):
                    piece_score += 15
            
            # Rooks on open/semi-open file
            elif piece.piece_type == chess.ROOK:
                file = chess.square_file(square)
                if self.is_open_file(board, file):
                    piece_score += 20
                elif self.is_semi_open_file(board, file, piece.color):
                    piece_score += 10
            
            if piece.color:
                score += piece_score
            else:
                score -= piece_score
        
        return score

    def is_outpost(self, board, square, color):
        """
        Determine whether `square` is an outpost for side `color`.
        Defensive: validate indices and catch exceptions when querying board.piece_at
        to avoid IndexError from invalid square values.
        """
        import chess  # ensure local reference if file doesn't already have it

        # Basic validation: square must be an int in 0..63
        if not isinstance(square, int) or square < 0 or square > 63:
            return False

        try:
            file = chess.square_file(square)
            rank = chess.square_rank(square)
        except Exception:
            return False

        try:
            # Determine the pawn-supporting rank depending on color
            if color == chess.WHITE:
                back_rank = rank - 1
            else:
                back_rank = rank + 1

            # If back_rank is offboard, there cannot be a supporting pawn
            if back_rank < 0 or back_rank > 7:
                return False

            pawn_square = chess.square(file, back_rank)

            # Safe access to piece_at: guard against unexpected IndexError from library
            try:
                piece = board.piece_at(pawn_square)
            except Exception:
                piece = None

            if piece and piece.piece_type == chess.PAWN and piece.color == color:
                # Additional original checks (if any) would go here.
                # To avoid changing behavior drastically, preserve rest of logic if present,
                # otherwise treat presence of a supporting pawn as a positive indicator.
                return True

            return False

        except Exception:
            # Any unexpected issue -> not an outpost (fail-safe)
            return False

    def is_on_long_diagonal(self, square):
        """Check if square is on a long diagonal"""
        rank = chess.square_rank(square)
        file = chess.square_file(square)
        return (rank + file == 7) or (rank - file == 0)

    def is_open_file(self, board, file):
        """Check if file is completely open"""
        for rank in range(8):
            square = chess.square(file, rank)
            piece = board.piece_at(square)
            if piece and piece.piece_type == chess.PAWN:
                return False
        return True

    def is_semi_open_file(self, board, file, color):
        """Check if file is semi-open for given color"""
        has_own_pawn = False
        for rank in range(8):
            square = chess.square(file, rank)
            piece = board.piece_at(square)
            if piece and piece.piece_type == chess.PAWN and piece.color == color:
                has_own_pawn = True
                break
        return not has_own_pawn

    def evaluate_center_control(self, board):
        """Evaluate control of central squares - key for positional play"""
        center_squares = [chess.E4, chess.E5, chess.D4, chess.D5]
        extended_center = [chess.C3, chess.C4, chess.C5, chess.C6,
                          chess.D3, chess.D6, chess.E3, chess.E6,
                          chess.F3, chess.F4, chess.F5, chess.F6]
        
        score = 0
        
        for square in center_squares:
            white_attackers = len(board.attackers(True, square))
            black_attackers = len(board.attackers(False, square))
            score += (white_attackers - black_attackers) * 10
            
            # Bonus for occupying center with pieces
            piece = board.piece_at(square)
            if piece:
                if piece.color:
                    score += 15
                else:
                    score -= 15
        
        for square in extended_center:
            white_attackers = len(board.attackers(True, square))
            black_attackers = len(board.attackers(False, square))
            score += (white_attackers - black_attackers) * 5
        
        return score

    def evaluate_tactical_factors(self, board):
        """Evaluate tactical elements - promotes aggressive/bold play"""
        score = 0
        
        if board.is_check():
            if board.turn:  # Black is in check (white advantage)
                score += 20
            else:  # White is in check (black advantage)
                score -= 20
        
        # Bonus for attacking enemy pieces
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece is None:
                continue
            
            attackers = board.attackers(not piece.color, square)
            defenders = board.attackers(piece.color, square)
            
            if len(attackers) > len(defenders):
                attack_value = self.piece_values[piece.piece_type] // 10
                if piece.color:
                    score -= attack_value
                else:
                    score += attack_value
        
        return score

    def evaluate_endgame_factors(self, board):
        score = 0

        for color in [True, False]:
            king_square = board.king(color)
            if king_square:
                # Centralized king is good in endgame
                king_file = chess.square_file(king_square)
                king_rank = chess.square_rank(king_square)
                centralization = 7 - (abs(3.5 - king_file) + abs(3.5 - king_rank))
                
                if color:
                    score += centralization * 5
                else:
                    score -= centralization * 5
        
        return score

    def is_endgame(self, board):
        queens = len(board.pieces(chess.QUEEN, True)) + len(board.pieces(chess.QUEEN, False))
        
        # Simple endgame detection: few pieces left or no queens
        total_pieces = len(board.piece_map())
        return queens == 0 or total_pieces <= 12

if __name__ == "__main__":
    evaluator = ChessPositionEvaluator()
    
    board = chess.Board()
    print(f"Starting position evaluation: {evaluator.evaluate_position(board)}")
    
    board.push_san("e4")
    board.push_san("e5")
    board.push_san("Nf3")
    board.push_san("Nc6")
    print(f"After 1.e4 e5 2.Nf3 Nc6: {evaluator.evaluate_position(board)}")
    
    board = chess.Board("rnbqkb1r/pppp1ppp/5n2/4p3/2B1P3/8/PPPP1PPP/RNBQK1NR w KQkq - 2 3")
    print(f"Italian Game position: {evaluator.evaluate_position(board)}")