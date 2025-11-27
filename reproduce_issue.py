import chess.pgn
import io

pgn_content = """
[Event "?"]
[Site "?"]
[Date "2025.11.14"]
[Round "?"]
[White "?"]
[Black "?"]
[Result "*"]

1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 4. O-O Nf6 5. d3 d6 6. c3 a6 7. Bb3 Ba7 8. h3 h6 9. Re1 O-O 10. Nbd2 Re8 11. Nf1 Be6 12. Bc2 d5 13. exd5 Bxd5 14. Ng3 Qd7 15. Nh4 Rad8 16. Nhf5 Be6 17. Qf3 Bd5 18. Ne4 Nxe4 19. dxe4 Be6 20. Qg4 Bxf5 21. exf5 Kh8 22. Qh5 f6 23. Re4 Re7 24. Rh4 Qe8 25. Qg4 Qf8 26. Bb3 e4 27. Bf4 Ne5 28. Bxe5 Rxe5 29. Re1 e3 30. fxe3 Bxe3+ 31. Kh1 Bf2 32. Rxe5 Bxh4 33. Re6 Bg5 34. h4 Bc1 35. Qe2 Bf4 36. Re4 Be5 37. g4 Qd6 38. g5 Qd2 39. Kg2 Qxe2+ 40. Rxe2 hxg5 41. hxg5 Kh7 42. Kf3 g6 43. Bc2 gxf5 44. Bxf5+ Kg7 45. g6 Rh8 46. Rd2 Bd6 47. c4 b6 48. b4 Rh5 49. Kg4 Rg5+ 50. Kh4 Rxf5 51. c5 bxc5 52. bxc5 Rxc5 53. Rg2 Rg5 54. Rc2 Kxg6 55. Rc6 a5 56. Ra6 Bb4 57. a3 Bxa3 58. Rc6 Bd6 59. Rc4 f5 60. Kh3 Rg3+ 61. Kh4 Rg4+ 62. Rxg4+ fxg4 63. Kxg4 a4 64. Kf3 a3 65. Ke4 a2 66. Kd5 a1=Q 67. Kc6 Qc3+ 68. Kd7 Kf6 69. Kc8 Ke7 70. Kb7 Kd7 71. Ka6 Kc6 72. Ka7 Qa5+ 73. Kb8 Qb6+ 74. Ka8 Qb7# 0-1
"""

# I'll try to simulate the error by creating a PGN with an illegal move
# The user said "Kxh4" in "8/8/8/3B2rk/P2K4/8/8/8 w - - 1 78"
# Let's try to set up that board and play Kxh4
board = chess.Board("8/8/8/3B2rk/P2K4/8/8/8 w - - 1 78")
print(f"Board:\n{board}")
print(f"Legal moves: {[m.uci() for m in board.legal_moves]}")

try:
    move = board.parse_san("Kxh4")
    print(f"Parsed move: {move}")
except ValueError as e:
    print(f"Error parsing SAN: {e}")

# Now try reading a PGN with this move
pgn_with_illegal = """
[FEN "8/8/8/3B2rk/P2K4/8/8/8 w - - 1 78"]
1. Kxh4
"""
pgn_io = io.StringIO(pgn_with_illegal)
try:
    game = chess.pgn.read_game(pgn_io)
    print("Read game successfully")
    if game.errors:
        print(f"Game errors: {game.errors}")
except Exception as e:
    print(f"Read game failed: {e}")
