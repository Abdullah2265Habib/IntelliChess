import time
import random
import chess
from typing import Tuple, Optional

from position_evaluator import ChessPositionEvaluator

class ChessEngine:
    def __init__(self):
        self.evaluator = ChessPositionEvaluator()
        self.nodes_searched = 0
        self.best_move_found = None
        self.transposition_table = {}
        
        # Move ordering scores
        self.MVV_LVA = {
            chess.PAWN: 100,
            chess.KNIGHT: 300,
            chess.BISHOP: 300,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 0
        }
    
    def get_best_move(self, board: chess.Board, max_time: float = None) -> chess.Move:
        current_eval = self.evaluator.evaluate_position(board)
        is_white = board.turn
        
        if not is_white:
            current_eval = -current_eval
        
        if max_time is None:
            if current_eval < -200:  
                max_time = random.uniform(30, 40)
                print("Position is losing! Thinking deeply...")
            elif current_eval < -100:  
                max_time = random.uniform(20, 30)
                print("Position is difficult. Calculating carefully...")
            elif current_eval < 100:
                max_time = random.uniform(5, 15)
            else:
                max_time = random.uniform(3, 8)
                print("Position is winning. Quick move...")
        
        return self.iterative_deepening_search(board, max_time)
    
    def iterative_deepening_search(self, board: chess.Board, max_time: float) -> chess.Move:

        start_time = time.time()
        self.best_move_found = None
        self.nodes_searched = 0
        self.transposition_table.clear()
        
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None
        
        self.best_move_found = legal_moves[0]
        best_eval = float('-inf')
        
        for depth in range(1, 50):
            elapsed = time.time() - start_time
            
            if elapsed >= max_time * 0.95:  
                break
            
            try:
                eval_score, move = self.alpha_beta_root(
                    board, 
                    depth, 
                    float('-inf'), 
                    float('inf'),
                    start_time,
                    max_time
                )
                
                if move is not None:
                    self.best_move_found = move
                    best_eval = eval_score
                    
                    elapsed = time.time() - start_time
                    print(f"Depth {depth}: Eval={eval_score:+.2f}, "
                          f"Move={move}, Nodes={self.nodes_searched}, "
                          f"Time={elapsed:.2f}s")
                
                if abs(eval_score) > 9000:
                    print(f"Found forced mate! Eval: {eval_score}")
                    break
                    
            except TimeoutError:
                print(f"Search stopped at depth {depth} due to time limit")
                break
        
        total_time = time.time() - start_time
        print(f"Final move: {self.best_move_found}, Total nodes: {self.nodes_searched}, "
              f"Time: {total_time:.2f}s")
        
        return self.best_move_found
    
    def alpha_beta_root(self, board: chess.Board, depth: int, alpha: float, beta: float, start_time: float, max_time: float) -> Tuple[float, Optional[chess.Move]]:

        best_move = None
        best_value = float('-inf')

        moves = self.order_moves(board, list(board.legal_moves))
        
        for move in moves:

            if time.time() - start_time >= max_time * 0.95:
                raise TimeoutError()
            
            board.push(move)
            try:
                value = -self.alpha_beta(board, depth - 1, -beta, -alpha, start_time, max_time)
            finally:
                board.pop()
            
            if value > best_value:
                best_value = value
                best_move = move
            
            alpha = max(alpha, value)
            if alpha >= beta:
                break  
        
        return best_value, best_move
    
    def alpha_beta(self, board: chess.Board, depth: int, alpha: float, beta: float, start_time: float, max_time: float) -> float:

        self.nodes_searched += 1
        

        if self.nodes_searched % 1000 == 0:
            if time.time() - start_time >= max_time * 0.95:
                raise TimeoutError()
        

        board_key = board.fen()
        if board_key in self.transposition_table:
            entry_depth, entry_value = self.transposition_table[board_key]
            if entry_depth >= depth:
                return entry_value

        if depth == 0 or board.is_game_over():
            eval_score = self.quiescence_search(board, alpha, beta, start_time, max_time)
            return eval_score
        
        max_value = float('-inf')
        moves = self.order_moves(board, list(board.legal_moves))
        
        for move in moves:
            board.push(move)
            try:
                value = -self.alpha_beta(board, depth - 1, -beta, -alpha, start_time, max_time)
            finally:
                board.pop()
            
            max_value = max(max_value, value)
            alpha = max(alpha, value)
            
            if alpha >= beta:
                break  
        self.transposition_table[board_key] = (depth, max_value)
        
        return max_value
    
    def quiescence_search(self, board: chess.Board, alpha: float, beta: float,
                         start_time: float, max_time: float, depth: int = 0) -> float:

        self.nodes_searched += 1
        

        stand_pat = self.evaluator.evaluate_position(board)
        
        if depth > 4:  #limit quiescence depth
            return stand_pat
        
        if stand_pat >= beta:
            return beta
        
        if alpha < stand_pat:
            alpha = stand_pat
 
        tactical_moves = []
        for move in board.legal_moves:
            if board.is_capture(move) or move.promotion or board.gives_check(move):
                tactical_moves.append(move)
        
        if not tactical_moves:
            return stand_pat
        

        tactical_moves = self.order_moves(board, tactical_moves)
        
        for move in tactical_moves:
            board.push(move)
            try:
                score = -self.quiescence_search(board, -beta, -alpha, start_time, max_time, depth + 1)
            finally:
                board.pop()
            
            if score >= beta:
                return beta
            
            if score > alpha:
                alpha = score
        
        return alpha
    
    def order_moves(self, board: chess.Board, moves: list) -> list:

        def move_score(move):
            score = 0
            
            #captures (MVV-LVA)
            if board.is_capture(move):
                victim = board.piece_at(move.to_square)
                attacker = board.piece_at(move.from_square)
                
                if victim and attacker:
                    victim_value = self.MVV_LVA.get(victim.piece_type, 0)
                    attacker_value = self.MVV_LVA.get(attacker.piece_type, 0)
                    score += (victim_value * 10 - attacker_value)
            

            if move.promotion:
                score += 800
            

            board.push(move)
            if board.is_check():
                score += 50
            board.pop()
            

            to_file = chess.square_file(move.to_square)
            to_rank = chess.square_rank(move.to_square)
            if 2 <= to_file <= 5 and 2 <= to_rank <= 5:
                score += 10
            
            return score
        
        return sorted(moves, key=move_score, reverse=True)


def get_bot_move(board, opening_book=None, endgame_engine=None, max_time=10.0, search_depth=3):
    piece_values = {
        chess.PAWN: 100,
        chess.KNIGHT: 320,
        chess.BISHOP: 330,
        chess.ROOK: 500,
        chess.QUEEN: 900,
        chess.KING: 20000,
    }

    def material_score(b):
        s = 0
        for sq in chess.SQUARES:
            p = b.piece_at(sq)
            if p:
                v = piece_values.get(p.piece_type, 0)
                s += v if p.color == chess.WHITE else -v

        return s

    def generate_captures(b):
        return [m for m in b.legal_moves if b.is_capture(m)]

    def mvv_lva_key(b, move):
        victim = b.piece_at(move.to_square)
        v_val = 0 if victim is None else piece_values.get(victim.piece_type, 0)
        attacker = b.piece_at(move.from_square)
        a_val = 0 if attacker is None else piece_values.get(attacker.piece_type, 0)

        return (v_val * 1000) - a_val

    def quiescence(b, alpha, beta, start, time_limit, depth_left):
        stand_pat = material_score(b)
        if stand_pat >= beta:
            return stand_pat
        if alpha < stand_pat:
            alpha = stand_pat

        if depth_left <= 0 or (time.time() - start) > time_limit:
            return stand_pat

        caps = generate_captures(b)
        if not caps:
            return stand_pat

        caps.sort(key=lambda mv: mvv_lva_key(b, mv), reverse=True)

        for mv in caps:
            if (time.time() - start) > time_limit:
                break
            b.push(mv)
            try:
                score = -quiescence(b, -beta, -alpha, start, time_limit, depth_left - 1)
            finally:
                b.pop()
            if score >= beta:
                return score
            if score > alpha:
                alpha = score
        return alpha


    start_time = time.time()
    end_time = start_time + max_time
    best_move = None
    best_score = -10**9

    legal = list(board.legal_moves)
    if not legal:
        return None


    legal.sort(key=lambda mv: (1 if board.is_capture(mv) else 0, mvv_lva_key(board, mv)), reverse=True)


    for depth in range(1, search_depth + 1):
        if time.time() >= end_time:
            break
        for mv in legal:
            if time.time() >= end_time:
                break
            board.push(mv)
            try:
                score = -quiescence(board, -10**9, 10**9, start_time, max_time, depth_left=depth)
            finally:
                board.pop()
            if score is None:
                continue
            if score > best_score:
                best_score = score
                best_move = mv

        if best_move:
            legal.sort(key=lambda m: 0 if m == best_move else 1)


    while time.time() < end_time:
        for mv in legal:
            if time.time() >= end_time:
                break
            board.push(mv)
            try:
                score = -quiescence(board, -10**9, 10**9, start_time, max_time, depth_left=search_depth)
            finally:
                board.pop()
            if score is None:
                continue
            if score > best_score:
                best_score = score
                best_move = mv

        if time.time() < end_time:
            time.sleep(0.01)


    if best_move is None:
        best_score = -10**9
        for mv in legal:
            board.push(mv)
            try:
                score = -material_score(board)
            finally:
                board.pop()
            if score > best_score:
                best_score = score
                best_move = mv

    if best_move is None and legal:
        best_move = random.choice(legal)

    return best_move



def return_bestMove_and_bestValue(board: chess.Board, depth: int = 3) -> chess.Move:
    engine = ChessEngine()
    
    max_time = depth * 2
    
    try:
        return engine.get_best_move(board, max_time)
    except:
        legal_moves = list(board.legal_moves)
        return random.choice(legal_moves) if legal_moves else None


if __name__ == "__main__":

    print("Testing Chess Engine with Alpha-Beta Pruning\n")
    
    engine = ChessEngine()
    
    # Test position 1: Starting position
    board = chess.Board()
    print("Test 1: Starting position")
    move = engine.get_best_move(board, max_time=5)
    print(f"Best move: {move}\n")
    
    # Test position 2: Tactical position
    board = chess.Board("r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4")
    print("Test 2: Italian Game position")
    move = engine.get_best_move(board, max_time=8)
    print(f"Best move: {move}\n")
    
    # Test position 3: Endgame
    board = chess.Board("8/8/8/8/8/4k3/8/4K2R w - - 0 1")
    print("Test 3: King and Rook endgame")
    move = engine.get_best_move(board, max_time=5)
    print(f"Best move: {move}\n")