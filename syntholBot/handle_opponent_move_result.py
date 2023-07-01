# Function to sense opponent move
def filter_boards_by_opponent_piece(board_list, square, my_color):
    opponent_color = not my_color
    filtered_boards = []

    for board in board_list:
        piece = board.piece_at(square)
        if piece is not None and piece.color == opponent_color:
            filtered_boards.append(board)

    return filtered_boards