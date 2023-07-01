import chess
import numpy as np
from scipy import signal


def convert_board_to_json(board_list):
    result = []
    for board in board_list:
        for row in range(8):
            for col in range(8):
                square = chess.square(col, row)
                piece = board.piece_at(square)

                position_data = {
                    "row": row,
                    "col": col,
                    "images": []
                }

                existing_position = next((item for item in result if item['row'] == row and item['col'] == col),
                                         None)
                if existing_position:
                    position_data['images'] = existing_position['images']

                if piece is not None:
                    color = "B" if piece.color == chess.BLACK else "W"
                    piece_type = piece.symbol().upper()
                    image_path = f"images/{color}{piece_type}.png"
                else:
                    image_path = f"images/placeholder.png"

                if image_path not in position_data['images']:
                    position_data['images'].append(image_path)

                if not existing_position:
                    result.append(position_data)
    return result


def calculate_diagonal_squares(square1, square2):
    diagonal_squares = []

    row1, col1 = square1 // 8, square1 % 8
    row2, col2 = square2 // 8, square2 % 8

    if row1 < row2 and col1 > col2:  # up left
        orientation = 1
        direction = -1
    elif row1 < row2 and col2 > col1:  # up right
        orientation = 1
        direction = +1
    elif row1 > row2 and col1 > col2:  # down left
        orientation = -1
        direction = 1
    elif row1 > row2 and col2 > col1:  # down right
        orientation = -1
        direction = -1

    # Calculate the squares on the diagonal
    current_square = square1
    while current_square != square2:
        current_square += (8 + direction) * orientation
        diagonal_squares.append(current_square)

    return diagonal_squares[:-1]


def calculate_straight_squares(square1, square2):
    middle_squares = []

    # Determine if squares are on the same file or rank
    if chess.square_file(square1) == chess.square_file(square2):
        # Squares are on the same file
        rank1, rank2 = chess.square_rank(square1), chess.square_rank(square2)

        for rank in range(min(rank1, rank2) + 1, max(rank1, rank2)):
            middle_squares.append(chess.square(chess.square_file(square1), rank))

    elif chess.square_rank(square1) == chess.square_rank(square2):
        # Squares are on the same rank
        file1, file2 = chess.square_file(square1), chess.square_file(square2)

        for file in range(min(file1, file2) + 1, max(file1, file2)):
            middle_squares.append(chess.square(file, chess.square_rank(square1)))

    return middle_squares


def get_stockfish_top_moves(board, engine, color, depth=20, multipv=5, file=None):
    if not board.is_valid():
        result = find_attacking_enemy_king_moves(board)
        # ora ritorniamo 10000 a caso ma andrebbe controllato il verso, cioè per noi è 100k ma se è lui ad avere il matto è -100k
        return [{"move": move, "score": 100000} for move in result]
    try:
        top = []
        board.turn = color
        board.clear_stack()
        result = engine.analyse(board, chess.engine.Limit(depth=depth), multipv=multipv)
        for item in result:
            move = item["pv"][0]
            score = item["score"].relative
            if hasattr(score, "cp"):
                score = score.cp
            elif hasattr(score, "moves"):
                score = 1000000 / score.moves
            top.append({"move": move, "score": score})
        return top, {board.fen(): [x["pv"] for x in result]}
    except (chess.engine.EngineError, chess.engine.EngineTerminatedError) as e:
        print('Engine bad state at "{}"'.format(board.fen()))
        #engine = chess.engine.SimpleEngine.popen_uci(elf.stockfish_path)
    except AttributeError as e:
        pass


def find_attacking_enemy_king_moves(board):
    # Find the square of the enemy king
    enemy_king_square = board.king(not board.turn)
    # Generate all legal moves for your pieces
    pseudo_legal_moves = board.pseudo_legal_moves

    # Filter moves that attack the enemy king's square
    attacking_moves = []
    for move in pseudo_legal_moves:
        if move.to_square == enemy_king_square:
            attacking_moves.append(move)

    return attacking_moves


def sum_array(to_sum_array):
    kernel = np.ones((3, 3))
    padded_res = np.zeros_like(to_sum_array)
    padded_res[1:-1, 1:-1] = to_sum_array[1:7, 1:7]
    res = signal.convolve2d(padded_res, kernel, boundary='fill', mode='same')
    padded_res = np.zeros_like(res)
    padded_res[1:-1, 1:-1] = res[1:7, 1:7]
    return padded_res.flatten()
