import chess.pgn
import datetime
import os

def saveGamePGN(board):
    game = chess.pgn.Game()
    node = game
    for move in board.move_stack:
        node = node.add_variation(move)
    game.headers["Event"] = "Bullet: 1 min"
    game.headers["Date"] = datetime.datetime.now().strftime("%Y.%m.%d")
    game.headers["Result"] = board.result()

    pgn_string = str(game)

    os.makedirs("games", exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"games/{timestamp}.txt"

    with open(filename, "w") as file:
        file.write(pgn_string)

    print(f"[INFO] Game saved to {filename}")
