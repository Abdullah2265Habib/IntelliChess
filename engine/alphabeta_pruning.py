import math
import chess # for is_game_over() and legal_moves
from engine.position_evaluator import ChessPositionEvaluator # for evaluate_position()

evaluator = ChessPositionEvaluator() # created an instance of the evaluator

def minimax_with_alphabeta(position, depth, alpha, beta, maximizingPlayer): 
    ''' minimax with alpha-beta pruning '''
    if depth == 0 or position.is_game_over(): # base case
        return evaluator.evaluate_position(position)

    if maximizingPlayer:
        maxEval = -math.inf
        for move in position.legal_moves:
            position.push(move)
            eval = minimax_with_alphabeta(position, depth - 1, alpha, beta, False) #recursive call
            position.pop()

            maxEval = max(maxEval, eval)
            alpha = max(alpha, eval)
            
            if alpha >= beta: # pruning occurs
                break

        return maxEval

    else:
        minEval = math.inf
        for move in position.legal_moves:
            position.push(move)
            eval = minimax_with_alphabeta(position, depth - 1, alpha, beta, True) #recursive call
            position.pop()

            minEval = min(minEval, eval)
            beta = min(beta, eval)

            if alpha >= beta: # pruning occurs
                break

        return minEval


def return_bestMove_and_bestValue(position, depth): 
    ''' helper function for minimax_with_alphabeta(); returns the best move and best value for the current position '''
    best_move = None
    best_value = -math.inf

    alpha = -math.inf
    beta = math.inf

    for move in position.legal_moves:
        position.push(move)
        eval = minimax_with_alphabeta(position, depth - 1, alpha, beta, False) # call minimax for the opponent
        position.pop()

        if eval > best_value: # update best move and value
            best_value = eval
            best_move = move

        alpha = max(alpha, eval) # update alpha

    return best_move, best_value
