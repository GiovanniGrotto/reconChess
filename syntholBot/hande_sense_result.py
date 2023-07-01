from typing import Tuple, List, Any

import chess
from tqdm import tqdm

def generate_possible_boards(board_list: list, mycolor):
    possible_board_list = []
    attack_board_list = []
    for board in board_list:
        for move in board.pseudo_legal_moves:
            if not board.piece_at(move.to_square) or (board.piece_at(move.to_square) and board.piece_at(move.to_square).color != mycolor):
                new_board = board.copy()
                new_board.push(move)
                possible_board_list.append(new_board)
            else:
                new_board = board.copy()
                new_board.push(move)
                attack_board_list.append(new_board)
    return possible_board_list, attack_board_list

def generate_possible_boards_with_eval(board_list: list, mycolor, engine, depth=10):
    possible_board_list = []
    attack_board_list = []
    for board in board_list:
        for move in board.pseudo_legal_moves:
            if not board.piece_at(move.to_square) or (board.piece_at(move.to_square) and board.piece_at(move.to_square).color != mycolor):
                new_board = board.copy()
                new_board.push(move)
                result = engine.analyse(board, chess.engine.Limit(depth=depth))
                possible_board_list.append(new_board)
            else:
                new_board = board.copy()
                new_board.push(move)
                attack_board_list.append(new_board)
    return possible_board_list, attack_board_list


# Filter the board_list based on the given board_info dictionary
def filter_possible_boards(board_list: list, board_state) -> list:
    filtered_board_list = []

    for board in board_list:
        matches = True
        for cell, piece in board_state:
            # Elimina se uno e None e l'altro no o se nessuno è None ma sono diversi
            if (board.piece_at(cell) is not None and piece is None) or (
                    board.piece_at(cell) is None and piece is not None) or (
                    board.piece_at(cell) is not None and board.piece_at(cell).symbol() != piece.symbol()):
                matches = False
                break
        if matches:
            filtered_board_list.append(board)

    return filtered_board_list
