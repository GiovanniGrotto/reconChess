#!/bin/sh
import chess.engine
from reconchess import *
import os
import json
import time
from tqdm import tqdm
from handle_opponent_move_result import *
from handle_move_result import *
from hande_sense_result import *
from chose_sense import *
from utils import *
from choose_move import *

STOCKFISH_ENV_VAR = 'STOCKFISH_EXECUTABLE'
# depth of stockfish analysis
DEPTH = 23
# number of top moves recived from stockfish
MULTIPV = 5

# Linux
# os.environ[STOCKFISH_ENV_VAR] = "/media/joseph/TOSHIBA EXT/SynthBot/stockfish"

# Windows
# os.environ[STOCKFISH_ENV_VAR] = "/Python39/Lib/site-packages/stockfish/stockfish_15_x64_avx2.exe"
os.environ[STOCKFISH_ENV_VAR] = "C:/Users/giova/OneDrive/Desktop/SynthBot/stockfish_15.1_win_x64_avx2/stockfish-windows-2022-x86-64-avx2.exe"


class SyntholBot(Player):
    """
    TroutBot uses the Stockfish chess engine to choose moves. In order to run TroutBot you'll need to download
    Stockfish from https://stockfishchess.org/download/ and create an environment variable called STOCKFISH_EXECUTABLE
    that is the path to the downloaded Stockfish executable.
    """

    def __init__(self):
        self.board_list = []
        self.previous_board_list = []
        self.move_cache = dict()
        self.color = None
        self.remaining_time = 900

        self.possible_boards = []
        self.boards_lenghts = []
        self.check_squares = []

        # make sure stockfish environment variable exists
        if STOCKFISH_ENV_VAR not in os.environ:
            raise KeyError(
                'TroutBot requires an environment variable called "{}" pointing to the Stockfish executable'.format(
                    STOCKFISH_ENV_VAR))

        # make sure there is actually a file
        stockfish_path = os.environ[STOCKFISH_ENV_VAR]
        if not os.path.exists(stockfish_path):
            raise ValueError('No stockfish executable found at "{}"'.format(stockfish_path))
        # initialize the stockfish engine
        self.engine = chess.engine.SimpleEngine.popen_uci(stockfish_path, setpgrp=True)
        self.engine.configure({'Threads': 4, 'Use NNUE': True, "Hash": 1024})  # 'Use NNUE':True "Hash": 32

    def handle_game_start(self, color: Color, board: chess.Board, opponent_name: str):
        self.board_list.append(board)
        self.color = color
        day = time.strftime(' %Y-%m-%d_%H-%M-%S', time.localtime(time.time()))
        file_name = "SyntholFish_" + opponent_name + str(day) + ".txt"

    def handle_opponent_move_result(self, captured_my_piece: bool, capture_square: Optional[Square]):
        if len(self.board_list) == 0:
            print()
        if not (self.board_list[0].fullmove_number == 1 and self.color):
            self.previous_board_list = self.board_list.copy()
            self.board_list, attack_board_list = generate_possible_boards(self.board_list, self.color) # genero già qui le scacchiere in modo tale che
            # poi posso controllare e filtrare quelle che non hanno mangiato nello square come invece è successo
            if captured_my_piece:
                self.board_list = filter_boards_by_opponent_piece(attack_board_list, capture_square, self.color)

    def choose_sense(self, sense_actions: List[Square], move_actions: List[chess.Move], seconds_left: float) -> \
            Optional[Square]:
        # If it's the first turn, and we are white, skip
        if len(self.board_list) == 0:
            print()
        if self.board_list[0].fullmove_number == 1 and self.color:
            self.board_list[0].fullmove_number += 1
            return None
        print()
        self.remaining_time = seconds_left

        # Keep weights for every analyzed Stockfish move
        stockfish_board = np.zeros(64)

        to_sum_array = np.zeros((8, 8))

        if len(self.previous_board_list) > 300:
            print("Vado a escludere più pezzi possibile")
            to_sum_array = count_pieces_from_possible_boards(self.board_list, self.color)
        else:
            for board in tqdm(self.previous_board_list[0:30]):
                to_sum_array, move_sequence = stockfish_tile_weight(board, self.engine, stockfish_board, not self.color)
                to_sum_array = to_sum_array.reshape(8, 8)
                self.move_cache.update(move_sequence)

        res = sum_array(to_sum_array)
        best_square = np.argwhere(res == np.amax(res)).flatten()
        if len(best_square) > 1:
            print("Pareggio sui punteggi stockfish")
            res = sum_array(count_piece_landing_on_square(self.board_list, list(best_square)))
            best_square = np.argwhere(res == np.amax(res)).flatten()
        to_sense = int(best_square[0])
        print(f"Scanning square number: {to_sense}")
        self.check_squares.append(to_sense)
        return to_sense

    def handle_sense_result(self, sense_result: List[Tuple[Square, Optional[chess.Piece]]]):
        self.board_list = filter_possible_boards(self.board_list, sense_result)
        self.possible_boards.append(convert_board_to_json(self.board_list))
        self.boards_lenghts.append(len(self.board_list))
        print(f"Considering {len(self.board_list)} possible board state after filter")

    def choose_move(self, move_actions: List[chess.Move], seconds_left: float) -> Optional[chess.Move]:
        if len(self.board_list) == 0:
            enemy_king_square = self.board[0].king(not self.color)
            if enemy_king_square:
                # if there are any ally pieces that can take king, execute one of those moves
                enemy_king_attackers = self.board[0].attackers(self.color, enemy_king_square)
                if enemy_king_attackers:
                    attacker_square = enemy_king_attackers.pop()
                    move = chess.Move(attacker_square, enemy_king_square)
                    return move
        # otherwise, try to move with the stockfish chess engine
        if len(self.board_list) > 300:
            top_move = calculate_best_move_by_frequency(self.board_list, self.engine, self.color, multipv=1)
        else:
            top_move = calculate_best_move_by_frequency(self.board_list, self.engine, self.color)
        print(f"best found move: {top_move}")
        print()
        return top_move

    def handle_move_result(self, requested_move: Optional[chess.Move], taken_move: Optional[chess.Move],
                           captured_opponent_piece: bool, capture_square: Optional[Square]):

        # If the move is not the same we requested we keep only the boards that had an enemy
        # piece on the square where we stopped
        if taken_move != requested_move and captured_opponent_piece:
            self.board_list = filter_boards_by_piece_color(self.board_list, taken_move.to_square, not self.color)

        # Mi viene in mente solo una mossa illegale di pedone che cerca di mangiare e non trova nulla,
        # al che sappiamo che la cella dove andare è vuota
        elif taken_move != requested_move and not captured_opponent_piece:
            board_state = [(requested_move.to_square, None)] # indico che la casella di arrivo è vuota
            self.board_list = filter_possible_boards(self.board_list, board_state)

        # The move was successfull, so there is for sure no piece in the squares crossed by our piece,
        # we update board_list with this new info
        else:
            # trova le celle percorse e usa filter dando in input le celle e None come piece su ogni cella
            moved_piece = self.board_list[0].piece_at(requested_move.from_square)
            traveled_squares = calculate_traveled_squares(moved_piece, taken_move)
            if traveled_squares:
                board_state = [(x, None) for x in traveled_squares]
                self.board_list = filter_possible_boards(self.board_list, board_state)

        if taken_move:
            self.board_list = push_move_to_possible_boards(taken_move, self.board_list)
        print(json.dumps({'check': self.check_squares, 'positions': self.possible_boards, 'possibilities': self.boards_lenghts}))
        print(f"Remainign time: {self.remaining_time}")


    def handle_game_end(self, winner_color: Optional[Color], win_reason: Optional[WinReason],
                        game_history: GameHistory):
        print(win_reason)
        try:
            # if the engine is already terminated then this call will throw an exception
            self.engine.quit()
        except chess.engine.EngineTerminatedError:
            pass
