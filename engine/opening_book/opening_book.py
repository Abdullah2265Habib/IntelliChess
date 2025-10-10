import chess
import chess.pgn
import os
import random
from collections import defaultdict, Counter

class OpeningBook:
    def __init__(self, base_dir="engine/opening_book/dataset", max_ply=10):
        self.base_dir = base_dir
        self.max_ply = max_ply
        self.opening_moves = defaultdict(Counter)
        self.eco_openings = {}
    
        print(f"Initializing opening book from: {os.path.abspath(base_dir)}")
        self.check_files()  # Check files first
        self.load_all_openings()
    
    def check_files(self):
        """Check if required files exist and have content"""
        pgn_path = os.path.join(self.base_dir, "lichess_games.pgn")
        eco_files = ['a.tsv', 'b.tsv', 'c.tsv', 'd.tsv', 'e.tsv']
    
        print("Checking opening book files:")
    
        # Check PGN file
        if os.path.exists(pgn_path):
            size = os.path.getsize(pgn_path)
            print(f"  lichess_games.pgn: {size} bytes")
            if size == 0:
                print("  WARNING: PGN file is empty!")
        else:
            print("  WARNING: lichess_games.pgn not found!")
    
        # Check ECO files
        for eco_file in eco_files:
            file_path = os.path.join(self.base_dir, eco_file)
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                print(f"  {eco_file}: {size} bytes")
                if size == 0:
                    print(f"  WARNING: {eco_file} is empty!")
            else:
                print(f"  WARNING: {eco_file} not found!")
    
    def create_fallback_openings(self):
        """Create basic opening moves if files are empty"""
        print("Creating fallback opening moves...")
    
        # Starting position moves
        board = chess.Board()
        fen = self._get_position_key(board)
    
        # Common opening moves for white
        white_moves = [
            chess.Move.from_uci("e2e4"),  # King's Pawn
            chess.Move.from_uci("d2d4"),  # Queen's Pawn  
            chess.Move.from_uci("c2c4"),  # English
            chess.Move.from_uci("g1f3"),  # Reti
        ]
    
        for move in white_moves:
            if move in board.legal_moves:
                self.opening_moves[fen][move] = 100
    
        # After 1.e4
        board.push(chess.Move.from_uci("e2e4"))
        fen_e4 = self._get_position_key(board)
    
        black_responses = [
            chess.Move.from_uci("e7e5"),  # Open Game
            chess.Move.from_uci("c7c5"),  # Sicilian
            chess.Move.from_uci("e7e6"),  # French
            chess.Move.from_uci("c7c6"),  # Caro-Kann
        ]
    
        for move in black_responses:
            if move in board.legal_moves:
                self.opening_moves[fen_e4][move] = 100
    
        print("Fallback openings created!")
    
    def load_lichess_games(self):
        """Load opening moves from Lichess PGN database"""
        print("Loading Lichess games...")
        game_count = 0
        
        pgn_path = os.path.join(self.base_dir, "lichess_games.pgn")
        try:
            with open(pgn_path, 'r') as pgn_file:
                while True:
                    game = chess.pgn.read_game(pgn_file)
                    if game is None:
                        break
                    
                    board = game.board()
                    moves = list(game.mainline_moves())
                    
                    # Only use games with reasonable length
                    if len(moves) >= 10:
                        self._add_game_to_book(board, moves)
                        game_count += 1
                    
                    if game_count % 1000 == 0:
                        print(f"Processed {game_count} games...")
                    
                    # Limit for memory (optional)
                    if game_count >= 50000:  # Adjust based on your memory
                        break
                        
        except FileNotFoundError:
            print(f"PGN file not found at {pgn_path}")
        
        print(f"Loaded {game_count} games from Lichess")
    
    def load_eco_openings(self):
        """Load ECO openings from TSV files"""
        print("Loading ECO openings...")
        eco_files = ['a.tsv', 'b.tsv', 'c.tsv', 'd.tsv', 'e.tsv']
        
        for eco_file in eco_files:
            file_path = os.path.join(self.base_dir, eco_file)
            try:
                with open(file_path, 'r') as f:
                    for line in f:
                        parts = line.strip().split('\t')
                        if len(parts) >= 3:
                            eco_code, moves_str, name = parts[0], parts[1], parts[2]
                            self._parse_eco_line(eco_code, moves_str, name)
            except FileNotFoundError:
                print(f"ECO file not found: {file_path}")
    
    def _parse_eco_line(self, eco_code, moves_str, name):
        """Parse a single ECO line and add to opening book"""
        board = chess.Board()
        moves = moves_str.split()
        
        try:
            for i, move_str in enumerate(moves):
                # Skip move numbers
                if move_str.endswith('.') or ('.' in move_str and move_str.split('.')[0].isdigit()):
                    continue
                
                # Handle check and capture symbols
                move_str = move_str.replace('+', '').replace('#', '')
                
                # Parse the move
                move = board.parse_san(move_str)
                fen = self._get_position_key(board)
                
                # Add to opening book
                self.opening_moves[fen][move] += 100  # Higher weight for ECO moves
                
                board.push(move)
                
                # Store ECO info
                if i == 0:  # First move of the variation
                    self.eco_openings[fen] = name
                    
        except Exception as e:
            # Skip invalid moves
            pass
    
    def _add_game_to_book(self, board, moves):
        """Add a single game to the opening book"""
        current_board = board.copy()
        
        for i, move in enumerate(moves):
            if i >= self.max_ply * 2:  # Stop after max_ply moves for each side
                break
            
            fen = self._get_position_key(current_board)
            self.opening_moves[fen][move] += 1
            current_board.push(move)
    
    def _get_position_key(self, board):
        """Get a simplified FEN for position (without move counters)"""
        fen_parts = board.fen().split(' ')
        return ' '.join(fen_parts[:4])  # Only position, active color, castling, ep
    
    def get_opening_move(self, board):
        """Get a move from the opening book for the current position"""
        if board.ply() >= self.max_ply:
            return None
        
        fen = self._get_position_key(board)
        
        if fen in self.opening_moves:
            moves_counter = self.opening_moves[fen]
            
            # Get all legal moves that are in our opening book
            legal_opening_moves = []
            weights = []
            
            for move, frequency in moves_counter.items():
                if move in board.legal_moves:
                    legal_opening_moves.append(move)
                    weights.append(frequency)
            
            if legal_opening_moves:
                # Weighted random choice based on frequency
                total = sum(weights)
                if total > 0:
                    r = random.uniform(0, total)
                    current = 0
                    for i, weight in enumerate(weights):
                        current += weight
                        if r <= current:
                            return legal_opening_moves[i]
        
        return None
    
    def get_opening_name(self, board):
        """Get the name of the current opening if known"""
        fen = self._get_position_key(board)
        return self.eco_openings.get(fen, "Unknown Opening")
    
    def load_all_openings(self):
        """Load both Lichess games and ECO openings"""
        games_loaded = False
        eco_loaded = False

        try:
            self.load_lichess_games()
            games_loaded = True
        except Exception as e:
            print(f"Failed to load Lichess games: {e}")

        try:
            self.load_eco_openings() 
            eco_loaded = True
        except Exception as e:
            print(f"Failed to load ECO openings: {e}")

        # If both failed, create fallback openings
        if not games_loaded and not eco_loaded:
            print("Both Lichess and ECO loading failed, creating fallback openings")
            self.create_fallback_openings()
        else:
            print("Opening book loaded successfully!")