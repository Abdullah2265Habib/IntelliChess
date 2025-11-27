"""
Chess Game Analysis using Lichess API and Stockfish
Analyzes PGN files and provides detailed move classification and evaluation
"""

import requests
import chess
import chess.pgn
import json
import time
from typing import Dict, List, Optional
import io
import chess.engine

class ChessGameAnalyzer:
    """Analyzes chess games using Stockfish or Lichess cloud analysis API"""
    
    def __init__(self, stockfish_path: str = None):
        self.stockfish_path = stockfish_path
        self.base_url = "https://lichess.org/api"
        self.headers = {
            "Accept": "application/json"
        }
        self.stockfish_engine = None
        
        # Try to initialize stockfish library if path is provided
        if self.stockfish_path:
            try:
                from stockfish import Stockfish
                self.stockfish_engine = Stockfish(path=self.stockfish_path)
                self.stockfish_engine.set_depth(15)  # Set analysis depth
                print("Stockfish library initialized successfully")
            except ImportError:
                print("Warning: stockfish library not installed. Install with: pip install stockfish")
                self.stockfish_engine = None
            except Exception as e:
                print(f"Warning: Failed to initialize Stockfish library: {e}")
                self.stockfish_engine = None
    
    def analyze_pgn_file(self, pgn_file: str) -> Dict:
        """
        Analyze a PGN file
        
        Args:
            pgn_file: Path to PGN file
            
        Returns:
            Analysis results dictionary
        """
        try:
            # Load game from file
            with open(pgn_file, 'r') as f:
                pgn_text = f.read()
            
            pgn_io = io.StringIO(pgn_text)
            game = chess.pgn.read_game(pgn_io)
            
            if not game:
                return {"error": "Failed to parse PGN file"}
            
            # Analyze using Stockfish library if available, otherwise try engine, then cloud
            if self.stockfish_engine:
                print("Using Stockfish library for analysis...")
                analysis_result = self._analyze_with_stockfish_library(game)
            elif self.stockfish_path:
                print("Using Stockfish engine for analysis...")
                analysis_result = self._analyze_with_stockfish(game)
            else:
                print("Using Lichess cloud analysis...")
                analysis_result = self._request_cloud_analysis(game)
            
            # Process the analysis
            processed = self._process_analysis(game, analysis_result)
            
            return processed
            
        except Exception as e:
            return {"error": f"Analysis failed: {str(e)}"}
    
    def _analyze_with_stockfish_library(self, game: chess.pgn.Game) -> Dict:
        """
        Analyze game using stockfish Python library
        
        Args:
            game: chess.pgn.Game object
            
        Returns:
            Analysis data compatible with process_analysis
        """
        if not self.stockfish_engine:
            return {"error": "Stockfish engine not initialized"}
        
        try:
            board = game.board()
            analysis_data = []
            move_count = len(list(game.mainline_moves()))
            
            print(f"Analyzing {move_count} moves...")
            
            # Analyze each position
            for idx, move in enumerate(game.mainline_moves()):
                fen = board.fen()
                
                # Set position and get evaluation
                self.stockfish_engine.set_fen_position(fen)
                
                # Get top 3 lines
                top_moves = self.stockfish_engine.get_top_moves(3)
                
                pvs = []
                for move_info in top_moves:
                    centipawn = move_info.get('Centipawn')
                    mate_score = move_info.get('Mate')
                    
                    pvs.append({
                        "moves": move_info.get('Move', ''),
                        "cp": centipawn,
                        "mate": mate_score
                    })
                
                eval_data = {"pvs": pvs}
                
                analysis_data.append({
                    "fen": fen,
                    "move": move.uci(),
                    "eval": eval_data
                })
                
                board.push(move)
                
                # Progress indicator
                if (idx + 1) % 10 == 0:
                    print(f"  Analyzed {idx + 1}/{move_count} moves...")
            
            print(f"Analysis complete! Analyzed {len(analysis_data)} moves.")
            return {"moves": analysis_data, "game": game}
            
        except Exception as e:
            return {"error": f"Stockfish library analysis failed: {str(e)}"}

    def _analyze_with_stockfish(self, game: chess.pgn.Game) -> Dict:
        """
        Analyze game using local Stockfish engine (chess.engine)
        
        Args:
            game: chess.pgn.Game object
            
        Returns:
            Analysis data compatible with process_analysis
        """
        try:
            engine = chess.engine.SimpleEngine.popen_uci(self.stockfish_path)
        except Exception as e:
            return {"error": f"Failed to start Stockfish: {str(e)}"}
            
        try:
            board = game.board()
            analysis_data = []
            
            # Analyze each position
            for move in game.mainline_moves():
                fen = board.fen()
                
                # Analyze position
                # We use a small time limit for speed, but user might want deeper analysis
                # Let's use 0.1s per move for now
                info = engine.analyse(board, chess.engine.Limit(time=0.1), multipv=3)
                
                pvs = []
                for pv_info in info:
                    score = pv_info.get("score")
                    mate = None
                    cp = None
                    
                    if score.is_mate():
                        mate = score.mate()
                    else:
                        cp = score.score()
                        
                    # Get PV moves as string
                    pv_moves = [m.uci() for m in pv_info.get("pv", [])]
                    moves_str = " ".join(pv_moves)
                    
                    pvs.append({
                        "moves": moves_str,
                        "cp": cp,
                        "mate": mate
                    })
                
                eval_data = {"pvs": pvs}
                
                analysis_data.append({
                    "fen": fen,
                    "move": move.uci(),
                    "eval": eval_data
                })
                
                board.push(move)
            
            engine.quit()
            return {"moves": analysis_data, "game": game}
            
        except Exception as e:
            try:
                engine.quit()
            except:
                pass
            return {"error": f"Stockfish analysis failed: {str(e)}"}
    
    def _request_cloud_analysis(self, game: chess.pgn.Game) -> Dict:
        """
        Request analysis from Lichess cloud analysis
        
        Args:
            game: chess.pgn.Game object
            
        Returns:
            Analysis data from Lichess
        """
        try:
            # Convert game to PGN string
            exporter = chess.pgn.StringExporter(headers=False, variations=False, comments=False)
            pgn_moves = game.accept(exporter)
            
            # Lichess cloud eval endpoint
            # Note: This uses the cloud evaluation API which doesn't require authentication
            # but has rate limits
            
            board = game.board()
            moves = []
            analysis_data = []
            
            # Analyze each position
            for move in game.mainline_moves():
                fen = board.fen()
                
                # Get cloud evaluation for this position
                eval_data = self._get_cloud_eval(fen)
                
                analysis_data.append({
                    "fen": fen,
                    "move": move.uci(),
                    "eval": eval_data
                })
                
                board.push(move)
                
                # Rate limiting - be respectful to the API
                time.sleep(0.3)
            
            return {"moves": analysis_data, "game": game}
            
        except Exception as e:
            return {"error": f"Cloud analysis request failed: {str(e)}"}
    
    def _get_cloud_eval(self, fen: str) -> Dict:
        """
        Get cloud evaluation for a position
        
        Args:
            fen: FEN string of the position
            
        Returns:
            Evaluation data
        """
        try:
            url = f"{self.base_url}/cloud-eval"
            params = {
                "fen": fen,
                "multiPv": 3  # Get top 3 moves
            }
            
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def _process_analysis(self, game: chess.pgn.Game, analysis_data: Dict) -> Dict:
        """
        Process raw analysis data into human-readable format
        
        Args:
            game: chess.pgn.Game object
            analysis_data: Raw analysis from Lichess
            
        Returns:
            Processed analysis with move classifications
        """
        if "error" in analysis_data:
            return analysis_data
        
        moves_data = analysis_data.get("moves", [])
        
        # Initialize counters
        move_classifications = {
            "brilliant": 0,
            "great": 0,
            "best": 0,
            "excellent": 0,
            "good": 0,
            "book": 0,
            "inaccuracy": 0,
            "mistake": 0,
            "blunder": 0
        }
        
        detailed_moves = []
        board = game.board()
        prev_eval = 0
        
        for idx, move_data in enumerate(moves_data):
            eval_info = move_data.get("eval", {})
            
            if "error" in eval_info:
                continue
            
            # Extract evaluation
            current_eval = self._extract_eval(eval_info)
            
            # Get best move suggestion
            pvs = eval_info.get("pvs", [])
            best_move = pvs[0].get("moves", "").split()[0] if pvs else None
            
            # Classify the move
            played_move = move_data.get("move")
            classification = self._classify_move(
                prev_eval, current_eval, played_move, best_move, board.turn
            )
            
            move_classifications[classification] += 1
            
            detailed_moves.append({
                "move_number": idx + 1,
                "move": played_move,
                "fen": move_data.get("fen"),
                "eval": current_eval,
                "classification": classification,
                "best_move": best_move,
                "alternative_lines": pvs[:3] if pvs else []
            })
            
            prev_eval = current_eval
            board.push(chess.Move.from_uci(played_move))
        
        # Estimate ELO based on move quality
        estimated_elo = self._estimate_elo(move_classifications, len(moves_data))
        
        return {
            "game_info": {
                "event": game.headers.get("Event", "Unknown"),
                "date": game.headers.get("Date", "Unknown"),
                "result": game.headers.get("Result", "Unknown")
            },
            "move_classifications": move_classifications,
            "estimated_elo": estimated_elo,
            "detailed_moves": detailed_moves,
            "total_moves": len(moves_data)
        }
    
    def _extract_eval(self, eval_data: Dict) -> float:
        """Extract numeric evaluation from eval data"""
        pvs = eval_data.get("pvs", [])
        if not pvs:
            return 0.0
        
        cp = pvs[0].get("cp")
        mate = pvs[0].get("mate")
        
        if mate is not None:
            # Mate score: positive for winning, negative for losing
            return 100.0 if mate > 0 else -100.0
        elif cp is not None:
            # Centipawn score
            return cp / 100.0
        
        return 0.0
    
    def _classify_move(self, prev_eval: float, current_eval: float, 
                       played_move: str, best_move: str, turn: bool) -> str:
        """
        Classify a move based on evaluation change
        
        Args:
            prev_eval: Previous position evaluation
            current_eval: Current position evaluation
            played_move: Move that was played
            best_move: Best move according to engine
            turn: True for white, False for black
            
        Returns:
            Classification string
        """
        # Adjust for turn (we want eval from the moving player's perspective)
        if not turn:
            prev_eval = -prev_eval
            current_eval = -current_eval
        
        eval_loss = prev_eval - current_eval
        
        # Check if it's the best move
        if played_move == best_move:
            if eval_loss <= 0.1:
                return "best"
            elif eval_loss <= 0.3:
                return "excellent"
        
        # Check for brilliant moves (sacrifices that lead to advantage)
        if eval_loss < -0.5:  # Move improved position significantly
            return "brilliant"
        
        # Classify based on eval loss
        if eval_loss <= 0.1:
            return "great"
        elif eval_loss <= 0.3:
            return "good"
        elif eval_loss <= 1.0:
            return "inaccuracy"
        elif eval_loss <= 3.0:
            return "mistake"
        else:
            return "blunder"
    
    def _estimate_elo(self, classifications: Dict, total_moves: int) -> int:
        """
        Estimate player ELO based on move quality
        
        Args:
            classifications: Dictionary of move classifications
            total_moves: Total number of moves analyzed
            
        Returns:
            Estimated ELO rating
        """
        if total_moves == 0:
            return 0
        
        # Calculate accuracy score
        brilliant = classifications.get("brilliant", 0)
        great = classifications.get("great", 0)
        best = classifications.get("best", 0)
        excellent = classifications.get("excellent", 0)
        good = classifications.get("good", 0)
        inaccuracy = classifications.get("inaccuracy", 0)
        mistake = classifications.get("mistake", 0)
        blunder = classifications.get("blunder", 0)
        
        # Weighted score
        score = (
            brilliant * 1.5 +
            great * 1.3 +
            best * 1.2 +
            excellent * 1.0 +
            good * 0.8 -
            inaccuracy * 0.5 -
            mistake * 1.5 -
            blunder * 3.0
        )
        
        # Normalize to 0-1 range
        accuracy = max(0, min(1, (score / total_moves + 1) / 2))
        
        # Map to ELO (rough approximation)
        # 400 = beginner, 800 = casual, 1200 = intermediate, 1600 = advanced, 2000+ = expert
        base_elo = 400
        elo_range = 1600
        estimated = int(base_elo + (accuracy * elo_range))
        
        return estimated
    
    def print_analysis_summary(self, analysis: Dict):
        """
        Print a formatted analysis summary
        
        Args:
            analysis: Analysis dictionary
        """
        if "error" in analysis:
            print(f"\nError: {analysis['error']}")
            return
        
        game_info = analysis.get("game_info", {})
        classifications = analysis.get("move_classifications", {})
        estimated_elo = analysis.get("estimated_elo", 0)
        
        print("\n" + "="*60)
        print("CHESS GAME ANALYSIS")
        print("="*60)
        
        print(f"\nGame Information:")
        print(f"   Event: {game_info.get('event')}")
        print(f"   Date: {game_info.get('date')}")
        print(f"   Result: {game_info.get('result')}")
        
        print(f"\nMove Classifications:")
        print(f"   Brilliant:    {classifications.get('brilliant', 0)}")
        print(f"   Great:        {classifications.get('great', 0)}")
        print(f"   Best:         {classifications.get('best', 0)}")
        print(f"   Excellent:    {classifications.get('excellent', 0)}")
        print(f"   Good:         {classifications.get('good', 0)}")
        print(f"   Book:         {classifications.get('book', 0)}")
        print(f"   Inaccuracy:  {classifications.get('inaccuracy', 0)}")
        print(f"   Mistake:      {classifications.get('mistake', 0)}")
        print(f"   Blunder:      {classifications.get('blunder', 0)}")
        
        print(f"\nEstimated ELO: {estimated_elo}")
        print("="*60 + "\n")


# Example usage
if __name__ == "__main__":
    import sys
    
    analyzer = ChessGameAnalyzer()
    
    # Analyze a specific game file
    if len(sys.argv) > 1:
        pgn_file = sys.argv[1]
    else:
        # Default to most recent game
        import os
        import glob
        
        games = glob.glob("games/*.txt")
        if not games:
            print("No games found in 'games' folder")
            sys.exit(1)
        
        pgn_file = max(games, key=os.path.getctime)
        print(f"Analyzing most recent game: {pgn_file}")
    
    # Perform analysis
    print("\nAnalyzing game... (this may take a minute)")
    analysis = analyzer.analyze_pgn_file(pgn_file)
    
    # Print summary
    analyzer.print_analysis_summary(analysis)
    
    # Optionally save detailed analysis to JSON
    if "error" not in analysis:
        output_file = pgn_file.replace(".txt", "_analysis.json")
        with open(output_file, 'w') as f:
            json.dump(analysis, f, indent=2)
        print(f"Detailed analysis saved to: {output_file}")