from utils import *
from tqdm import tqdm

def calculate_best_move_by_frequency(board_list, engine, color, depth=20, multipv=5):
    best_move_counter = dict()

    for board in tqdm(board_list[:30]):
        top_moves,_ = get_stockfish_top_moves(board, engine, color, depth, multipv)
        for move_dict in top_moves:
            move = move_dict["move"]
            if move in best_move_counter:
                best_move_counter[move] += 1
            else:
                best_move_counter[move] = 1

    best_move_by_frequency = max(best_move_counter, key=best_move_counter.get)
    return best_move_by_frequency
