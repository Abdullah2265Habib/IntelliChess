"""
Auto-analyze games after they're saved
Add this to your project root as 'run_analysis.py'
"""

import os
import sys
import glob
import subprocess

def find_latest_game():
    """Find the most recently saved game"""
    games = glob.glob("games/*[!_analysis].txt")
    
    if not games:
        print("No games found in 'games' folder")
        return None
    
    return max(games, key=os.path.getctime)

def find_stockfish():
    """Find Stockfish executable"""
    import shutil
    
    # Check system PATH
    path = shutil.which("stockfish")
    if path:
        return path
        
    # Check common locations
    common_paths = [
        "stockfish.exe",
        "stockfish",
        "engine/stockfish.exe",
        "engine/stockfish",
        "bin/stockfish.exe",
        "bin/stockfish"
    ]
    
    for p in common_paths:
        if os.path.exists(p):
            return os.path.abspath(p)
            
    return None

def analyze_game(pgn_file):
    """Run analysis on a game file"""
    print(f"\nAnalyzing game: {pgn_file}")
    
    stockfish_path = find_stockfish()
    if stockfish_path:
        print(f"   Using Stockfish at: {stockfish_path}")
        print("Please wait, analyzing entire game...")
    else:
        print("Stockfish not found!")
        print("   To use this tool, please download Stockfish and place it in the project folder.")
        print("   (Expected locations: stockfish.exe, engine/stockfish.exe, or in system PATH)")
        return False
    
    # Import the analyzer
    sys.path.append(os.path.dirname(__file__))
    from analysis.game_analyzer import ChessGameAnalyzer
    
    analyzer = ChessGameAnalyzer(stockfish_path=stockfish_path)
    analysis = analyzer.analyze_pgn_file(pgn_file)
    
    if "error" in analysis:
        print(f"Analysis failed: {analysis['error']}")
        return False
    
    # Save analysis
    output_file = pgn_file.replace(".txt", "_analysis.json")
    import json
    with open(output_file, 'w') as f:
        json.dump(analysis, f, indent=2)
    
    # Print summary
    analyzer.print_analysis_summary(analysis)
    print(f"Analysis saved to: {output_file}")
    
    return True

def launch_viewer(pgn_file):
    """Launch the analysis viewer"""
    analysis_file = pgn_file.replace(".txt", "_analysis.json")
    
    if not os.path.exists(analysis_file):
        print(f"Analysis file not found: {analysis_file}")
        return
    
    print(f"\nLaunching analysis viewer...")
    
    from analysis.analysis_viewer import AnalysisViewer
    
    try:
        viewer = AnalysisViewer(pgn_file, analysis_file)
        viewer.run()
    except Exception as e:
        print(f"Viewer error: {e}")

def main():
    """Main function"""
    print("\n" + "="*60)
    print("IntelliChess Game Analysis Tool")
    print("="*60)
    
    # Check if a specific file was provided
    if len(sys.argv) > 1:
        pgn_file = sys.argv[1]
        if not os.path.exists(pgn_file):
            print(f"File not found: {pgn_file}")
            return
    else:
        # Find latest game
        pgn_file = find_latest_game()
        if not pgn_file:
            return
        print(f"Found latest game: {pgn_file}")
    
    # Check if analysis already exists
    analysis_file = pgn_file.replace(".txt", "_analysis.json")
    
    if os.path.exists(analysis_file):
        print(f"\nAnalysis already exists: {analysis_file}")
        response = input("   Re-analyze? (y/n): ").strip().lower()
        
        if response != 'y':
            launch_viewer(pgn_file)
            return
    
    # Run analysis
    success = analyze_game(pgn_file)
    
    if success:
        print("\n" + "="*60)
        response = input("Launch analysis viewer? (y/n): ").strip().lower()
        
        if response == 'y':
            launch_viewer(pgn_file)

if __name__ == "__main__":
    main()