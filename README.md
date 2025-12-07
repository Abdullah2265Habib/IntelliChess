# \# IntelliChess ♟️

# 

# A feature-rich chess engine and analysis platform built with Python, featuring advanced AI capabilities, game analysis, opening books, endgame tablebases, and comprehensive visualization tools.

# 

# !\[IntelliChess](https://img.shields.io/badge/Python-3.8+-blue.svg)

# !\[License](https://img.shields.io/badge/license-MIT-green.svg)

# !\[Chess](https://img.shields.io/badge/chess-engine-red.svg)

# 

# ---

# 

# \## 📋 Table of Contents

# 

# \- \[Overview](#overview)

# \- \[Key Features](#key-features)

# \- \[Installation](#installation)

# \- \[Project Structure](#project-structure)

# \- \[Usage](#usage)

# \- \[Engine Architecture](#engine-architecture)

# \- \[Analysis Tools](#analysis-tools)

# \- \[Configuration](#configuration)

# \- \[Requirements](#requirements)

# \- \[Contributing](#contributing)

# \- \[Troubleshooting](#troubleshooting)

# 

# ---

# 

# \## 🎯 Overview

# 

# IntelliChess is a sophisticated chess platform that combines a powerful chess engine with professional-grade analysis tools. It offers:

# 

# \- \*\*Advanced Chess Engine\*\*: Alpha-beta pruning with PVS (Principal Variation Search)

# \- \*\*Opening Book\*\*: 100,000+ master games and ECO classification

# \- \*\*Endgame Tablebases\*\*: Syzygy tablebase support for perfect endgame play

# \- \*\*Game Analysis\*\*: Move classification, evaluation graphs, and performance metrics

# \- \*\*Interactive GUI\*\*: Modern interface with real-time engine analysis

# 

# Whether you're learning chess, analyzing your games, or building chess applications, IntelliChess provides the tools you need.

# 

# ---

# 

# \## ✨ Key Features

# 

# \### 🤖 Chess Engine

# 

# \- \*\*Search Algorithm\*\*: 

# &nbsp; - Iterative deepening with aspiration windows

# &nbsp; - Principal Variation Search (PVS)

# &nbsp; - Null move pruning

# &nbsp; - Late move reduction (LMR)

# &nbsp; - Quiescence search to avoid horizon effect

# 

# \- \*\*Move Ordering\*\*:

# &nbsp; - MVV-LVA (Most Valuable Victim - Least Valuable Attacker)

# &nbsp; - Killer move heuristic

# &nbsp; - History heuristic

# &nbsp; - Transposition table

# 

# \- \*\*Evaluation\*\*:

# &nbsp; - Material counting

# &nbsp; - Piece-square tables

# &nbsp; - King safety evaluation

# &nbsp; - Pawn structure analysis

# &nbsp; - Piece activity and mobility

# &nbsp; - Center control

# &nbsp; - Endgame-specific evaluation

# 

# \### 📚 Opening Book

# 

# \- Supports both PGN game databases and ECO (Encyclopedia of Chess Openings)

# \- Compiled opening book for fast loading

# \- Frequency-based move selection

# \- Opening name identification

# 

# \### 🏁 Endgame Support

# 

# \- Syzygy tablebase integration

# \- Perfect play in 3-7 piece endgames

# \- WDL (Win/Draw/Loss) and DTZ (Distance to Zero) probing

# \- Basic endgame knowledge for KPK, KRK, KQK, KBNK

# 

# \### 📊 Game Analysis

# 

# \- \*\*Move Classification\*\*:

# &nbsp; - Brilliant (!!)

# &nbsp; - Great (!)

# &nbsp; - Best

# &nbsp; - Excellent

# &nbsp; - Good

# &nbsp; - Inaccuracy (?!)

# &nbsp; - Mistake (?)

# &nbsp; - Blunder (??)

# 

# \- \*\*Performance Metrics\*\*:

# &nbsp; - ELO estimation

# &nbsp; - Nodes searched per second

# &nbsp; - Search depth statistics

# &nbsp; - Time management analysis

# 

# \- \*\*Visualization\*\*:

# &nbsp; - Evaluation graphs

# &nbsp; - Performance statistics

# &nbsp; - Move history timeline

# &nbsp; - Real-time engine analysis display

# 

# \### 🎮 Interactive GUI

# 

# \- Clean, modern interface

# \- Piece dragging and move validation

# \- Timer support (Bullet, Blitz, Rapid)

# \- Side selection (play as White or Black)

# \- Move history panel

# \- Live engine analysis panel

# \- Scrollable content areas

# 

# ---

# 

# \## 🚀 Installation

# 

# \### Prerequisites

# 

# \- Python 3.8 or higher

# \- pip (Python package manager)

# 

# \### Quick Start

# 

# 1\. \*\*Clone the repository\*\*:

# ```bash

# git clone https://github.com/yourusername/IntelliChess.git

# cd IntelliChess

# ```

# 

# 2\. \*\*Install dependencies\*\*:

# ```bash

# pip install -r requirements.txt

# ```

# 

# Or use the provided batch file (Windows):

# ```bash

# requirements.bat

# ```

# 

# 3\. \*\*Optional: Download Stockfish\*\* (for enhanced analysis):

# &nbsp;  - Download from \[official Stockfish website](https://stockfishchess.org/download/)

# &nbsp;  - Place `stockfish.exe` in the project root or `engine/` folder

# 

# 4\. \*\*Optional: Download Syzygy Tablebases\*\* (for perfect endgame play):

# &nbsp;  - Download from \[Lichess Tablebases](https://database.lichess.org/#egtb)

# &nbsp;  - Place in `engine/tablebases/syzygy/` folder

# 

# \### Required Python Packages

# 

# ```

# pygame>=2.5.0

# chess>=1.9.4

# matplotlib>=3.7.0

# requests>=2.31.0

# ```

# 

# ---

# 

# \## 📁 Project Structure

# 

# ```

# IntelliChess/

# │

# ├── gui/                          # Graphical user interface

# │   ├── main.py                   # Main game loop and UI

# │   ├── board.py                  # Chess board rendering

# │   ├── menu.py                   # Game mode selection

# │   ├── timer.py                  # Chess clock implementation

# │   ├── turn.py                   # Side selection screen

# │   ├── utils.py                  # Image loading and utilities

# │   ├── statistics\_graphs.py      # Performance visualization

# │   ├── img/                      # Piece images and icons

# │   └── font/                     # Custom fonts (Orbitron)

# │

# ├── engine/                       # Chess engine core

# │   ├── engine.py                 # Main search engine (PVS)

# │   ├── position\_evaluator.py    # Board evaluation

# │   ├── opening\_book/             # Opening book system

# │   │   ├── opening\_book.py       # Opening book implementation

# │   │   └── dataset/              # PGN games and ECO data

# │   └── endgame/                  # Endgame support

# │       ├── endgame.py            # Basic endgame + tablebase

# │       └── tablebases/           # Syzygy tablebase files

# │

# ├── analysis/                     # Game analysis tools

# │   ├── game\_analyzer.py          # Engine-based game analyzer

# │   ├── analysis\_viewer.py        # Interactive analysis viewer

# │   └── game\_selector.py          # Game selection interface

# │

# ├── pgn/                          # PGN file handling

# │   └── savePGN.py                # Game saving utilities

# │

# ├── games/                        # Saved games (auto-created)

# │   ├── \*.txt                     # PGN game files

# │   └── \*\_analysis.json           # Analysis data

# │

# ├── run.bat                       # Windows launcher

# ├── run\_analysis.py               # Standalone analysis tool

# └── requirements.txt              # Python dependencies

# ```

# 

# ---

# 

# \## 💻 Usage

# 

# \### Playing a Game

# 

# 1\. \*\*Launch the game\*\*:

# ```bash

# python gui/main.py

# ```

# 

# Or double-click `run.bat` (Windows)

# 

# 2\. \*\*Select game mode\*\*:

# &nbsp;  - Bullet (1 minute)

# &nbsp;  - Blitz (3 minutes)

# &nbsp;  - Rapid (10 minutes)

# 

# 3\. \*\*Choose your side\*\*:

# &nbsp;  - Play as White

# &nbsp;  - Play as Black

# 

# 4\. \*\*Play\*\*:

# &nbsp;  - Click a piece to select

# &nbsp;  - Click destination to move

# &nbsp;  - Right-click to deselect

# &nbsp;  - Press 'R' to restart game

# 

# \### Analyzing Games

# 

# \#### Automatic Analysis

# 

# Games are automatically saved to the `games/` folder. To analyze:

# 

# ```bash

# python run\_analysis.py

# ```

# 

# This will:

# 1\. Find the most recent game

# 2\. Analyze with Stockfish (if available) or Lichess cloud

# 3\. Generate move classifications and metrics

# 4\. Launch the interactive viewer

# 

# \#### Manual Analysis

# 

# ```bash

# python -m analysis.game\_analyzer games/your\_game.txt

# ```

# 

# \#### Game Selector

# 

# Browse and analyze all saved games:

# 

# ```bash

# python -m analysis.game\_selector

# ```

# 

# Features:

# \- View all saved games

# \- See analysis status

# \- Analyze multiple games at once (Press 'A')

# \- Launch viewer for any game

# 

# \### Interactive Viewer

# 

# The analysis viewer provides:

# \- Move-by-move navigation (← → keys)

# \- Best move arrows (toggle with Space)

# \- Move classification icons

# \- Evaluation bar

# \- Move history panel

# \- Engine analysis output

# 

# \*\*Controls\*\*:

# \- `←/→`: Navigate moves

# \- `Space`: Toggle best move arrow

# \- `T`: Toggle threat display

# \- `R`: Reset to start

# \- `ESC`: Exit

# 

# ---

# 

# \## 🧠 Engine Architecture

# 

# \### Search Algorithm

# 

# IntelliChess uses a sophisticated search algorithm based on modern chess engine techniques:

# 

# 1\. \*\*Iterative Deepening\*\*: Gradually increases search depth, allowing for better time management and move ordering.

# 

# 2\. \*\*Principal Variation Search (PVS)\*\*: Optimized alpha-beta search that assumes the first move is best and verifies subsequent moves with null windows.

# 

# 3\. \*\*Aspiration Windows\*\*: Narrow search windows around the expected evaluation, with re-search if the window fails.

# 

# 4\. \*\*Null Move Pruning\*\*: Prunes positions where even giving the opponent a free move doesn't improve their position.

# 

# 5\. \*\*Late Move Reduction (LMR)\*\*: Reduces search depth for moves that are unlikely to be best.

# 

# 6\. \*\*Quiescence Search\*\*: Extends search in tactical positions to avoid the horizon effect.

# 

# \### Evaluation Function

# 

# The position evaluator considers:

# 

# \- \*\*Material Balance\*\*: Standard piece values with adjustments

# \- \*\*Piece Positioning\*\*: Piece-square tables for positional play

# \- \*\*King Safety\*\*: Pawn shield, castling rights, king exposure

# \- \*\*Pawn Structure\*\*: Doubled, isolated, and passed pawns

# \- \*\*Piece Activity\*\*: Mobility, outposts, open files

# \- \*\*Center Control\*\*: Control of central squares

# \- \*\*Tactical Factors\*\*: Checks, attacks, threats

# \- \*\*Endgame Factors\*\*: King centralization, pawn races

# 

# \### Opening Book

# 

# The opening book system:

# \- Loads master games from PGN databases

# \- Imports ECO opening classifications

# \- Compiles into efficient lookup structure

# \- Selects moves based on frequency (weighted random)

# \- Identifies opening names for display

# 

# \### Endgame Tablebases

# 

# Syzygy tablebase support provides:

# \- Perfect play in 3-7 piece endgames

# \- WDL (Win/Draw/Loss) evaluation

# \- DTZ (Distance to Zero) for optimal play

# \- Fallback to basic endgame knowledge

# 

# ---

# 

# \## 📊 Analysis Tools

# 

# \### Move Classification

# 

# Moves are classified based on evaluation loss:

# 

# | Classification | Eval Loss | Description |

# |---------------|-----------|-------------|

# | Brilliant (!!) | < -0.5 | Finds an unexpected winning move |

# | Great (!) | ≤ 0.1 | Excellent move, near-optimal |

# | Best | ≤ 0.1 | The engine's top choice |

# | Excellent | ≤ 0.3 | Very good move |

# | Good | ≤ 0.3 | Solid, reasonable move |

# | Inaccuracy (?!) | ≤ 1.0 | Slight mistake |

# | Mistake (?) | ≤ 3.0 | Significant error |

# | Blunder (??) | > 3.0 | Serious mistake |

# 

# \### ELO Estimation

# 

# The system estimates playing strength based on:

# \- Move quality distribution

# \- Accuracy score calculation

# \- Mapping to ELO range (400-2000+)

# 

# \### Performance Metrics

# 

# Real-time tracking of:

# \- Nodes searched per move

# \- Search depth achieved

# \- Time per move

# \- Nodes per second (NPS)

# \- Evaluation over time

# 

# \### Visualization

# 

# Matplotlib graphs showing:

# \- Search speed (NPS) progression

# \- Time vs. depth analysis

# \- Nodes vs. depth correlation

# \- Position evaluation timeline

# 

# ---

# 

# \## ⚙️ Configuration

# 

# \### Engine Settings

# 

# Edit `engine/engine.py` to configure:

# 

# ```python

# \# Search depth limits

# max\_depth = 50

# 

# \# Time management

# max\_time = 20.0  # seconds per move

# 

# \# Aspiration window size

# window\_size = 50  # centipawns

# ```

# 

# \### Opening Book

# 

# Configure in `engine/opening\_book/opening\_book.py`:

# 

# ```python

# \# Maximum opening book depth

# max\_ply = 10  # moves per side

# 

# \# Dataset location

# base\_dir = "engine/opening\_book/dataset"

# ```

# 

# \### Tablebases

# 

# Set tablebase path in `engine/endgame/endgame.py`:

# 

# ```python

# tablebase\_path = "engine/tablebases/syzygy"

# ```

# 

# ---

# 

# \## 📦 Requirements

# 

# \### Core Dependencies

# 

# \- \*\*pygame\*\*: GUI and graphics

# \- \*\*python-chess\*\*: Chess logic and move generation

# \- \*\*matplotlib\*\*: Performance visualization

# \- \*\*requests\*\*: Lichess API integration

# 

# \### Optional Components

# 

# \- \*\*Stockfish\*\*: Enhanced analysis engine

# \- \*\*Syzygy Tablebases\*\*: Perfect endgame play

# \- \*\*Opening Database\*\*: Master games in PGN format

# 

# ---

# 

# \## 🤝 Contributing

# 

# Contributions are welcome! Areas for improvement:

# 

# 1\. \*\*Engine Enhancements\*\*:

# &nbsp;  - Neural network evaluation (NNUE)

# &nbsp;  - Better time management

# 

# 2\. \*\*Analysis Features\*\*:

# &nbsp;  - Tactical pattern recognition

# &nbsp;  - Strategic theme identification

# &nbsp;  - Training mode with hints

# 

# 3\. \*\*GUI Improvements\*\*:

# &nbsp;  - Board themes

# &nbsp;  - Piece sets

# &nbsp;  - Sound effects

# &nbsp;  - Online play support

# 

# 4\. \*\*Documentation\*\*:

# &nbsp;  - Code comments

# &nbsp;  - Tutorial videos

# &nbsp;  - Algorithm explanations

# 

# ---

# 

# \## 🐛 Troubleshooting

# 

# \### Game Won't Start

# 

# \- Ensure Python 3.8+ is installed

# \- Install all dependencies: `pip install -r requirements.txt`

# \- Check that pygame initializes: `python -c "import pygame; pygame.init()"`

# 

# \### Engine Not Working

# 

# \- Verify Stockfish path if using external engine

# \- Check `engine/engine.py` for errors

# \- Ensure sufficient memory (minimum 2GB RAM)

# 

# \### Analysis Fails

# 

# \- Check that game files exist in `games/` folder

# \- Verify JSON analysis files are valid

# \- Try re-analyzing: `python run\_analysis.py`

# 

# \### Opening Book Empty

# 

# \- Download Lichess games database

# \- Place PGN files in `engine/opening\_book/dataset/`

# \- Delete `opening\_compiled.pkl` to force rebuild

# 

# \### Tablebases Not Working

# 

# \- Verify files are in `engine/tablebases/syzygy/`

# \- Check file permissions

# \- Ensure enough disk space (6-piece = ~150GB)

# 

# \### Performance Issues

# 

# \- Reduce search depth in settings

# \- Close background applications

# \- Use compiled opening book

# \- Consider disabling real-time analysis display

# 

# ---

# 

# \## 📄 License

# 

# This project is licensed under the MIT License - see LICENSE file for details.

# 

# ---

# 

# \## 👥 Team

# 

# IntelliChess was developed by:

# 

# \- \*\*\[Tooba Nadeem](https://github.com/l232550)\*\* - Co-Developer

# \- \*\*\[Nayab Maryam](https://github.com/NayabMaryam)\*\* - Co-Developer

# \- \*\*\[Your Name]\*\* - Co-Developer

# 

# ---

# 

# \## 🙏 Acknowledgments

# 

# \- \*\*python-chess\*\*: Niklas Fiekas

# \- \*\*Stockfish\*\*: Stockfish developers

# \- \*\*Syzygy Tablebases\*\*: Ronald de Man

# \- \*\*Lichess\*\*: Free online chess platform and API

# \- \*\*Chess.com\*\*: Inspiration for UI design

# 

# ---

# 

# \## 📞 Support

# 

# For issues, questions, or suggestions:

# 

# \- Open an issue on GitHub

# \- Contact: \*\*abdullah2006habib@gmail.com\*\*

# 

# 

# ---

# 

# \## 🔮 Future Plans

# 

# \- \[ ] Neural network evaluation (NNUE)

# \- \[ ] Cloud analysis integration

# \- \[ ] Mobile app version

# \- \[ ] Multiplayer support

# \- \[ ] Tournament mode

# \- \[ ] Puzzle trainer

# \- \[ ] Opening repertoire builder

# \- \[ ] Endgame practice mode

# 

# ---

# 

# \*\*Built with Dedication by \[Tooba Nadeem](https://github.com/l232550), \[Nayab Maryam](https://github.com/NayabMaryam), and team\*\*

# 

# ---

# 

# \*A collaborative chess engine project combining AI, game theory, and passion for chess\*

