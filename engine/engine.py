import time
import math
import chess
import chess.polyglot
from typing import Tuple, Optional
from collections import defaultdict

from position_evaluator import ChessPositionEvaluator

# --- Constants ---
MATE_SCORE = 9999
MAX_PLY = 64
TT_SIZE = 1 << 20  # ~1M entries

# Transposition table entry flags
TT_EXACT = 0
TT_LOWERBOUND = 1
TT_UPPERBOUND = 2

# Precompute LMR reduction table
LMR_TABLE = [[0] * 64 for _ in range(64)]
for d in range(1, 64):
    for m in range(1, 64):
        LMR_TABLE[d][m] = max(0, int(0.75 + math.log(d) * math.log(m) / 2.25))


class TranspositionTable:
    """Fixed-size transposition table with depth-preferred replacement."""
    __slots__ = ('table', 'mask')

    def __init__(self, size=TT_SIZE):
        self.mask = size - 1
        self.table = [None] * size

    def probe(self, key):
        entry = self.table[key & self.mask]
        if entry is not None and entry[0] == key:
            return entry  # (key, depth, score, flag, best_move)
        return None

    def store(self, key, depth, score, flag, best_move):
        idx = key & self.mask
        old = self.table[idx]
        # Always replace if: empty, same position, or new depth >= old depth
        if old is None or old[0] == key or depth >= old[1]:
            self.table[idx] = (key, depth, score, flag, best_move)

    def clear(self):
        for i in range(len(self.table)):
            self.table[i] = None


class EnhancedChessEngine:
    def __init__(self):
        self.evaluator = ChessPositionEvaluator()
        self.nodes_searched = 0
        self.best_move_found = None
        self.tt = TranspositionTable()

        # Killer moves: store two killer moves per ply
        self.killers = [[None, None] for _ in range(MAX_PLY)]

        # History heuristic: [color][from_sq][to_sq]
        self.history = [[[0] * 64 for _ in range(64)] for _ in range(2)]

        # Counter move heuristic
        self.counter_moves = [[None] * 64 for _ in range(64)]

        # MVV-LVA scores for capture ordering
        self._mvv_lva = {}
        victim_scores = {
            chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
            chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 20
        }
        attacker_scores = {
            chess.PAWN: 6, chess.KNIGHT: 5, chess.BISHOP: 4,
            chess.ROOK: 3, chess.QUEEN: 2, chess.KING: 1
        }
        for vt, vs in victim_scores.items():
            for at, a_s in attacker_scores.items():
                self._mvv_lva[(vt, at)] = vs * 10 + a_s

        # Previous move for counter-move heuristic
        self._prev_move = None

    def clear_tables(self):
        """Clear search tables for new game."""
        self.tt.clear()
        self.killers = [[None, None] for _ in range(MAX_PLY)]
        self.history = [[[0] * 64 for _ in range(64)] for _ in range(2)]
        self.counter_moves = [[None] * 64 for _ in range(64)]

    def get_best_move(self, board: chess.Board, max_time: float = None) -> chess.Move:
        """Main entry point to get best move."""
        if max_time is None:
            max_time = 10.0

        return self.iterative_deepening_search(board, max_time)

    def iterative_deepening_search(self, board: chess.Board, max_time: float) -> chess.Move:
        """Iterative deepening with aspiration windows."""
        start_time = time.time()
        self.best_move_found = None
        self.nodes_searched = 0
        self._start_time = start_time
        self._max_time = max_time
        self._stop = False

        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None
        if len(legal_moves) == 1:
            return legal_moves[0]

        self.best_move_found = legal_moves[0]
        best_eval = 0

        for depth in range(1, MAX_PLY):
            if self._stop or (time.time() - start_time) >= max_time * 0.5:
                break

            # Aspiration windows
            if depth >= 5:
                delta = 25
                alpha = best_eval - delta
                beta = best_eval + delta

                while True:
                    try:
                        score = self._search_root(board, depth, alpha, beta)
                    except TimeoutError:
                        self._stop = True
                        break

                    if score <= alpha:
                        alpha = max(alpha - delta, -MATE_SCORE)
                        delta *= 2
                    elif score >= beta:
                        beta = min(beta + delta, MATE_SCORE)
                        delta *= 2
                    else:
                        best_eval = score
                        break

                    if delta > 500:
                        try:
                            score = self._search_root(board, depth, -MATE_SCORE, MATE_SCORE)
                            best_eval = score
                        except TimeoutError:
                            self._stop = True
                        break
            else:
                try:
                    score = self._search_root(board, depth, -MATE_SCORE, MATE_SCORE)
                    best_eval = score
                except TimeoutError:
                    self._stop = True
                    break

            if self._stop:
                break

            elapsed = time.time() - start_time
            nps = int(self.nodes_searched / elapsed) if elapsed > 0 else 0
            print(f"Depth {depth}: Eval={best_eval:+.2f}, "
                  f"Move={self.best_move_found}, Nodes={self.nodes_searched}, "
                  f"Time={elapsed:.2f}s, NPS={nps}")

            # Stop if mate found
            if abs(best_eval) > MATE_SCORE - MAX_PLY:
                print(f"Found forced mate! Eval: {best_eval}")
                break

        total_time = time.time() - start_time
        nps = int(self.nodes_searched / total_time) if total_time > 0 else 0
        print(f"Final move: {self.best_move_found}, Total nodes: {self.nodes_searched}, "
              f"Time: {total_time:.2f}s, NPS: {nps}")

        return self.best_move_found

    def _check_time(self):
        """Periodically check if time is up."""
        if self.nodes_searched & 4095 == 0:
            if time.time() - self._start_time >= self._max_time * 0.90:
                self._stop = True
                raise TimeoutError()

    def _search_root(self, board: chess.Board, depth: int, alpha: float, beta: float) -> float:
        """Search at root level with full move ordering."""
        best_move = None
        best_value = -MATE_SCORE
        old_alpha = alpha

        moves = self._order_moves_root(board, depth)

        for idx, move in enumerate(moves):
            board.push(move)
            try:
                if idx == 0:
                    value = -self._pvs(board, depth - 1, -beta, -alpha, 1, True)
                else:
                    # LMR at root
                    reduction = 0
                    if (depth >= 3 and idx >= 3 and
                            not board.is_check() and
                            not move.promotion and
                            not board.is_capture(move)):
                        reduction = LMR_TABLE[min(depth, 63)][min(idx, 63)]
                        reduction = max(0, reduction - 1)  # Less aggressive at root

                    value = -self._pvs(board, depth - 1 - reduction, -alpha - 1, -alpha, 1, True)

                    if value > alpha and (reduction > 0 or value < beta):
                        value = -self._pvs(board, depth - 1, -beta, -alpha, 1, True)
            finally:
                board.pop()

            if self._stop:
                break

            if value > best_value:
                best_value = value
                best_move = move
                self.best_move_found = move

            if value > alpha:
                alpha = value

            if alpha >= beta:
                if not board.is_capture(move):
                    self._update_killers(move, 0)
                    self._update_history(board.turn, move, depth)
                break

        # Store in TT
        if not self._stop and best_move is not None:
            key = chess.polyglot.zobrist_hash(board)
            if best_value <= old_alpha:
                flag = TT_UPPERBOUND
            elif best_value >= beta:
                flag = TT_LOWERBOUND
            else:
                flag = TT_EXACT
            self.tt.store(key, depth, best_value, flag, best_move)

        return best_value

    def _pvs(self, board: chess.Board, depth: int, alpha: float, beta: float,
             ply: int, pv_node: bool) -> float:
        """Principal Variation Search with all pruning techniques."""
        self.nodes_searched += 1
        self._check_time()

        is_check = board.is_check()

        # Check extension
        if is_check:
            depth += 1

        # Mate distance pruning
        mating_value = MATE_SCORE - ply
        if mating_value < beta:
            beta = mating_value
            if alpha >= mating_value:
                return mating_value
        mating_value = -MATE_SCORE + ply
        if mating_value > alpha:
            alpha = mating_value
            if beta <= mating_value:
                return mating_value

        # Terminal / depth 0
        if depth <= 0:
            return self._quiescence(board, alpha, beta, ply, 0)

        if board.is_game_over():
            if board.is_checkmate():
                return -MATE_SCORE + ply
            return 0  # stalemate / draw

        # Repetition / 50-move draw
        if board.is_repetition(2) or board.can_claim_fifty_moves():
            return 0

        # --- Transposition Table probe ---
        key = chess.polyglot.zobrist_hash(board)
        tt_move = None
        entry = self.tt.probe(key)
        if entry is not None:
            _, tt_depth, tt_score, tt_flag, tt_best = entry
            tt_move = tt_best

            if tt_depth >= depth and not pv_node:
                if tt_flag == TT_EXACT:
                    return tt_score
                elif tt_flag == TT_LOWERBOUND and tt_score >= beta:
                    return tt_score
                elif tt_flag == TT_UPPERBOUND and tt_score <= alpha:
                    return tt_score

        # --- Static eval for pruning decisions ---
        static_eval = self.evaluator.evaluate_position(board)
        if not board.turn:
            static_eval = -static_eval

        # --- Reverse Futility Pruning (Static Null Move Pruning) ---
        if (not pv_node and not is_check and depth <= 7 and
                abs(beta) < MATE_SCORE - MAX_PLY):
            margin = 80 * depth
            if static_eval - margin >= beta:
                return static_eval - margin

        # --- Null Move Pruning ---
        if (not pv_node and not is_check and depth >= 3 and
                static_eval >= beta and
                # Don't do NMP in positions with only pawns
                (board.occupied_co[board.turn] &
                 ~board.pawns & ~board.kings)):
            R = 3 + depth // 4 + min((static_eval - beta) // 200, 3)
            R = min(R, depth - 1)

            board.push(chess.Move.null())
            try:
                null_score = -self._pvs(board, depth - R - 1, -beta, -beta + 1,
                                        ply + 1, False)
            finally:
                board.pop()

            if null_score >= beta:
                if abs(null_score) >= MATE_SCORE - MAX_PLY:
                    return beta
                return null_score

        # --- Internal Iterative Deepening ---
        if tt_move is None and depth >= 4 and pv_node:
            self._pvs(board, depth - 2, alpha, beta, ply, True)
            entry = self.tt.probe(key)
            if entry is not None:
                tt_move = entry[4]

        # --- Move loop ---
        best_value = -MATE_SCORE
        best_move = None
        old_alpha = alpha
        moves_searched = 0

        moves = self._order_moves(board, tt_move, ply)

        for move in moves:
            is_capture = board.is_capture(move)
            is_promotion = move.promotion is not None

            # --- Futility Pruning ---
            if (not pv_node and not is_check and depth <= 3 and
                    moves_searched > 0 and not is_capture and
                    not is_promotion and
                    abs(alpha) < MATE_SCORE - MAX_PLY):
                futility_margin = static_eval + 100 * depth
                if futility_margin <= alpha:
                    continue

            # --- Late Move Pruning ---
            if (not pv_node and not is_check and depth <= 3 and
                    moves_searched >= 3 + depth * depth and
                    not is_capture and not is_promotion):
                continue

            board.push(move)
            gives_check = board.is_check()

            try:
                if moves_searched == 0:
                    value = -self._pvs(board, depth - 1, -beta, -alpha,
                                       ply + 1, pv_node)
                else:
                    # LMR
                    reduction = 0
                    if (depth >= 3 and moves_searched >= 2 and
                            not is_capture and not is_promotion and
                            not gives_check):
                        reduction = LMR_TABLE[min(depth, 63)][min(moves_searched, 63)]

                        # Reduce less in PV nodes
                        if pv_node:
                            reduction = max(0, reduction - 1)

                        # Reduce less for killer moves
                        if (move == self.killers[ply][0] or
                                move == self.killers[ply][1]):
                            reduction = max(0, reduction - 1)

                        # Don't reduce into qsearch
                        reduction = min(reduction, depth - 2)
                        reduction = max(0, reduction)

                    # Null window search with reduction
                    value = -self._pvs(board, depth - 1 - reduction,
                                       -alpha - 1, -alpha, ply + 1, False)

                    # Re-search without reduction if LMR failed high
                    if value > alpha and reduction > 0:
                        value = -self._pvs(board, depth - 1,
                                           -alpha - 1, -alpha, ply + 1, False)

                    # Full re-search if PV node and still better
                    if value > alpha and value < beta:
                        value = -self._pvs(board, depth - 1, -beta, -alpha,
                                           ply + 1, True)
            finally:
                board.pop()

            moves_searched += 1

            if self._stop:
                return 0

            if value > best_value:
                best_value = value
                best_move = move

            if value > alpha:
                alpha = value

            if alpha >= beta:
                # Update quiet move heuristics
                if not is_capture:
                    self._update_killers(move, ply)
                    self._update_history(board.turn, move, depth)
                    # Counter move
                    if self._prev_move:
                        self.counter_moves[self._prev_move.from_square][self._prev_move.to_square] = move
                break

        # Checkmate or stalemate
        if moves_searched == 0:
            if is_check:
                return -MATE_SCORE + ply
            return 0

        # Store in TT
        if not self._stop:
            if best_value <= old_alpha:
                flag = TT_UPPERBOUND
            elif best_value >= beta:
                flag = TT_LOWERBOUND
            else:
                flag = TT_EXACT
            self.tt.store(key, depth, best_value, flag, best_move)

        self._prev_move = best_move
        return best_value

    def _quiescence(self, board: chess.Board, alpha: float, beta: float,
                    ply: int, q_depth: int) -> float:
        """Quiescence search — captures and promotions only."""
        self.nodes_searched += 1

        if q_depth > 8:
            eval_score = self.evaluator.evaluate_position(board)
            return eval_score if board.turn == chess.WHITE else -eval_score

        if board.is_checkmate():
            return -MATE_SCORE + ply
        if board.is_stalemate() or board.is_insufficient_material():
            return 0

        stand_pat = self.evaluator.evaluate_position(board)
        if not board.turn:
            stand_pat = -stand_pat

        if stand_pat >= beta:
            return beta

        # Delta pruning
        BIG_DELTA = 975
        if stand_pat < alpha - BIG_DELTA:
            return alpha

        if stand_pat > alpha:
            alpha = stand_pat

        # Generate only tactical moves (captures + promotions)
        tactical_moves = []
        for move in board.legal_moves:
            if board.is_capture(move) or move.promotion:
                tactical_moves.append(move)

        if not tactical_moves:
            return stand_pat

        # Order captures by MVV-LVA
        tactical_moves.sort(key=lambda m: self._capture_score(board, m), reverse=True)

        for move in tactical_moves:
            # SEE pruning: skip obviously bad captures
            if board.is_capture(move) and not move.promotion:
                if self._see_sign(board, move) < 0:
                    continue

            board.push(move)
            try:
                score = -self._quiescence(board, -beta, -alpha, ply + 1, q_depth + 1)
            finally:
                board.pop()

            if score >= beta:
                return beta
            if score > alpha:
                alpha = score

        return alpha

    def _see_sign(self, board, move):
        """Simplified Static Exchange Evaluation — returns positive if capture is likely good."""
        piece_values = {
            chess.PAWN: 100, chess.KNIGHT: 325, chess.BISHOP: 335,
            chess.ROOK: 500, chess.QUEEN: 975, chess.KING: 20000
        }

        # Value of captured piece
        captured = board.piece_at(move.to_square)
        if captured is None:
            # En passant
            if board.is_en_passant(move):
                return 0  # pawn takes pawn, roughly equal
            return 0

        attacker = board.piece_at(move.from_square)
        if attacker is None:
            return 0

        # If we capture something more valuable, it's likely good
        captured_val = piece_values.get(captured.piece_type, 0)
        attacker_val = piece_values.get(attacker.piece_type, 0)

        # If capturing with a less valuable piece, it's definitely good
        if captured_val >= attacker_val:
            return 1

        # Check if the destination square is defended
        defenders = board.attackers(not board.turn, move.to_square)
        if not defenders:
            return 1  # No defenders = free capture

        # Simple heuristic: gain = captured - attacker (if recaptured)
        return captured_val - attacker_val

    # --- Move Ordering ---

    def _capture_score(self, board, move):
        """Score a capture for ordering (MVV-LVA)."""
        victim = board.piece_at(move.to_square)
        attacker = board.piece_at(move.from_square)
        if victim and attacker:
            return self._mvv_lva.get((victim.piece_type, attacker.piece_type), 0)
        if move.promotion:
            return 60 + (move.promotion or 0)
        return 0

    def _order_moves_root(self, board, depth):
        """Order moves at root level."""
        tt_move = None
        entry = self.tt.probe(chess.polyglot.zobrist_hash(board))
        if entry is not None:
            tt_move = entry[4]

        moves = list(board.legal_moves)
        scored = []
        for move in moves:
            score = 0
            if tt_move and move == tt_move:
                score = 100000
            elif board.is_capture(move):
                score = 50000 + self._capture_score(board, move)
            elif move.promotion:
                score = 45000
            else:
                color_idx = 1 if board.turn else 0
                score = self.history[color_idx][move.from_square][move.to_square]
            scored.append((score, move))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in scored]

    def _order_moves(self, board, tt_move, ply):
        """Order moves using TT move, captures (MVV-LVA), killers, counter, history."""
        moves = list(board.legal_moves)
        scored = []
        ply_idx = min(ply, MAX_PLY - 1)
        color_idx = 1 if board.turn else 0

        counter = None
        if self._prev_move:
            counter = self.counter_moves[self._prev_move.from_square][self._prev_move.to_square]

        for move in moves:
            score = 0

            if tt_move and move == tt_move:
                score = 100000
            elif board.is_capture(move):
                score = 50000 + self._capture_score(board, move)
            elif move.promotion:
                score = 45000
            elif move == self.killers[ply_idx][0]:
                score = 40000
            elif move == self.killers[ply_idx][1]:
                score = 39000
            elif counter and move == counter:
                score = 38000
            else:
                score = self.history[color_idx][move.from_square][move.to_square]

            scored.append((score, move))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in scored]

    def _update_killers(self, move, ply):
        """Update killer moves at given ply."""
        ply_idx = min(ply, MAX_PLY - 1)
        if move != self.killers[ply_idx][0]:
            self.killers[ply_idx][1] = self.killers[ply_idx][0]
            self.killers[ply_idx][0] = move

    def _update_history(self, color, move, depth):
        """Update history heuristic with depth-squared bonus."""
        color_idx = 1 if color else 0
        bonus = depth * depth
        val = self.history[color_idx][move.from_square][move.to_square]
        # History gravity: prevent overflow
        self.history[color_idx][move.from_square][move.to_square] = min(val + bonus, 16384)


# Keep backward compatibility
def return_bestMove_and_bestValue(board: chess.Board, depth: int = 3) -> chess.Move:
    """Legacy function for compatibility."""
    engine = EnhancedChessEngine()
    max_time = min(depth * 3, 15.0)

    try:
        return engine.get_best_move(board, max_time)
    except:
        legal_moves = list(board.legal_moves)
        return legal_moves[0] if legal_moves else None