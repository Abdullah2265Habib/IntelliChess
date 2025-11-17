# [file name]: engine/endgame/endgame.py
import chess
import random
import os
from collections import defaultdict

class BasicEndgame:
    """Basic endgame knowledge without external tablebases"""
    
    def __init__(self):
        self.knowledge = self._build_basic_knowledge()
    
    def _build_basic_knowledge(self):
        """Build basic endgame principles"""
        knowledge = {
            'kpk': self._handle_kpk,  # King and Pawn vs King
            'krk': self._handle_krk,  # King and Rook vs King
            'kqk': self._handle_kqk,  # King and Queen vs King
            'kbnk': self._handle_kbnk,  # King, Bishop and Knight vs King
        }
        return knowledge
    
    def _handle_kpk(self, board):
        """Basic King and Pawn vs King endgame"""
        # Get kings and pawns
        white_king = board.king(chess.WHITE)
        black_king = board.king(chess.BLACK)
        white_pawns = list(board.pieces(chess.PAWN, chess.WHITE))
        black_pawns = list(board.pieces(chess.PAWN, chess.BLACK))
        
        if white_pawns:
            pawn_square = white_pawns[0]
            pawn_color = chess.WHITE
        elif black_pawns:
            pawn_square = black_pawns[0]
            pawn_color = chess.BLACK
        else:
            return None
            
        pawn_file = chess.square_file(pawn_square)
        pawn_rank = chess.square_rank(pawn_square)
        
        # Try to advance pawn or support with king
        legal_moves = list(board.legal_moves)
        good_moves = []
        
        for move in legal_moves:
            score = 0
            
            # Pawn advancement is good
            if move.from_square == pawn_square:
                if pawn_color == chess.WHITE:
                    if chess.square_rank(move.to_square) > pawn_rank:
                        score += 10
                else:
                    if chess.square_rank(move.to_square) < pawn_rank:
                        score += 10
            
            # King opposition is good
            piece = board.piece_at(move.from_square)
            if piece and piece.piece_type == chess.KING:
                # Move king closer to pawn or opponent king
                if piece.color == chess.WHITE:
                    if white_pawns:
                        distance_to_pawn = self._distance(move.to_square, pawn_square)
                        score += (8 - distance_to_pawn) * 2
                    distance_to_opp_king = self._distance(move.to_square, black_king)
                    score += (8 - distance_to_opp_king)
                else:
                    if black_pawns:
                        distance_to_pawn = self._distance(move.to_square, pawn_square)
                        score += distance_to_pawn * 3  # Black wants to block pawn
            
            # Promotion is very good
            if getattr(move, 'promotion', None) and move.promotion != chess.PAWN:
                score += 100
            
            if score > 0:
                good_moves.append((score, move))
        
        if good_moves:
            # Sort by score only, don't compare moves
            good_moves.sort(key=lambda x: x[0], reverse=True)
            return good_moves[0][1]
        
        return random.choice(legal_moves) if legal_moves else None
    
    def _handle_krk(self, board):
        """Basic King and Rook vs King endgame - checkmate patterns"""
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None
        
        # Look for checks and moves that restrict the king
        checking_moves = []
        restricting_moves = []
        
        for move in legal_moves:
            board.push(move)
            
            # Checks are good
            if board.is_check():
                checking_moves.append(move)
            
            # Moves that limit king's mobility
            opponent_king = board.king(not board.turn)
            if opponent_king:
                mobility = len([m for m in board.legal_moves if board.piece_at(m.from_square) and board.piece_at(m.from_square).color != board.turn])
                if mobility < 3:  # King is restricted
                    restricting_moves.append((mobility, move))
            
            board.pop()
        
        if checking_moves:
            return random.choice(checking_moves)
        
        if restricting_moves:
            # Sort by mobility only
            restricting_moves.sort(key=lambda x: x[0])
            return restricting_moves[0][1]
        
        return random.choice(legal_moves)
    
    def _handle_kqk(self, board):
        """King and Queen vs King - easy checkmate"""
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None
        
        # Look for checks
        checking_moves = []
        for move in legal_moves:
            board.push(move)
            if board.is_check():
                checking_moves.append(move)
            board.pop()
        
        if checking_moves:
            return random.choice(checking_moves)
        
        return random.choice(legal_moves)
    
    def _handle_kbnk(self, board):
        """King, Bishop and Knight vs King - difficult checkmate"""
        # Just play reasonable moves
        return self._general_endgame_move(board)
    
    def _distance(self, square1, square2):
        """Calculate Chebyshev distance between two squares"""
        rank1, file1 = chess.square_rank(square1), chess.square_file(square1)
        rank2, file2 = chess.square_rank(square2), chess.square_file(square2)
        return max(abs(rank1 - rank2), abs(file1 - file2))
    
    def get_basic_endgame_move(self, board):
        """Get a move based on basic endgame principles"""
        piece_count = chess.popcount(board.occupied)
        
        if piece_count > 10:  # Too many pieces for simple endgame
            return None
        
        # Get material composition
        white_pieces = self._get_material(board, chess.WHITE)
        black_pieces = self._get_material(board, chess.BLACK)
        
        # Try to match with known endgame types
        endgame_type = self._classify_endgame(white_pieces, black_pieces)
        
        if endgame_type in self.knowledge:
            move = self.knowledge[endgame_type](board)
            if move:
                return move
        
        # Fallback: use general endgame principles
        return self._general_endgame_move(board)
    
    def _get_material(self, board, color):
        """Get material count by piece type"""
        pieces = {}
        for piece_type in [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
            count = len(list(board.pieces(piece_type, color)))
            if count > 0:
                pieces[piece_type] = count
        return pieces
    
    def _classify_endgame(self, white_pieces, black_pieces):
        """Classify the endgame type based on material"""
        # Simple classification - you can expand this
        white_count = sum(white_pieces.values())
        black_count = sum(black_pieces.values())
        
        if white_count == 2 and chess.PAWN in white_pieces and black_count == 1:
            return 'kpk'
        elif white_count == 2 and chess.ROOK in white_pieces and black_count == 1:
            return 'krk'
        elif white_count == 2 and chess.QUEEN in white_pieces and black_count == 1:
            return 'kqk'
        elif white_count == 3 and (chess.BISHOP in white_pieces or chess.KNIGHT in white_pieces) and black_count == 1:
            return 'kbnk'
        
        return 'unknown'
    
    def _general_endgame_move(self, board):
        """General endgame principles"""
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None
        
        scored_moves = []
        
        for move in legal_moves:
            score = 0
            
            # Promotion is excellent
            if getattr(move, 'promotion', None) and move.promotion != chess.PAWN:
                score += 1000
            
            # Pawn advancement in endgame is good
            piece = board.piece_at(move.from_square)
            if piece and piece.piece_type == chess.PAWN:
                direction = 1 if piece.color == chess.WHITE else -1
                advance = (chess.square_rank(move.to_square) - chess.square_rank(move.from_square)) * direction
                if advance > 0:
                    score += 20 + advance * 5  # Further advances are better
            
            # King centralization in endgame
            if piece and piece.piece_type == chess.KING:
                to_rank = chess.square_rank(move.to_square)
                to_file = chess.square_file(move.to_square)
                center_distance = abs(to_rank - 3.5) + abs(to_file - 3.5)
                score += (7 - center_distance) * 3
            
            # Checks are good in endgames
            board.push(move)
            if board.is_check():
                score += 15
            board.pop()
            
            # Captures can be good
            if board.is_capture(move):
                captured_piece = board.piece_at(move.to_square)
                if captured_piece:
                    # Value pieces: Queen=9, Rook=5, Bishop/Knight=3, Pawn=1
                    piece_values = {
                        chess.QUEEN: 9,
                        chess.ROOK: 5,
                        chess.BISHOP: 3,
                        chess.KNIGHT: 3,
                        chess.PAWN: 1
                    }
                    score += piece_values.get(captured_piece.piece_type, 0) * 10
            
            scored_moves.append((score, move))
        
        # Sort by score only, don't compare moves
        if scored_moves:
            scored_moves.sort(key=lambda x: x[0], reverse=True)
            return scored_moves[0][1]
        
        return random.choice(legal_moves)


class EndgameEngine:
    """Main endgame engine with fallback to basic knowledge"""
    
    def __init__(self, tablebase_path=None):
        self.basic_endgame = BasicEndgame()
        self.tablebase_available = False
        self.tablebase = None
        
        # Try to initialize Syzygy tablebases if path provided
        if tablebase_path and os.path.exists(tablebase_path):
            try:
                import chess.syzygy
                self.tablebase = chess.syzygy.Tablebase()
                self.tablebase.add_directory(tablebase_path)
                self.tablebase_available = True
                print("Syzygy tablebases loaded successfully")
                
                # Determine max pieces supported
                self.max_pieces = self._get_max_pieces()
                print(f"Tablebases support up to {self.max_pieces} pieces")
                
            except Exception as e:
                print(f"Failed to load Syzygy tablebases: {e}")
                self.tablebase_available = False
        else:
            print("Tablebase path not available, using basic endgame knowledge")
    
    def _get_max_pieces(self):
        """Determine the maximum number of pieces supported by the tablebases"""
        if not self.tablebase_available:
            return 0
            
        # Check common tablebase configurations
        for pieces in [7, 6, 5, 4, 3]:
            try:
                # Create a simple position with the given number of pieces
                board = chess.Board()
                board.clear()
                
                # Add kings (required)
                board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
                board.set_piece_at(chess.E8, chess.Piece(chess.KING, chess.BLACK))
                
                # Add some pieces to reach the target count
                piece_count = 2  # Already have 2 kings
                squares = [sq for sq in chess.SQUARES if sq not in [chess.E1, chess.E8]]
                
                for i in range(min(pieces - 2, len(squares))):
                    board.set_piece_at(squares[i], chess.Piece(chess.QUEEN, chess.WHITE))
                    piece_count += 1
                    if piece_count >= pieces:
                        break
                
                # Try to probe this position
                self.tablebase.probe_wdl(board)
                return pieces
            except chess.syzygy.MissingTableError:
                continue
            except:
                continue
        
        return 0
    
    def is_endgame(self, board):
        """Check if position is an endgame (few pieces)"""
        piece_count = chess.popcount(board.occupied)
        
        # Use tablebases if we have them and position has few enough pieces
        if self.tablebase_available:
            return piece_count <= self.max_pieces
        
        # Otherwise, use basic endgame definition
        return piece_count <= 10
    
    def get_best_move(self, board):
        """Get the best endgame move"""
        if not self.is_endgame(board):
            return None
        
        # Try tablebases first if available
        if self.tablebase_available:
            try:
                move = self._get_tablebase_move(board)
                if move:
                    print("Using tablebase move")
                    return move
            except Exception as e:
                print(f"Tablebase error: {e}")
        
        # Fallback to basic endgame knowledge
        print("Using basic endgame knowledge")
        return self.basic_endgame.get_basic_endgame_move(board)
    
    def _get_tablebase_move(self, board):
        """Try to get move from tablebases"""
        try:
            legal_moves = list(board.legal_moves)
            
            if not legal_moves:
                return None
            
            # If we're in check, we need to be careful
            if board.is_check():
                best_moves = []
                for move in legal_moves:
                    board.push(move)
                    try:
                        # Try to get WDL (Win/Draw/Loss) score
                        wdl = self.tablebase.probe_wdl(board)
                        # Positive WDL is good for the moving side (the one who just moved)
                        # Since we pushed the move, we need to consider from opponent's perspective
                        if wdl > 0:  # Winning for the side that just moved (opponent)
                            board.pop()
                            continue  # This is bad for us
                        best_moves.append(move)
                    except:
                        best_moves.append(move)
                    finally:
                        board.pop()
                
                if best_moves:
                    return random.choice(best_moves)
                return random.choice(legal_moves)
            
            # Not in check - try to find best move using tablebases
            best_wdl = -2  # -2 is worst possible (loss)
            best_moves = []
            
            for move in legal_moves:
                board.push(move)
                try:
                    wdl = self.tablebase.probe_wdl(board)
                    # We want moves that maximize WDL from our perspective
                    # Since we pushed the move, wdl is from opponent's perspective
                    # So we invert the value
                    our_wdl = -wdl
                    
                    if our_wdl > best_wdl:
                        best_wdl = our_wdl
                        best_moves = [move]
                    elif our_wdl == best_wdl:
                        best_moves.append(move)
                except:
                    # If we can't probe this position, consider it neutral
                    if 0 > best_wdl:
                        best_wdl = 0
                        best_moves = [move]
                    elif 0 == best_wdl:
                        best_moves.append(move)
                finally:
                    board.pop()
            
            if best_moves:
                return random.choice(best_moves)
            
        except Exception as e:
            print(f"Tablebase probing error: {e}")
        
        return None
    
    def get_tablebase_evaluation(self, board):
        """
        Get tablebase evaluation of the current position.
        Returns a string describing the position outcome.
        """
        if not self.tablebase_available or not self.is_endgame(board):
            return "Unknown"
        
        try:
            wdl = self.tablebase.probe_wdl(board)
            if wdl > 0:
                return "Win for White" if board.turn == chess.WHITE else "Win for Black"
            elif wdl < 0:
                return "Loss for White" if board.turn == chess.WHITE else "Loss for Black"
            else:
                return "Draw"
        except:
            return "Unknown"


# For testing
if __name__ == "__main__":
    # Test basic endgame knowledge
    engine = EndgameEngine()
    board = chess.Board("8/8/8/8/8/k7/8/K7 w - - 0 1")  # K vs K
    print(f"Is endgame: {engine.is_endgame(board)}")
    print(f"Best move: {engine.get_best_move(board)}")
    
    # Test KPK endgame
    board = chess.Board("8/8/8/8/8/k1P5/8/K7 w - - 0 1")  # KPK
    print(f"KPK position - Best move: {engine.get_best_move(board)}")