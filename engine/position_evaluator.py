import chess

class ChessPositionEvaluator:
    """
    High-performance tapered evaluation function.
    Uses game-phase interpolation between middlegame and endgame scores,
    well-tuned piece-square tables (CPW/Simplified Eval style),
    and efficient incremental-friendly evaluation terms.
    """

    # Phase weights for tapered eval (total phase = 24)
    PHASE_WEIGHTS = {
        chess.PAWN: 0,
        chess.KNIGHT: 1,
        chess.BISHOP: 1,
        chess.ROOK: 2,
        chess.QUEEN: 4,
        chess.KING: 0,
    }
    TOTAL_PHASE = 24  # 4*1 (knights) + 4*1 (bishops) + 4*2 (rooks) + 2*4 (queens)

    # Material values [middlegame, endgame]
    PIECE_VALUES_MG = {
        chess.PAWN: 100, chess.KNIGHT: 325, chess.BISHOP: 335,
        chess.ROOK: 500, chess.QUEEN: 975, chess.KING: 0,
    }
    PIECE_VALUES_EG = {
        chess.PAWN: 120, chess.KNIGHT: 305, chess.BISHOP: 330,
        chess.ROOK: 530, chess.QUEEN: 1000, chess.KING: 0,
    }

    # ---- AGGRESSION KNOB -------------------------------------------------
    # Global multiplier applied to every "attacking" evaluation term
    # (enemy-king attacks, piece threats, pawn storms, tropism).
    # 1.0 = balanced, 2.0 = reckless. Tuned hot for an attacking style.
    AGGRESSION = 1.8

    # How much each attacker type contributes to the king-attack pressure
    # when it bears on a square in the enemy king's ring.
    KING_ATTACK_WEIGHT = {
        chess.PAWN: 1,
        chess.KNIGHT: 2,
        chess.BISHOP: 2,
        chess.ROOK: 3,
        chess.QUEEN: 5,
    }

    def __init__(self):
        # Build flattened PSTs for fast lookup: PST[piece_type] = (mg[64], eg[64])
        # Tables are from White's perspective, index = square (a1=0, h8=63)
        self._build_pst()

    def _build_pst(self):
        """Build piece-square tables. Tables defined rank8..rank1 (visual order),
        then flipped to square-index order for White."""

        # --- Pawns ---
        pawn_mg = [
             0,  0,  0,  0,  0,  0,  0,  0,
             5, 10, 10,-20,-20, 10, 10,  5,
             5, -5,-10,  0,  0,-10, -5,  5,
             0,  0,  0, 20, 20,  0,  0,  0,
             5,  5, 10, 25, 25, 10,  5,  5,
            10, 10, 20, 30, 30, 20, 10, 10,
            50, 50, 50, 50, 50, 50, 50, 50,
             0,  0,  0,  0,  0,  0,  0,  0,
        ]
        pawn_eg = [
             0,  0,  0,  0,  0,  0,  0,  0,
            10, 10, 10, 10, 10, 10, 10, 10,
            10, 10, 10, 10, 10, 10, 10, 10,
            20, 20, 20, 20, 20, 20, 20, 20,
            30, 30, 30, 30, 30, 30, 30, 30,
            50, 50, 50, 50, 50, 50, 50, 50,
            80, 80, 80, 80, 80, 80, 80, 80,
             0,  0,  0,  0,  0,  0,  0,  0,
        ]

        # --- Knights ---
        knight_mg = [
            -50,-40,-30,-30,-30,-30,-40,-50,
            -40,-20,  0,  5,  5,  0,-20,-40,
            -30,  0, 10, 15, 15, 10,  0,-30,
            -30,  5, 15, 20, 20, 15,  5,-30,
            -30,  0, 15, 20, 20, 15,  0,-30,
            -30,  5, 10, 15, 15, 10,  5,-30,
            -40,-20,  0,  0,  0,  0,-20,-40,
            -50,-40,-30,-30,-30,-30,-40,-50,
        ]
        knight_eg = [
            -50,-40,-30,-30,-30,-30,-40,-50,
            -40,-20,  0,  0,  0,  0,-20,-40,
            -30,  0, 10, 15, 15, 10,  0,-30,
            -30,  5, 15, 20, 20, 15,  5,-30,
            -30,  5, 15, 20, 20, 15,  5,-30,
            -30,  0, 10, 15, 15, 10,  0,-30,
            -40,-20,  0,  0,  0,  0,-20,-40,
            -50,-40,-30,-30,-30,-30,-40,-50,
        ]

        # --- Bishops ---
        bishop_mg = [
            -20,-10,-10,-10,-10,-10,-10,-20,
            -10,  5,  0,  0,  0,  0,  5,-10,
            -10, 10, 10, 10, 10, 10, 10,-10,
            -10,  0, 10, 10, 10, 10,  0,-10,
            -10,  5,  5, 10, 10,  5,  5,-10,
            -10,  0,  5, 10, 10,  5,  0,-10,
            -10,  0,  0,  0,  0,  0,  0,-10,
            -20,-10,-10,-10,-10,-10,-10,-20,
        ]
        bishop_eg = [
            -20,-10,-10,-10,-10,-10,-10,-20,
            -10,  0,  0,  0,  0,  0,  0,-10,
            -10,  0,  5,  5,  5,  5,  0,-10,
            -10,  0,  5, 10, 10,  5,  0,-10,
            -10,  0,  5, 10, 10,  5,  0,-10,
            -10,  0,  5,  5,  5,  5,  0,-10,
            -10,  0,  0,  0,  0,  0,  0,-10,
            -20,-10,-10,-10,-10,-10,-10,-20,
        ]

        # --- Rooks ---
        rook_mg = [
             0,  0,  0,  5,  5,  0,  0,  0,
            -5,  0,  0,  0,  0,  0,  0, -5,
            -5,  0,  0,  0,  0,  0,  0, -5,
            -5,  0,  0,  0,  0,  0,  0, -5,
            -5,  0,  0,  0,  0,  0,  0, -5,
            -5,  0,  0,  0,  0,  0,  0, -5,
             5, 10, 10, 10, 10, 10, 10,  5,
             0,  0,  0,  0,  0,  0,  0,  0,
        ]
        rook_eg = [
             0,  0,  0,  0,  0,  0,  0,  0,
             0,  0,  0,  0,  0,  0,  0,  0,
             0,  0,  0,  0,  0,  0,  0,  0,
             0,  0,  0,  0,  0,  0,  0,  0,
             0,  0,  0,  0,  0,  0,  0,  0,
             0,  0,  0,  0,  0,  0,  0,  0,
             0,  0,  0,  0,  0,  0,  0,  0,
             0,  0,  0,  0,  0,  0,  0,  0,
        ]

        # --- Queen ---
        queen_mg = [
            -20,-10,-10, -5, -5,-10,-10,-20,
            -10,  0,  5,  0,  0,  0,  0,-10,
            -10,  5,  5,  5,  5,  5,  0,-10,
              0,  0,  5,  5,  5,  5,  0, -5,
             -5,  0,  5,  5,  5,  5,  0, -5,
            -10,  0,  5,  5,  5,  5,  0,-10,
            -10,  0,  0,  0,  0,  0,  0,-10,
            -20,-10,-10, -5, -5,-10,-10,-20,
        ]
        queen_eg = [
            -20,-10,-10, -5, -5,-10,-10,-20,
            -10,  0,  0,  0,  0,  0,  0,-10,
            -10,  0,  5,  5,  5,  5,  0,-10,
             -5,  0,  5,  5,  5,  5,  0, -5,
             -5,  0,  5,  5,  5,  5,  0, -5,
            -10,  0,  5,  5,  5,  5,  0,-10,
            -10,  0,  0,  0,  0,  0,  0,-10,
            -20,-10,-10, -5, -5,-10,-10,-20,
        ]

        # --- King ---
        king_mg = [
             20, 30, 10,  0,  0, 10, 30, 20,
             20, 20,  0,  0,  0,  0, 20, 20,
            -10,-20,-20,-20,-20,-20,-20,-10,
            -20,-30,-30,-40,-40,-30,-30,-20,
            -30,-40,-40,-50,-50,-40,-40,-30,
            -30,-40,-40,-50,-50,-40,-40,-30,
            -30,-40,-40,-50,-50,-40,-40,-30,
            -30,-40,-40,-50,-50,-40,-40,-30,
        ]
        king_eg = [
            -50,-30,-30,-30,-30,-30,-30,-50,
            -30,-30,  0,  0,  0,  0,-30,-30,
            -30,-10, 20, 30, 30, 20,-10,-30,
            -30,-10, 30, 40, 40, 30,-10,-30,
            -30,-10, 30, 40, 40, 30,-10,-30,
            -30,-10, 20, 30, 30, 20,-10,-30,
            -30,-20,-10,  0,  0,-10,-20,-30,
            -50,-40,-30,-20,-20,-30,-40,-50,
        ]

        # Store as tuples for fast indexing
        # Tables are already in correct square order (a1=index 0)
        self.pst_mg = {
            chess.PAWN: tuple(pawn_mg),
            chess.KNIGHT: tuple(knight_mg),
            chess.BISHOP: tuple(bishop_mg),
            chess.ROOK: tuple(rook_mg),
            chess.QUEEN: tuple(queen_mg),
            chess.KING: tuple(king_mg),
        }
        self.pst_eg = {
            chess.PAWN: tuple(pawn_eg),
            chess.KNIGHT: tuple(knight_eg),
            chess.BISHOP: tuple(bishop_eg),
            chess.ROOK: tuple(rook_eg),
            chess.QUEEN: tuple(queen_eg),
            chess.KING: tuple(king_eg),
        }

        # Pre-compute mirrored square for black (flip rank)
        self._mirror = [chess.square(chess.square_file(sq), 7 - chess.square_rank(sq))
                        for sq in range(64)]

        # Pre-compute file/rank masks for pawn evaluation
        self._file_masks = []
        for f in range(8):
            mask = chess.BB_EMPTY
            for r in range(8):
                mask |= chess.BB_SQUARES[chess.square(f, r)]
            self._file_masks.append(mask)

        # Adjacent file masks
        self._adjacent_files = []
        for f in range(8):
            mask = chess.BB_EMPTY
            if f > 0:
                mask |= self._file_masks[f - 1]
            if f < 7:
                mask |= self._file_masks[f + 1]
            self._adjacent_files.append(mask)

        # Passed pawn masks: squares in front on same + adjacent files
        self._passed_pawn_mask_white = [chess.BB_EMPTY] * 64
        self._passed_pawn_mask_black = [chess.BB_EMPTY] * 64
        for sq in range(64):
            f = chess.square_file(sq)
            r = chess.square_rank(sq)
            w_mask = chess.BB_EMPTY
            b_mask = chess.BB_EMPTY
            for check_f in range(max(0, f - 1), min(8, f + 2)):
                for check_r in range(r + 1, 8):
                    w_mask |= chess.BB_SQUARES[chess.square(check_f, check_r)]
                for check_r in range(0, r):
                    b_mask |= chess.BB_SQUARES[chess.square(check_f, check_r)]
            self._passed_pawn_mask_white[sq] = w_mask
            self._passed_pawn_mask_black[sq] = b_mask

        # King "danger zone": the king square + the 8 squares around it,
        # extended by one extra rank in front of the king (where attacks
        # and pawn storms land). Stored as plain ints for fast masking.
        self._king_zone = [0] * 64
        for sq in range(64):
            f = chess.square_file(sq)
            r = chess.square_rank(sq)
            zone = int(chess.BB_KING_ATTACKS[sq]) | int(chess.BB_SQUARES[sq])
            # extend one rank toward the centre of the board (both ways is fine;
            # this just widens the net a touch so looming attacks register)
            for df in (-1, 0, 1):
                nf = f + df
                if 0 <= nf <= 7:
                    for nr in (r + 2, r - 2):
                        if 0 <= nr <= 7:
                            zone |= int(chess.BB_SQUARES[chess.square(nf, nr)])
            self._king_zone[sq] = zone

        # Chebyshev distance table between any two squares (king tropism).
        self._distance = [[0] * 64 for _ in range(64)]
        for a in range(64):
            af, ar = chess.square_file(a), chess.square_rank(a)
            for b in range(64):
                bf, br = chess.square_file(b), chess.square_rank(b)
                self._distance[a][b] = max(abs(af - bf), abs(ar - br))

    def evaluate_position(self, board):
        """
        Main evaluation: tapered eval with MG/EG interpolation.
        Returns positive for white advantage, negative for black.
        """
        if board.is_checkmate():
            return -9999 if board.turn else 9999

        if board.is_stalemate() or board.is_insufficient_material():
            return 0

        # Also handle other draw conditions
        if board.can_claim_fifty_moves() or board.is_repetition(2):
            return 0

        mg_score = 0
        eg_score = 0
        phase = 0

        white_bishops = 0
        black_bishops = 0

        piece_map = board.piece_map()

        # --- Material + PST ---
        for sq, piece in piece_map.items():
            pt = piece.piece_type
            phase += self.PHASE_WEIGHTS.get(pt, 0)

            if piece.color == chess.WHITE:
                mg_score += self.PIECE_VALUES_MG[pt] + self.pst_mg[pt][sq]
                eg_score += self.PIECE_VALUES_EG[pt] + self.pst_eg[pt][sq]
                if pt == chess.BISHOP:
                    white_bishops += 1
            else:
                msq = self._mirror[sq]
                mg_score -= self.PIECE_VALUES_MG[pt] + self.pst_mg[pt][msq]
                eg_score -= self.PIECE_VALUES_EG[pt] + self.pst_eg[pt][msq]
                if pt == chess.BISHOP:
                    black_bishops += 1

        # --- Bishop pair bonus ---
        if white_bishops >= 2:
            mg_score += 30
            eg_score += 50
        if black_bishops >= 2:
            mg_score -= 30
            eg_score -= 50

        # --- Pawn structure ---
        pawn_mg, pawn_eg = self._evaluate_pawns(board)
        mg_score += pawn_mg
        eg_score += pawn_eg

        # --- Rook bonuses (open/semi-open files, 7th rank) ---
        rook_mg, rook_eg = self._evaluate_rooks(board)
        mg_score += rook_mg
        eg_score += rook_eg

        # --- King safety (middlegame only, lightweight) ---
        king_mg = self._evaluate_king_safety(board)
        mg_score += king_mg

        # --- Activity: mobility + enemy-king attacks + piece threats ---
        act_mg, act_eg = self._evaluate_activity(board)
        mg_score += act_mg
        eg_score += act_eg

        # --- Pawn storms against the enemy king (attacking term) ---
        storm_mg = self._evaluate_pawn_storms(board)
        mg_score += storm_mg

        # --- Tapered eval ---
        phase = min(phase, self.TOTAL_PHASE)
        mg_weight = phase
        eg_weight = self.TOTAL_PHASE - phase

        score = (mg_score * mg_weight + eg_score * eg_weight) // self.TOTAL_PHASE

        # Tempo bonus (small bonus for side to move)
        if board.turn == chess.WHITE:
            score += 10
        else:
            score -= 10

        return score

    def _evaluate_pawns(self, board):
        """Evaluate pawn structure using bitboards for speed."""
        mg = 0
        eg = 0
        white_pawns = board.pieces(chess.PAWN, chess.WHITE)
        black_pawns = board.pieces(chess.PAWN, chess.BLACK)
        white_pawns_mask = int(white_pawns)
        black_pawns_mask = int(black_pawns)

        # White pawns
        for sq in white_pawns:
            f = chess.square_file(sq)
            r = chess.square_rank(sq)

            # Doubled pawns
            pawns_on_file = white_pawns_mask & self._file_masks[f]
            if chess.popcount(pawns_on_file) > 1:
                mg -= 10
                eg -= 20

            # Isolated pawns
            if not (white_pawns_mask & self._adjacent_files[f]):
                mg -= 15
                eg -= 20

            # Passed pawns
            if not (black_pawns_mask & self._passed_pawn_mask_white[sq]):
                bonus = [0, 5, 10, 20, 35, 60, 100, 0][r]
                mg += bonus // 2
                eg += bonus

            # Connected pawns (pawn on adjacent file, same or one rank behind)
            for adj_f in [f - 1, f + 1]:
                if 0 <= adj_f <= 7:
                    for adj_r in [r, r - 1]:
                        if 0 <= adj_r <= 7:
                            adj_sq = chess.square(adj_f, adj_r)
                            if adj_sq in white_pawns:
                                mg += 5
                                eg += 5
                                break

        # Black pawns
        for sq in black_pawns:
            f = chess.square_file(sq)
            r = chess.square_rank(sq)

            pawns_on_file = black_pawns_mask & self._file_masks[f]
            if chess.popcount(pawns_on_file) > 1:
                mg += 10
                eg += 20

            if not (black_pawns_mask & self._adjacent_files[f]):
                mg += 15
                eg += 20

            if not (white_pawns_mask & self._passed_pawn_mask_black[sq]):
                bonus = [0, 100, 60, 35, 20, 10, 5, 0][r]
                mg -= bonus // 2
                eg -= bonus

            for adj_f in [f - 1, f + 1]:
                if 0 <= adj_f <= 7:
                    for adj_r in [r, r + 1]:
                        if 0 <= adj_r <= 7:
                            adj_sq = chess.square(adj_f, adj_r)
                            if adj_sq in black_pawns:
                                mg -= 5
                                eg -= 5
                                break

        return mg, eg

    def _evaluate_rooks(self, board):
        """Evaluate rook placement: open files, semi-open files, 7th rank."""
        mg = 0
        eg = 0
        white_pawns_mask = int(board.pieces(chess.PAWN, chess.WHITE))
        black_pawns_mask = int(board.pieces(chess.PAWN, chess.BLACK))

        for sq in board.pieces(chess.ROOK, chess.WHITE):
            f = chess.square_file(sq)
            r = chess.square_rank(sq)
            file_mask = self._file_masks[f]

            own_pawns_on_file = white_pawns_mask & file_mask
            opp_pawns_on_file = black_pawns_mask & file_mask

            if not own_pawns_on_file and not opp_pawns_on_file:
                mg += 20  # open file
                eg += 15
            elif not own_pawns_on_file:
                mg += 10  # semi-open file
                eg += 8

            if r == 6:  # 7th rank
                mg += 20
                eg += 30

        for sq in board.pieces(chess.ROOK, chess.BLACK):
            f = chess.square_file(sq)
            r = chess.square_rank(sq)
            file_mask = self._file_masks[f]

            own_pawns_on_file = black_pawns_mask & file_mask
            opp_pawns_on_file = white_pawns_mask & file_mask

            if not own_pawns_on_file and not opp_pawns_on_file:
                mg -= 20
                eg -= 15
            elif not own_pawns_on_file:
                mg -= 10
                eg -= 8

            if r == 1:  # 2nd rank (7th from black's perspective)
                mg -= 20
                eg -= 30

        return mg, eg

    def _evaluate_king_safety(self, board):
        """Lightweight king safety for middlegame."""
        score = 0
        white_pawns = board.pieces(chess.PAWN, chess.WHITE)
        black_pawns = board.pieces(chess.PAWN, chess.BLACK)
        white_pawns_mask = int(white_pawns)
        black_pawns_mask = int(black_pawns)

        for color in [chess.WHITE, chess.BLACK]:
            king_sq = board.king(color)
            if king_sq is None:
                continue

            king_file = chess.square_file(king_sq)
            king_rank = chess.square_rank(king_sq)
            sign = 1 if color == chess.WHITE else -1

            # Pawn shield
            shield_bonus = 0
            own_pawns = white_pawns if color == chess.WHITE else black_pawns
            own_pawns_mask = white_pawns_mask if color == chess.WHITE else black_pawns_mask
            shield_rank = king_rank + (1 if color == chess.WHITE else -1)

            if 0 <= shield_rank <= 7:
                for df in [-1, 0, 1]:
                    sf = king_file + df
                    if 0 <= sf <= 7:
                        shield_sq = chess.square(sf, shield_rank)
                        if shield_sq in own_pawns:
                            shield_bonus += 10

            # Penalty for open files near king
            for df in [-1, 0, 1]:
                kf = king_file + df
                if 0 <= kf <= 7:
                    file_mask = self._file_masks[kf]
                    if not (own_pawns_mask & file_mask):
                        shield_bonus -= 15

            score += sign * shield_bonus

        return score

    def _evaluate_activity(self, board):
        """
        Combined piece-activity evaluation in a single attack-mask pass:
          * mobility (space / freedom of each piece)
          * king attack  -> pressure on the squares around the ENEMY king
          * threats       -> attacking more valuable / undefended enemy pieces
          * king tropism  -> rewarding pieces that crowd the enemy king

        The attack-related terms are scaled by AGGRESSION so the engine
        actively hunts the enemy king and plays for the initiative.
        Returns (mg, eg) from White's perspective.
        """
        mg = 0
        eg = 0
        AGG = self.AGGRESSION
        KAW = self.KING_ATTACK_WEIGHT

        wk = board.king(chess.WHITE)
        bk = board.king(chess.BLACK)
        # Zone around the enemy king (what each side is attacking).
        black_zone = self._king_zone[bk] if bk is not None else 0
        white_zone = self._king_zone[wk] if wk is not None else 0

        occ_white = board.occupied_co[chess.WHITE]
        occ_black = board.occupied_co[chess.BLACK]

        # Enemy heavy/minor targets for threat detection.
        bq = int(board.pieces(chess.QUEEN, chess.BLACK))
        br = int(board.pieces(chess.ROOK, chess.BLACK))
        bm = int(board.pieces(chess.KNIGHT, chess.BLACK) | board.pieces(chess.BISHOP, chess.BLACK))
        wq = int(board.pieces(chess.QUEEN, chess.WHITE))
        wr = int(board.pieces(chess.ROOK, chess.WHITE))
        wm = int(board.pieces(chess.KNIGHT, chess.WHITE) | board.pieces(chess.BISHOP, chess.WHITE))

        # King-attack accumulators: (number of attackers, summed pressure).
        w_atk_cnt = w_atk_units = 0   # White pieces attacking the Black king
        b_atk_cnt = b_atk_units = 0   # Black pieces attacking the White king

        # Mobility reference counts per piece type (centre of the scale).
        MOB_BASE = {chess.KNIGHT: 4, chess.BISHOP: 6, chess.ROOK: 7, chess.QUEEN: 14}
        MOB_MG = {chess.KNIGHT: 4, chess.BISHOP: 5, chess.ROOK: 2, chess.QUEEN: 2}
        MOB_EG = {chess.KNIGHT: 4, chess.BISHOP: 3, chess.ROOK: 3, chess.QUEEN: 2}

        for pt in (chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN):
            base = MOB_BASE[pt]
            mmg = MOB_MG[pt]
            meg = MOB_EG[pt]
            w = KAW[pt]

            # ---- White pieces ----
            for sq in board.pieces(pt, chess.WHITE):
                att = int(board.attacks_mask(sq))
                moves = chess.popcount(att & ~occ_white)
                mg += (moves - base) * mmg
                eg += (moves - base) * meg

                z = att & black_zone
                if z:
                    w_atk_cnt += 1
                    w_atk_units += w * chess.popcount(z)

                # Threats on more valuable enemy pieces (undefended-ish bonus).
                if pt in (chess.KNIGHT, chess.BISHOP):
                    if att & bq:
                        mg += int(55 * AGG)
                    if att & br:
                        mg += int(35 * AGG)
                elif pt == chess.ROOK:
                    if att & bq:
                        mg += int(40 * AGG)
                    if att & bm:
                        mg += int(15 * AGG)

                # King tropism: minor/major pieces that sit near the enemy king.
                if bk is not None:
                    d = self._distance[sq][bk]
                    if d <= 3:
                        mg += int((4 - d) * w * AGG)

            # ---- Black pieces ----
            for sq in board.pieces(pt, chess.BLACK):
                att = int(board.attacks_mask(sq))
                moves = chess.popcount(att & ~occ_black)
                mg -= (moves - base) * mmg
                eg -= (moves - base) * meg

                z = att & white_zone
                if z:
                    b_atk_cnt += 1
                    b_atk_units += w * chess.popcount(z)

                if pt in (chess.KNIGHT, chess.BISHOP):
                    if att & wq:
                        mg -= int(55 * AGG)
                    if att & wr:
                        mg -= int(35 * AGG)
                elif pt == chess.ROOK:
                    if att & wq:
                        mg -= int(40 * AGG)
                    if att & wm:
                        mg -= int(15 * AGG)

                if wk is not None:
                    d = self._distance[sq][wk]
                    if d <= 3:
                        mg -= int((4 - d) * w * AGG)

        # ---- Convert accumulated king pressure into a score ----
        # More attackers => sharply rising danger (sacrifices become worth it).
        if w_atk_cnt >= 2:
            mg += int(w_atk_units * w_atk_cnt * 0.9 * AGG)
        if b_atk_cnt >= 2:
            mg -= int(b_atk_units * b_atk_cnt * 0.9 * AGG)

        return mg, eg

    def _evaluate_pawn_storms(self, board):
        """
        Reward pawns marching toward the enemy king (pawn-storm attacks).
        The further advanced an attacking pawn and the closer to the enemy
        king's file, the bigger the bonus. Middlegame-only term.
        Returns a White-perspective score.
        """
        mg = 0
        AGG = self.AGGRESSION
        wk = board.king(chess.WHITE)
        bk = board.king(chess.BLACK)

        if bk is not None:
            bk_file = chess.square_file(bk)
            for sq in board.pieces(chess.PAWN, chess.WHITE):
                if abs(chess.square_file(sq) - bk_file) <= 2:
                    r = chess.square_rank(sq)  # 1..6 relevant
                    mg += int(r * r * 0.8 * AGG)
        if wk is not None:
            wk_file = chess.square_file(wk)
            for sq in board.pieces(chess.PAWN, chess.BLACK):
                if abs(chess.square_file(sq) - wk_file) <= 2:
                    r = 7 - chess.square_rank(sq)
                    mg -= int(r * r * 0.8 * AGG)

        return mg

    def is_endgame(self, board):
        """Check if we're in an endgame (for external use)."""
        queens = len(board.pieces(chess.QUEEN, True)) + len(board.pieces(chess.QUEEN, False))
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