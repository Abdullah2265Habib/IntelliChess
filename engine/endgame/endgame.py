# [file name]: engine/endgame/endgame.py
import chess
import random
import os
from collections import defaultdict

class BasicEndgame:
    def __init__(self):
        self.knowledge = self._build_basic_knowledge()
    
    def _build_basic_knowledge(self):
        knowledge = {
            'kpk': self._handle_kpk,
            'krk': self._handle_krk,
            'kqk': self._handle_kqk,
            'kbnk': self._handle_kbnk,  
        }
        return knowledge
    
    def _handle_kpk(self, board):
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
        
        legal_moves = list(board.legal_moves)
        good_moves = []
        
        for move in legal_moves:
            score = 0
            
            if move.from_square == pawn_square:
                if pawn_color == chess.WHITE:
                    if chess.square_rank(move.to_square) > pawn_rank:
                        score += 10
                else:
                    if chess.square_rank(move.to_square) < pawn_rank:
                        score += 10

            piece = board.piece_at(move.from_square)
            if piece and piece.piece_type == chess.KING:
                if piece.color == chess.WHITE:
                    if white_pawns:
                        distance_to_pawn = self._distance(move.to_square, pawn_square)
                        score += (8 - distance_to_pawn) * 2
                    distance_to_opp_king = self._distance(move.to_square, black_king)
                    score += (8 - distance_to_opp_king)
                else:
                    if black_pawns:
                        distance_to_pawn = self._distance(move.to_square, pawn_square)
                        score += distance_to_pawn * 3
            
            if move.promotion and move.promotion != chess.PAWN:
                score += 100
            
            if score > 0:
                good_moves.append((score, move))
        
        if good_moves:
            good_moves.sort(key=lambda x: x[0], reverse=True)
            return good_moves[0][1]
        
        return random.choice(legal_moves) if legal_moves else None
    
    def _handle_krk(self, board):
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None
        
        checking_moves = []
        restricting_moves = []
        
        for move in legal_moves:
            temp_board = board.copy()
            temp_board.push(move)
            
            if temp_board.is_check():
                checking_moves.append(move)
            
            opponent_king = temp_board.king(not board.turn)
            if opponent_king:
                mobility = len([m for m in temp_board.legal_moves 
                              if temp_board.piece_at(m.from_square) 
                              and temp_board.piece_at(m.from_square).color != board.turn])
                if mobility < 3:
                    restricting_moves.append((mobility, move))
        
        if checking_moves:
            return random.choice(checking_moves)
        
        if restricting_moves:
            restricting_moves.sort(key=lambda x: x[0])
            return restricting_moves[0][1]
        
        return random.choice(legal_moves)
    
    def _handle_kqk(self, board):
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None
        
        checking_moves = []
        for move in legal_moves:
            temp_board = board.copy()
            temp_board.push(move)
            if temp_board.is_check():
                checking_moves.append(move)
        
        if checking_moves:
            return random.choice(checking_moves)
        
        return random.choice(legal_moves)
    
    def _handle_kbnk(self, board):
        return self._general_endgame_move(board)
    
    def _distance(self, square1, square2):
        #calculating chebyshev distance between two squares
        rank1, file1 = chess.square_rank(square1), chess.square_file(square1)
        rank2, file2 = chess.square_rank(square2), chess.square_file(square2)
        return max(abs(rank1 - rank2), abs(file1 - file2))
    
    def get_basic_endgame_move(self, board):
        piece_count = chess.popcount(board.occupied)
        
        if piece_count > 10:
            return None
        
        white_pieces = self._get_material(board, chess.WHITE)
        black_pieces = self._get_material(board, chess.BLACK)
        
        endgame_type = self._classify_endgame(white_pieces, black_pieces)
        
        if endgame_type in self.knowledge:
            move = self.knowledge[endgame_type](board)
            if move:
                return move
        
        return self._general_endgame_move(board)
    
    def _get_material(self, board, color):
        pieces = {}
        for piece_type in [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
            count = len(list(board.pieces(piece_type, color)))
            if count > 0:
                pieces[piece_type] = count
        return pieces
    
    def _classify_endgame(self, white_pieces, black_pieces):
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
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None
        
        scored_moves = []
        
        for move in legal_moves:
            score = 0
            
            #promotion is excellent
            if move.promotion and move.promotion != chess.PAWN:
                score += 1000
            
            #pawn advancement in endgame is good
            piece = board.piece_at(move.from_square)
            if piece and piece.piece_type == chess.PAWN:
                direction = 1 if piece.color == chess.WHITE else -1
                advance = (chess.square_rank(move.to_square) - chess.square_rank(move.from_square)) * direction
                if advance > 0:
                    score += 20 + advance * 5
            
            #king centralization in endgame
            if piece and piece.piece_type == chess.KING:
                to_rank = chess.square_rank(move.to_square)
                to_file = chess.square_file(move.to_square)
                center_distance = abs(to_rank - 3.5) + abs(to_file - 3.5)
                score += (7 - center_distance) * 3
            #checks are good in endgames
            temp_board = board.copy()
            temp_board.push(move)
            if temp_board.is_check():
                score += 15
            #captures can be good
            if board.is_capture(move):
                captured_piece = board.piece_at(move.to_square)
                if captured_piece:
                    piece_values = {
                        chess.QUEEN: 9,
                        chess.ROOK: 5,
                        chess.BISHOP: 3,
                        chess.KNIGHT: 3,
                        chess.PAWN: 1
                    }
                    score += piece_values.get(captured_piece.piece_type, 0) * 10
            
            scored_moves.append((score, move))

        if scored_moves:
            scored_moves.sort(key=lambda x: x[0], reverse=True)
            return scored_moves[0][1]
        
        return random.choice(legal_moves)


class EndgameEngine:
    def __init__(self, tablebase_path=None):
        self.basic_endgame = BasicEndgame()
        self.tablebase_available = False
        self.tablebase = None
        self.max_pieces = 0

        if tablebase_path and os.path.exists(tablebase_path):
            try:
                import chess.syzygy
                self.tablebase = chess.syzygy.Tablebase()

                self.tablebase.add_directory(tablebase_path)
                self.tablebase_available = True
                print(f"Syzygy tablebases loaded from: {tablebase_path}")
                
                self.max_pieces = self._get_max_pieces()
                print(f"Tablebases support up to {self.max_pieces} pieces")
                
            except ImportError:
                print("unknown.")
                self.tablebase_available = False
            except Exception as e:
                print(f"failed to load Syzygy tablebases: {e}")
                self.tablebase_available = False
        else:
            if tablebase_path:
                print(f"tablebase path does not exist: {tablebase_path}")
            print("using basic endgame knowledge only")
    
    def _get_max_pieces(self):
        if not self.tablebase_available:
            return 0
        
        for pieces in [7, 6, 5, 4, 3]:
            try:
                board = chess.Board()
                board.clear()

                board.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
                board.set_piece_at(chess.E8, chess.Piece(chess.KING, chess.BLACK))
                
                piece_count = 2
                squares = [chess.A2, chess.B2, chess.C2, chess.D2, chess.F2]
                
                for i in range(min(pieces - 2, len(squares))):
                    board.set_piece_at(squares[i], chess.Piece(chess.PAWN, chess.WHITE))
                    piece_count += 1
                    if piece_count >= pieces:
                        break
                
                board.turn = chess.WHITE
                
                wdl = self.tablebase.probe_wdl(board)
                print(f"probed {pieces}-piece position")
                return pieces
                
            except Exception as e:
                continue
        
        return 0
    
    def is_endgame(self, board):
        piece_count = chess.popcount(board.occupied)
        
        if self.tablebase_available and self.max_pieces > 0:
            return piece_count <= self.max_pieces
        
        return piece_count <= 10
    
    def get_best_move(self, board):
        if not self.is_endgame(board):
            return None
        
        if self.tablebase_available and self.max_pieces > 0:
            piece_count = chess.popcount(board.occupied)
            if piece_count <= self.max_pieces:
                try:
                    move = self._get_tablebase_move(board)
                    if move:
                        print("using tablebase move")
                        return move
                except Exception as e:
                    print(f"tablebase error: {e}")
        
        print("using basic endgame knowledge")
        return self.basic_endgame.get_basic_endgame_move(board)
    
    def _get_tablebase_move(self, board):
        try:
            legal_moves = list(board.legal_moves)
            if not legal_moves:
                return None
            
            #store move evaluations
            move_scores = []
            
            for move in legal_moves:
                #create a copy of the board to avoid corrupting the original
                temp_board = board.copy()
                temp_board.push(move)
                
                try:
                    #[robe the position after the move
                    wdl = self.tablebase.probe_wdl(temp_board)
                    
                    #DTZ (Distance to Zero) gives us the number of moves to zeroing position
                    #i prefer moves with better WDL and lower DTZ
                    try:
                        dtz = self.tablebase.probe_dtz(temp_board)
                    except:
                        dtz = 0
                    
                    #WDL from opponent's perspective, so negate it for our perspective
                    #WDL: 2=win,1=cursed win,0=draw,-1=blessed loss,-2=loss
                    our_wdl = -wdl
                    
                    #score: prioritize WDL,then use DTZ as tiebreaker
                    #for winning positions,prefer moves that win faster => (lower DTZ)
                    #for losing positions,prefer moves that delay loss => (higher DTZ)
                    if our_wdl > 0:
                        score = (our_wdl * 10000) - abs(dtz)
                    elif our_wdl < 0:
                        score = (our_wdl * 10000) + abs(dtz)
                    else:
                        score = 0
                    
                    move_scores.append((score, move))
                    
                except Exception as e:
                    #if we cant probe, treat as neutral
                    move_scores.append((0, move))
            
            if move_scores:
                move_scores.sort(key=lambda x: x[0], reverse=True)
                best_score = move_scores[0][0]
                
                best_moves = [move for score, move in move_scores if score == best_score]

                return random.choice(best_moves)
            
        except Exception as e:
            print(f"tablebase probing error: {e}")
            import traceback
            traceback.print_exc()
        
        return None
    
    def get_tablebase_evaluation(self, board):
        if not self.tablebase_available or not self.is_endgame(board):
            return "Unknown"
        
        piece_count = chess.popcount(board.occupied)
        if piece_count > self.max_pieces:
            return "Unknown"
        
        try:
            wdl = self.tablebase.probe_wdl(board)
            
            #WDL is from the perspective of the side to move
            #2=win,1=cursed win,0=draw,-1=blessed loss,-2=loss
            if wdl == 2:
                return f"win for {'White' if board.turn == chess.WHITE else 'Black'}"
            elif wdl == 1:
                return f"cursed Win for {'White' if board.turn == chess.WHITE else 'Black'}"
            elif wdl == 0:
                return "draw"
            elif wdl == -1:
                return f"blessed Loss for {'White' if board.turn == chess.WHITE else 'Black'}"
            elif wdl == -2:
                return f"loss for {'White' if board.turn == chess.WHITE else 'Black'}"
            else:
                return "unknown"
                
        except Exception as e:
            return "unknown"


# For testing
if __name__ == "__main__":

    print("testing endgame engine")

    engine = EndgameEngine()
    board = chess.Board("8/8/8/8/8/k7/P7/K7 w - - 0 1")  # KPK
    print(f"\nKPK Position: {board.fen()}")
    print(f"is in endgame: {engine.is_endgame(board)}")
    print(f"best move: {engine.get_best_move(board)}")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    tablebase_path = os.path.join(script_dir, "..", "tablebases", "syzygy")
    tablebase_path = os.path.normpath(tablebase_path)
    
    print(f"\nlooking for tablebases at: {tablebase_path}")
    
    if os.path.exists(tablebase_path):
        print(f"tablebases found!")
        engine_with_tb = EndgameEngine(tablebase_path=tablebase_path)
        
        if engine_with_tb.tablebase_available:
            board = chess.Board("8/8/8/8/8/k7/P7/K7 w - - 0 1")
            print(f"\nKPK Position: {board.fen()}")
            print(f"Evaluation: {engine_with_tb.get_tablebase_evaluation(board)}")
            print(f"Best move: {engine_with_tb.get_best_move(board)}")
        else:
            print("Tablebases failed to load")
    else:
        print(f"tablebase path not found: {tablebase_path}")