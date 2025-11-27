
import sys
import os
sys.path.append(os.getcwd())
from analysis.game_analyzer import ChessGameAnalyzer

# Create a dummy PGN file
with open("test_game.pgn", "w") as f:
    f.write('[Event "Test Game"]\n[Site "Lichess"]\n[Date "2023.01.01"]\n[Round "-"]\n[White "White"]\n[Black "Black"]\n[Result "1-0"]\n\n1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 4. b4 Bxb4 5. c3 Ba5 6. d4 exd4 7. O-O 1-0')

print("Testing Lichess fallback...")
# Initialize without stockfish_path
analyzer = ChessGameAnalyzer(stockfish_path=None)
result = analyzer.analyze_pgn_file("test_game.pgn")

if "error" in result:
    print(f"Analysis failed: {result['error']}")
else:
    print("Analysis successful!")
    print(f"Moves analyzed: {len(result.get('moves', []))}")
    # Check if we got evaluation data (which comes from Lichess)
    if result.get('moves') and 'eval' in result['moves'][0]:
        print("Evaluation data found.")
    else:
        print("No evaluation data found.")

# Clean up
try:
    os.remove("test_game.pgn")
except:
    pass
