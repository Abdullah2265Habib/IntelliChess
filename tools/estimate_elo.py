"""
Estimate the Elo of the IntelliChess engine by playing a match against
Stockfish pinned to a known strength (UCI_Elo), then converting the match
score into an Elo estimate.

Run from the PROJECT ROOT:

    python tools/estimate_elo.py --games 40 --anchor 1600 --movetime 0.5

Options:
    --stockfish PATH   path to the stockfish binary (default: ./stockfish.exe)
    --games N          number of games to play (even number; colors alternate)
    --anchor R         Stockfish UCI_Elo to play against (1320..3190)
    --movetime SEC     thinking time per move for BOTH engines (fair TC)
    --auto             auto-ladder: re-anchor toward your level for a better estimate

Interpretation:
    your_Elo ~= anchor + 400 * log10(S / (1 - S))
where S is your fractional score. A 95% confidence margin is printed too.
Scores near 0% or 100% mean the anchor is too far off -- lower/raise --anchor
(or use --auto) until you score roughly 30-70%.
"""

import os
import sys
import math
import time
import argparse

import chess
import chess.engine

# --- make the project's engine importable (mirrors gui/main.py) ---
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# Order matters: ROOT must come first so `engine` resolves to the PACKAGE
# (engine/__init__.py), not the bare engine/engine.py module. ROOT/engine is
# still needed so engine.py's flat `from position_evaluator import ...` works.
sys.path.insert(0, os.path.join(ROOT, "engine"))
sys.path.insert(0, ROOT)
from engine.engine import EnhancedChessEngine  # noqa: E402


# A handful of varied, balanced opening positions (plies ~4-8) so the games
# are not all identical. Colors are alternated across the pair.
OPENINGS = [
    "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",   # 1.e4 e5
    "rnbqkbnr/pp1ppppp/8/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2",  # Sicilian
    "rnbqkb1r/pppppppp/5n2/8/3P4/8/PPP1PPPP/RNBQKBNR w KQkq - 2 2",    # 1.d4 Nf6
    "rnbqkbnr/pp1ppppp/8/2p5/2P5/8/PP1PPPPP/RNBQKBNR b KQkq - 0 2",    # English
    "rnbqkb1r/pppp1ppp/5n2/4p3/2P5/2N5/PP1PPPPP/R1BQKBNR w KQkq - 2 3",
    "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 3 3",
]


def elo_diff(score):
    """Elo difference implied by a fractional score in (0, 1)."""
    score = min(max(score, 1e-6), 1 - 1e-6)
    return 400.0 * math.log10(score / (1.0 - score))


def margin_95(score, n):
    """Rough 95% Elo margin from the standard error of the score."""
    if n == 0:
        return float("inf")
    se = math.sqrt(max(score * (1.0 - score), 1e-9) / n)
    lo = elo_diff(score - 1.96 * se) if score - 1.96 * se > 0 else -1200
    hi = elo_diff(score + 1.96 * se) if score + 1.96 * se < 1 else 1200
    return (hi - lo) / 2.0


def play_game(my_engine, sf, my_is_white, movetime, anchor):
    """Play one game; return 1.0 win / 0.5 draw / 0.0 loss for OUR engine."""
    start = OPENINGS[play_game.counter % len(OPENINGS)]
    play_game.counter += 1
    board = chess.Board(start)

    while not board.is_game_over(claim_draw=True):
        my_turn = (board.turn == chess.WHITE) == my_is_white
        if my_turn:
            move = my_engine.get_best_move(board, max_time=movetime)
            if move is None or move not in board.legal_moves:
                move = list(board.legal_moves)[0]
        else:
            result = sf.play(board, chess.engine.Limit(time=movetime))
            move = result.move
        board.push(move)
        if board.fullmove_number > 200:  # safety cap
            break

    outcome = board.outcome(claim_draw=True)
    if outcome is None or outcome.winner is None:
        return 0.5
    return 1.0 if (outcome.winner == chess.WHITE) == my_is_white else 0.0


play_game.counter = 0


def run_match(stockfish_path, games, anchor, movetime):
    my_engine = EnhancedChessEngine()
    sf = chess.engine.SimpleEngine.popen_uci(stockfish_path)
    sf.configure({"UCI_LimitStrength": True, "UCI_Elo": int(anchor)})

    score = 0.0
    wins = draws = losses = 0
    try:
        for g in range(games):
            my_engine.clear_tables()
            my_is_white = (g % 2 == 0)
            r = play_game(my_engine, sf, my_is_white, movetime, anchor)
            score += r
            wins += r == 1.0
            draws += r == 0.5
            losses += r == 0.0
            frac = score / (g + 1)
            est = anchor + elo_diff(frac)
            print(f"  game {g+1:>3}/{games}  "
                  f"{'W' if my_is_white else 'B'}  result={r:>3}  "
                  f"running: +{wins} ={draws} -{losses}  "
                  f"score={frac*100:5.1f}%  est~{est:6.0f}")
    finally:
        sf.quit()

    frac = score / games
    return frac, wins, draws, losses


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stockfish", default=os.path.join(ROOT, "stockfish.exe"))
    ap.add_argument("--games", type=int, default=20)
    ap.add_argument("--anchor", type=int, default=1600)
    ap.add_argument("--movetime", type=float, default=0.5)
    ap.add_argument("--auto", action="store_true",
                    help="re-anchor once toward your level for a sharper estimate")
    args = ap.parse_args()

    if not os.path.exists(args.stockfish):
        print(f"Stockfish binary not found: {args.stockfish}")
        print("Download one from https://stockfishchess.org/download/ and pass --stockfish PATH")
        sys.exit(1)

    anchor = args.anchor
    print(f"\nMatch: IntelliChess vs Stockfish@{anchor} Elo | "
          f"{args.games} games | {args.movetime}s/move\n")

    frac, w, d, l = run_match(args.stockfish, args.games, anchor, args.movetime)
    est = anchor + elo_diff(frac)
    margin = margin_95(frac, args.games)

    # Optional second pass anchored near the first estimate (more reliable
    # because the score lands nearer 50%).
    if args.auto and 0.0 < frac < 1.0:
        new_anchor = int(max(1320, min(3190, round(est / 25) * 25)))
        if abs(new_anchor - anchor) >= 25:
            print(f"\nAuto re-anchor -> Stockfish@{new_anchor}\n")
            frac, w, d, l = run_match(args.stockfish, args.games, new_anchor, args.movetime)
            anchor = new_anchor
            est = anchor + elo_diff(frac)
            margin = margin_95(frac, args.games)

    print("\n" + "=" * 52)
    print(f"  Opponent (Stockfish) Elo : {anchor}")
    print(f"  Games                    : {args.games}  (+{w} ={d} -{l})")
    print(f"  Score                    : {frac*100:.1f}%")
    print(f"  ESTIMATED IntelliChess Elo: {est:.0f}  (+/- {margin:.0f}, 95%)")
    print("=" * 52)
    if frac < 0.05 or frac > 0.95:
        print("  NOTE: score is lopsided -- change --anchor so you score 30-70%.")
    print("  Note: Stockfish UCI_Elo is approximate; more games = tighter margin.")


if __name__ == "__main__":
    main()
