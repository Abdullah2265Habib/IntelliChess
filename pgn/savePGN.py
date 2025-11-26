import chess.pgn
import datetime
import os

def saveGamePGN(board, auto_analyze=False):
    """
    Save game to PGN format and optionally trigger analysis
    
    Args:
        board: chess.Board object with the game
        auto_analyze: If True, automatically analyze the game after saving
    """
    game = chess.pgn.Game()
    node = game
    for move in board.move_stack:
        node = node.add_variation(move)
    
    game.headers["Event"] = "Bullet: 1 min"
    game.headers["Date"] = datetime.datetime.now().strftime("%Y.%m.%d")
    game.headers["Result"] = board.result()
    # TODO: Add white, black, round no, and site headers

    pgn_string = str(game)

    os.makedirs("games", exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"games/{timestamp}.txt"

    with open(filename, "w") as file:
        file.write(pgn_string)

    print(f"[INFO] Game saved to {filename}")
    
    # Optional: Trigger analysis
    if auto_analyze:
        print("[INFO] Starting game analysis...")
        try:
            import sys
            sys.path.append(os.path.dirname(os.path.dirname(__file__)))
            from analysis.game_analyzer import ChessGameAnalyzer
            
            analyzer = ChessGameAnalyzer()
            analysis = analyzer.analyze_pgn_file(filename)
            
            if "error" not in analysis:
                # Save analysis
                import json
                analysis_file = filename.replace(".txt", "_analysis.json")
                with open(analysis_file, 'w') as f:
                    json.dump(analysis, f, indent=2)
                
                print(f"[INFO] Analysis saved to {analysis_file}")
                analyzer.print_analysis_summary(analysis)
            else:
                print(f"[WARNING] Analysis failed: {analysis['error']}")
        except Exception as e:
            print(f"[WARNING] Could not analyze game: {e}")
    
    return filename