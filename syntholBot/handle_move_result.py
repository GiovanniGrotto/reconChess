from utils import *


# Function to handle move result
def filter_boards_by_piece_color(board_list, square, color):
    filtered_boards = []

    for board in board_list:
        piece_at_square = board.piece_at(square)

        if piece_at_square is not None and piece_at_square.color == color:
            filtered_boards.append(board)

    return filtered_boards


# Push a specific move in all the boards given
def push_move_to_possible_boards(move: chess.Move, board_list: list) -> list:
    new_board_list = []
    for board in board_list:  # la mossa eseguita potrebbe essere illegale in alcune board, tuttavia è stata eseguita con successo quindi escudiamo quelle scacchiere
        try:
            board.push(move)
            new_board_list.append(board)
        except Exception:
            print("Ho trovato una chessboard brutta")
    return new_board_list


def calculate_traveled_squares(piece, move):
    start_square = move.from_square
    end_square = move.to_square
    piece = piece.symbol().lower()

    rank_diff = abs(start_square // 8 - end_square // 8)
    file_diff = abs(start_square % 8 - end_square % 8)

    if piece == 'p':
        if abs(start_square - end_square) > 8:
            direction = 1 if end_square > start_square else -1
            return [start_square + (8 * direction)]
    elif rank_diff == file_diff and (piece == 'b' or piece == 'q'):
        return calculate_diagonal_squares(start_square, end_square)
    elif rank_diff != file_diff and (piece == 'r' or piece == 'q'):
        return calculate_straight_squares(start_square, end_square)
    elif piece == 'n' or 'k':
        return []
    else:
        return Exception
