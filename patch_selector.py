"""
Simple script to patch game_selector.py with correct imports
"""

import os

selector_path = r"c:\Users\Abdullah Habib\Desktop\for me\IntelliChess\analysis\game_selector.py"

# Read the file
with open(selector_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the imports - change both problematic imports
content = content.replace(
    'from analysis.game_analyzer import ChessGameAnalyzer',
    '''# Import handling both direct run and module run
            try:
                from game_analyzer import ChessGameAnalyzer
            except ImportError:
                from analysis.game_analyzer import ChessGameAnalyzer'''
)

content = content.replace(
    'from analysis.analysis_viewer import AnalysisViewer',
    '''# Import handling both direct run and module run
        try:
            from analysis_viewer import AnalysisViewer
        except ImportError:
            from analysis.analysis_viewer import AnalysisViewer'''
)

# Write back
with open(selector_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("game_selector.py patched successfully!")
