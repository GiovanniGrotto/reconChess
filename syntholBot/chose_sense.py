from utils import *
import numpy as np

PIECEVALUE = {"r": 1, "b": 0.7, "n": 0.7, "q": 1.2, 'k': 1.2, "p": 0.3, }


def stockfish_tile_weight(board, engine, stockfish_board, color, depth=20, multipv=5):
    top_moves, top_moves_sequence = get_stockfish_top_moves(board, engine, color)
    for move_dict in top_moves:
        move = move_dict["move"]
        start_square = move.from_square
        end_square = move.to_square
        # Add values on weight arrays for left piece and arrival tile
        stockfish_board[start_square] += 3
        stockfish_board[end_square] += 5
    return stockfish_board, top_moves_sequence


def count_pieces_from_possible_boards(board_list, mycolor):
    piece_val_board = np.zeros((8, 8), dtype=int)
    for board in board_list:

        # Iterate over all squares on the board
        for square in chess.SQUARES:
            piece = board.piece_at(square)

            if piece is not None and piece.color != mycolor:
                # Get the row and column indices for the square
                row = 7 - chess.square_rank(square)
                col = chess.square_file(square)

                # Increment the count for the corresponding square
                piece_val_board[row, col] += PIECEVALUE[piece.symbol().lower()]
    # Find the maximum value in the array
    max_value = np.max(piece_val_board)
    # Replace every cell with the maximum value to 0
    piece_val_board[piece_val_board >= (max_value * 0.75)] = 0
    return np.flip(piece_val_board)


def count_piece_landing_on_square(board_list, sqare_list):
    piece_val_board = np.zeros((8, 8), dtype=float)

    for board in board_list:
        for square in sqare_list:
            row = 7 - chess.square_rank(square)
            col = chess.square_file(square)
            piece = board.piece_at(square)
            if piece:
                piece_val_board[row, col] += PIECEVALUE[piece.symbol().lower()]

    return np.flip(piece_val_board)
