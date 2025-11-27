"""
Game Statistics Visualization Module
Displays performance metrics and analysis graphs when a chess game ends
"""

import matplotlib.pyplot as plt
import matplotlib
import time
import json
import os
from typing import List, Tuple, Optional

# Use a non-interactive backend to avoid conflicts with pygame if needed, 
# but usually TkAgg is fine for showing windows after pygame loop
try:
    matplotlib.use('TkAgg')
except:
    pass


class GameMetrics:
    """Stores all statistics and metrics during a chess game"""
    
    def __init__(self):
        # Evaluation data: (timestamp, eval_score, move_number, player)
        self.evaluations: List[Tuple[float, float, int, str]] = []
        
        # Depth data: (depth, nodes, time_taken, move_number, player)
        self.depths_data: List[Tuple[int, int, float, int, str]] = []
        
        # Move timing: (move_number, total_time, player)
        self.move_times: List[Tuple[int, float, str]] = []
        
        # Game start time
        self.game_start_time = time.time()
        
        # Current move number
        self.current_move = 0
    
    def add_depth_data(self, depth: int, nodes: int, time_taken: float, 
                       eval_score: float, player: str = "Bot"):
        """Add data for a specific depth iteration"""
        timestamp = time.time() - self.game_start_time
        
        self.depths_data.append((depth, nodes, time_taken, self.current_move, player))
        self.evaluations.append((timestamp, eval_score, self.current_move, player))
    
    def start_new_move(self):
        """Increment move counter"""
        self.current_move += 1
    
    def add_move_time(self, total_time: float, player: str = "Bot"):
        """Add total time taken for a move"""
        self.move_times.append((self.current_move, total_time, player))
    
    def has_data(self) -> bool:
        """Check if we have any data to display"""
        return len(self.depths_data) > 0 or len(self.evaluations) > 0

    def to_dict(self):
        """Convert metrics to dictionary for serialization"""
        return {
            "evaluations": self.evaluations,
            "depths_data": self.depths_data,
            "move_times": self.move_times,
            "game_start_time": self.game_start_time,
            "current_move": self.current_move
        }

    @classmethod
    def from_dict(cls, data):
        """Create metrics object from dictionary"""
        metrics = cls()
        metrics.evaluations = data.get("evaluations", [])
        metrics.depths_data = data.get("depths_data", [])
        metrics.move_times = data.get("move_times", [])
        metrics.game_start_time = data.get("game_start_time", time.time())
        metrics.current_move = data.get("current_move", 0)
        return metrics

def save_metrics(metrics: GameMetrics, filename: str):
    """Save metrics to a JSON file"""
    try:
        with open(filename, 'w') as f:
            json.dump(metrics.to_dict(), f)
        print(f"Statistics saved to {filename}")
    except Exception as e:
        print(f"Error saving statistics: {e}")

def load_metrics(filename: str) -> Optional[GameMetrics]:
    """Load metrics from a JSON file"""
    try:
        if not os.path.exists(filename):
            return None
        with open(filename, 'r') as f:
            data = json.load(f)
        return GameMetrics.from_dict(data)
    except Exception as e:
        print(f"Error loading statistics: {e}")
        return None


def display_game_statistics(metrics: GameMetrics):
    """
    Display comprehensive game statistics using matplotlib
    
    Shows 4 graphs:
    1. Nodes searched over time
    2. Time taken per depth level
    3. Nodes searched per depth level
    4. Evaluation score over time
    """
    
    if not metrics.has_data():
        print("No statistics data available to display")
        return
    
    # Create figure with 2x2 subplot layout
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Chess Game Performance Statistics', fontsize=16, fontweight='bold')
    
    # Graph 1: Cumulative Nodes vs Time
    if metrics.depths_data:
        # Group by move and calculate cumulative nodes
        cumulative_nodes = []
        cumulative_time = []
        total_nodes = 0
        
        # Sort by time to be safe
        sorted_depths = sorted(metrics.depths_data, key=lambda x: x[3]) # Sort by move num
        
        current_move_nodes = 0
        
        for depth, nodes, time_taken, move_num, player in metrics.depths_data:
            # We want cumulative nodes over the whole game
            # But nodes in depths_data are usually cumulative for that move
            # So we should take the max nodes for each move
            pass

        # Re-process to get proper cumulative timeline
        # We'll just plot raw data points for now
        times = []
        nodes_list = []
        running_nodes = 0
        
        for depth, nodes, time_taken, move_num, player in metrics.depths_data:
            # Approximate timestamp based on move number and time taken
            # This is a bit tricky without exact timestamps for each depth
            # So we'll use the evaluation timestamps if available
            pass
            
        # Simpler approach: Plot Nodes/Sec over moves
        move_nums = []
        nps_values = []
        
        for depth, nodes, time_taken, move_num, player in metrics.depths_data:
            if time_taken > 0.1: # Avoid division by zero and tiny intervals
                nps = nodes / time_taken
                move_nums.append(move_num + (depth/50.0)) # Spread out by depth
                nps_values.append(nps)
                
        ax1.scatter(move_nums, nps_values, alpha=0.5, s=10)
        ax1.set_xlabel('Move Number', fontsize=10)
        ax1.set_ylabel('Nodes Per Second', fontsize=10)
        ax1.set_title('Search Speed (NPS) over Game', fontsize=12, fontweight='bold')
        ax1.grid(True, alpha=0.3)
    
    # Graph 2: Time taken per depth
    if metrics.depths_data:
        depths = [d[0] for d in metrics.depths_data]
        times = [d[2] for d in metrics.depths_data]
        colors = ['blue' if d[4] == "Bot" else 'green' for d in metrics.depths_data]
        
        ax2.scatter(depths, times, c=colors, alpha=0.6, s=50)
        ax2.set_xlabel('Depth Level', fontsize=10)
        ax2.set_ylabel('Time Taken (seconds)', fontsize=10)
        ax2.set_title('Time Taken per Depth Level', fontsize=12, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        
        # Add legend
        from matplotlib.patches import Patch
        legend_elements = [Patch(facecolor='blue', label='Bot'),
                          Patch(facecolor='green', label='Player')]
        ax2.legend(handles=legend_elements, loc='upper left')
    
    # Graph 3: Nodes per depth
    if metrics.depths_data:
        depths = [d[0] for d in metrics.depths_data]
        nodes = [d[1] for d in metrics.depths_data]
        colors = ['blue' if d[4] == "Bot" else 'green' for d in metrics.depths_data]
        
        ax3.scatter(depths, nodes, c=colors, alpha=0.6, s=50)
        ax3.set_xlabel('Depth Level', fontsize=10)
        ax3.set_ylabel('Nodes Searched', fontsize=10)
        ax3.set_title('Nodes Searched per Depth Level', fontsize=12, fontweight='bold')
        ax3.grid(True, alpha=0.3)
        ax3.ticklabel_format(style='plain', axis='y')
        
        # Add legend
        ax3.legend(handles=legend_elements, loc='upper left')
    
    # Graph 4: Evaluation over time
    if metrics.evaluations:
        times = [e[0] for e in metrics.evaluations]
        evals = [e[1] for e in metrics.evaluations]
        
        # Clamp evals for better visualization
        clamped_evals = [max(min(e, 10), -10) for e in evals]
        
        ax4.plot(times, clamped_evals, 'r-', linewidth=2, marker='o', markersize=3)
        ax4.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
        ax4.set_xlabel('Time (seconds)', fontsize=10)
        ax4.set_ylabel('Evaluation Score (Cp)', fontsize=10)
        ax4.set_title('Position Evaluation Over Time', fontsize=12, fontweight='bold')
        ax4.grid(True, alpha=0.3)
        
        # Color the background based on advantage
        ax4.fill_between(times, clamped_evals, 0, where=[e >= 0 for e in clamped_evals], 
                        alpha=0.2, color='green', label='White advantage')
        ax4.fill_between(times, clamped_evals, 0, where=[e < 0 for e in clamped_evals], 
                        alpha=0.2, color='red', label='Black advantage')
        ax4.legend(loc='upper left')
    
    # Adjust layout to prevent overlap
    plt.tight_layout()
    
    # Show the plot
    print("Displaying game statistics...")
    plt.show()
    print("Statistics window closed.")

if __name__ == "__main__":
    # Try to load last game metrics
    metrics_file = "last_game_metrics.json"
    if os.path.exists(metrics_file):
        print(f"Loading statistics from {metrics_file}...")
        metrics = load_metrics(metrics_file)
        if metrics:
            display_game_statistics(metrics)
        else:
            print("Failed to load metrics.")
    else:
        print("No previous game statistics found.")
        print("Play a game first to generate statistics.")