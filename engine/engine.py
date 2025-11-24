import time
import chess
from typing import Tuple, Optional
from collections import defaultdict

from position_evaluator import ChessPositionEvaluator

class EnhancedChessEngine:
    def __init__(self):
        self.evaluator = ChessPositionEvaluator()
        self.nodes_searched = 0
        self.best_move_found = None
        self.transposition_table = {}
        
        # Killer moves: store two killer moves per depth
        self.killer_moves = defaultdict(list)
        
        # History heuristic: track moves that caused cutoffs
        self.history_table = {}
        
        # Principal variation
        self.pv_table = {}
        
        # Move ordering scores
        self.MVV_LVA = {
            chess.PAWN: 100,
            chess.KNIGHT: 320,
            chess.BISHOP: 330,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 20000
        }
    
    def clear_tables(self):
        """Clear search tables for new game"""
        self.killer_moves.clear()
        self.history_table.clear()
        self.pv_table.clear()
        self.transposition_table.clear()
    
    def get_best_move(self, board: chess.Board, max_time: float = None) -> chess.Move:
        """Main entry point to get best move"""
        current_eval = self.evaluator.evaluate_position(board)
        is_white = board.turn
        
        if not is_white:
            current_eval = -current_eval
        
        # Adaptive time control
        if max_time is None:
            if current_eval < -300:
                max_time = 15.0  # Losing badly - think longer
            elif current_eval < -150:
                max_time = 12.0
            elif current_eval < 150:
                max_time = 10.0
            else:
                max_time = 8.0  # Winning - move faster
        
        return self.iterative_deepening_search(board, max_time)
    
    def iterative_deepening_search(self, board: chess.Board, max_time: float) -> chess.Move:
        """Iterative deepening with aspiration windows"""
        start_time = time.time()
        self.best_move_found = None
        self.nodes_searched = 0
        
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None
        
        self.best_move_found = legal_moves[0]
        best_eval = 0
        
        # Aspiration window parameters
        window_size = 50
        
        for depth in range(1, 50):
            elapsed = time.time() - start_time
            
            if elapsed >= max_time * 0.90:
                break
            
            # Set aspiration window around previous eval
            alpha = best_eval - window_size
            beta = best_eval + window_size
            
            try:
                # Try search with narrow window
                eval_score, move = self.pvs_root(
                    board, depth, alpha, beta, start_time, max_time
                )
                
                # If we failed high or low, research with full window
                if eval_score <= alpha or eval_score >= beta:
                    eval_score, move = self.pvs_root(
                        board, depth, float('-inf'), float('inf'), 
                        start_time, max_time
                    )
                
                if move is not None:
                    self.best_move_found = move
                    best_eval = eval_score
                    
                    elapsed = time.time() - start_time
                    print(f"Depth {depth}: Eval={eval_score:+.2f}, "
                          f"Move={move}, Nodes={self.nodes_searched}, "
                          f"Time={elapsed:.2f}s, NPS={int(self.nodes_searched/elapsed) if elapsed > 0 else 0}")
                
                # Mate found
                if abs(eval_score) > 9000:
                    print(f"Found forced mate! Eval: {eval_score}")
                    break
                    
            except TimeoutError:
                print(f"Search stopped at depth {depth} due to time limit")
                break
        
        total_time = time.time() - start_time
        nps = int(self.nodes_searched / total_time) if total_time > 0 else 0
        print(f"Final move: {self.best_move_found}, Total nodes: {self.nodes_searched}, "
              f"Time: {total_time:.2f}s, NPS: {nps}")
        
        return self.best_move_found
    
    def pvs_root(self, board: chess.Board, depth: int, alpha: float, beta: float, 
                 start_time: float, max_time: float) -> Tuple[float, Optional[chess.Move]]:
        """Principal Variation Search at root"""
        best_move = None
        best_value = float('-inf')
        
        moves = self.order_moves(board, list(board.legal_moves), depth)
        
        for idx, move in enumerate(moves):
            if time.time() - start_time >= max_time * 0.90:
                raise TimeoutError()
            
            board.push(move)
            try:
                if idx == 0:
                    # Full window search for first move
                    value = -self.pvs(board, depth - 1, -beta, -alpha, start_time, max_time, depth)
                else:
                    # Null window search for other moves
                    value = -self.pvs(board, depth - 1, -alpha - 1, -alpha, start_time, max_time, depth)
                    
                    # Re-search if it's better than alpha
                    if alpha < value < beta:
                        value = -self.pvs(board, depth - 1, -beta, -alpha, start_time, max_time, depth)
            finally:
                board.pop()
            
            if value > best_value:
                best_value = value
                best_move = move
            
            alpha = max(alpha, value)
            if alpha >= beta:
                # Beta cutoff - update killer moves
                self.update_killers(move, depth)
                break
        
        return best_value, best_move
    
    def pvs(self, board: chess.Board, depth: int, alpha: float, beta: float,
            start_time: float, max_time: float, ply: int) -> float:
        """Principal Variation Search"""
        self.nodes_searched += 1
        
        # Time check
        if self.nodes_searched % 2048 == 0:
            if time.time() - start_time >= max_time * 0.90:
                raise TimeoutError()
        
        # Check transposition table
        board_key = board.fen()
        if board_key in self.transposition_table:
            entry_depth, entry_value, entry_flag = self.transposition_table[board_key]
            if entry_depth >= depth:
                if entry_flag == 'exact':
                    return entry_value
                elif entry_flag == 'lowerbound' and entry_value >= beta:
                    return entry_value
                elif entry_flag == 'upperbound' and entry_value <= alpha:
                    return entry_value
        
        # Terminal conditions
        if depth <= 0 or board.is_game_over():
            return self.quiescence_search(board, alpha, beta, start_time, max_time)
        
        # Null move pruning (if not in check and depth > 2)
        if depth >= 3 and not board.is_check():
            board.push(chess.Move.null())
            try:
                null_score = -self.pvs(board, depth - 3, -beta, -beta + 1, start_time, max_time, ply + 1)
            finally:
                board.pop()
            
            if null_score >= beta:
                return beta  # Null move cutoff
        
        max_value = float('-inf')
        moves = self.order_moves(board, list(board.legal_moves), ply)
        
        flag = 'upperbound'
        best_move = None
        
        for idx, move in enumerate(moves):
            board.push(move)
            try:
                if idx == 0:
                    # Full window search
                    value = -self.pvs(board, depth - 1, -beta, -alpha, start_time, max_time, ply + 1)
                else:
                    # Late Move Reduction (LMR)
                    reduction = 0
                    if (depth >= 3 and idx >= 4 and 
                        not board.is_capture(move) and 
                        not board.is_check() and 
                        move.promotion is None):
                        reduction = 1
                    
                    # Null window search with reduction
                    value = -self.pvs(board, depth - 1 - reduction, -alpha - 1, -alpha, 
                                     start_time, max_time, ply + 1)
                    
                    # Re-search if necessary
                    if alpha < value < beta:
                        value = -self.pvs(board, depth - 1, -beta, -alpha, 
                                        start_time, max_time, ply + 1)
            finally:
                board.pop()
            
            if value > max_value:
                max_value = value
                best_move = move
            
            alpha = max(alpha, value)
            
            if alpha >= beta:
                # Beta cutoff
                if not board.is_capture(move):
                    self.update_killers(move, ply)
                    self.update_history(move, depth)
                flag = 'lowerbound'
                break
        
        if max_value > alpha:
            flag = 'exact'
        
        # Store in transposition table
        self.transposition_table[board_key] = (depth, max_value, flag)
        
        return max_value
    
    def quiescence_search(self, board: chess.Board, alpha: float, beta: float,
                         start_time: float, max_time: float, depth: int = 0) -> float:
        """Quiescence search to avoid horizon effect"""
        self.nodes_searched += 1
        
        stand_pat = self.evaluator.evaluate_position(board)
        
        if depth > 6:  # Limit quiescence depth
            return stand_pat
        
        if stand_pat >= beta:
            return beta
        
        if alpha < stand_pat:
            alpha = stand_pat
        
        # Generate tactical moves
        tactical_moves = []
        for move in board.legal_moves:
            if board.is_capture(move) or move.promotion or board.gives_check(move):
                tactical_moves.append(move)
        
        if not tactical_moves:
            return stand_pat
        
        # Delta pruning - skip moves that can't possibly improve position
        BIG_DELTA = 975  # Queen value
        if stand_pat < alpha - BIG_DELTA:
            return alpha
        
        tactical_moves = self.order_moves(board, tactical_moves, 0, quiesce=True)
        
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
    
    def update_killers(self, move: chess.Move, ply: int):
        """Update killer move table"""
        if ply not in self.killer_moves:
            self.killer_moves[ply] = []
        
        killers = self.killer_moves[ply]
        
        if move not in killers:
            killers.insert(0, move)
            if len(killers) > 2:
                killers.pop()
    
    def update_history(self, move: chess.Move, depth: int):
        """Update history heuristic"""
        move_key = (move.from_square, move.to_square)
        if move_key not in self.history_table:
            self.history_table[move_key] = 0
        self.history_table[move_key] += depth * depth
    
    def order_moves(self, board: chess.Board, moves: list, ply: int = 0, quiesce: bool = False) -> list:
        """Advanced move ordering with multiple heuristics"""
        def move_score(move):
            score = 0
            
            # PV move (from transposition table)
            board_key = board.fen()
            if board_key in self.pv_table and self.pv_table[board_key] == move:
                score += 10000
            
            # Captures (MVV-LVA)
            if board.is_capture(move):
                victim = board.piece_at(move.to_square)
                attacker = board.piece_at(move.from_square)
                
                if victim and attacker:
                    victim_value = self.MVV_LVA.get(victim.piece_type, 0)
                    attacker_value = self.MVV_LVA.get(attacker.piece_type, 0)
                    score += (victim_value * 10 - attacker_value) + 8000
            
            # Promotions
            if move.promotion:
                score += 7000
            
            # Killer moves
            if not quiesce and ply in self.killer_moves:
                if move in self.killer_moves[ply]:
                    score += 5000
            
            # History heuristic
            move_key = (move.from_square, move.to_square)
            if move_key in self.history_table:
                score += min(self.history_table[move_key], 4000)
            
            # Checks
            board.push(move)
            if board.is_check():
                score += 500
            board.pop()
            
            # Center control
            to_file = chess.square_file(move.to_square)
            to_rank = chess.square_rank(move.to_square)
            if 2 <= to_file <= 5 and 2 <= to_rank <= 5:
                score += 20
            
            return score
        
        return sorted(moves, key=move_score, reverse=True)


# Keep backward compatibility
def return_bestMove_and_bestValue(board: chess.Board, depth: int = 3) -> chess.Move:
    """Legacy function for compatibility"""
    engine = EnhancedChessEngine()
    max_time = min(depth * 3, 15.0)
    
    try:
        return engine.get_best_move(board, max_time)
    except:
        legal_moves = list(board.legal_moves)
        return legal_moves[0] if legal_moves else None