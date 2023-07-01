import chess.engine
import random
from reconchess import *
import os
import numpy as np
import time


STOCKFISH_ENV_VAR = 'STOCKFISH_EXECUTABLE'

#depth of stockfish analysis
DEPTH = 20

#Dictionary which explains every piece weight
pieceValue = {"r":1,"R":1,"b":0.7,"B":0.7,"n":0.7,"N":0.7,"q":1.2,"Q":1.2,'k':1.2,"K":1.2,"p":0.3,"P":0.3}

class TroutBot(Player):
    """
    TroutBot uses the Stockfish chess engine to choose moves. In order to run TroutBot you'll need to download
    Stockfish from https://stockfishchess.org/download/ and create an environment variable called STOCKFISH_EXECUTABLE
    that is the path to the downloaded Stockfish executable.
    """

    def __init__(self):
        self.board = None
        self.color = None
        self.my_piece_captured_square = None

        #Set of top 5 opponent's moves
        self.top5Move = set()

        #Keep weights for every analyzed Stockfish move
        self.stockfishArray = np.zeros(64)

        #Keep weights for every legal move on the board
        self.pieceArray = np.zeros(64)

        #Sums of every 3x3 around every tile, based on stockfishArray
        self.stockfishArraySum = np.zeros(64)

        #Sums of every 3x3 around every tile, based on pieceArray
        self.pieceArraySum = np.zeros(64)

        #Track complete or partial information
        self.uncertanty = False

        #Linux
        #os.environ[STOCKFISH_ENV_VAR]="/media/joseph/TOSHIBA EXT/SynthBot/stockfish"

        #Windows
        os.environ[STOCKFISH_ENV_VAR]="/Python39/Lib/site-packages/stockfish/stockfish_15_x64_avx2.exe"

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

    def handle_game_start(self, color: Color, board: chess.Board, opponent_name: str):
        self.board = board
        self.color = color

    def handle_opponent_move_result(self, captured_my_piece: bool, capture_square: Optional[Square]):
        # if the opponent captured our piece, remove it from our board and save the square.
        if captured_my_piece:
            self.board.remove_piece_at(capture_square)
            self.my_piece_captured_square = capture_square
            # found_moves = False
            # from_tile = ""
            # for move in self.board.legal_moves:
            #     if str(move)[2:4] == self.intToNotation(capture_square):
            #         if found_moves:
            #             print("Aumento sensing = più mosse " + str(capture_square))
            #             self.stockfishArray[capture_square]+=100
            #             return
            #         from_tile = str(move)[0:2]
            #         found_moves = True
            # if found_moves:
            #     print("Sappiamo la mossa esatta " + from_tile + self.intToNotation(capture_square))
            #     self.board.push(chess.Move.from_uci(from_tile + self.intToNotation(capture_square)))


    def choose_sense(self, sense_actions: List[Square], move_actions: List[chess.Move], seconds_left: float) -> \
            Optional[Square]:
        #If it's the first turn and we are white, skip
        if self.board.fullmove_number == 1 and self.color: return 0

        #Fill every matrix with zeros
        self.stockfishArray.fill(0)
        self.pieceArray.fill(0)
        self.stockfishArraySum.fill(0)
        self.pieceArraySum.fill(0)

        # If one piece as been captured be sure to check that square on sensing
        if self.my_piece_captured_square != -1:
            self.stockfishArray[self.my_piece_captured_square]+=100
            self.my_piece_captured_square = -1

        #Calculate and print Stockfish value
        self.stockfish_tile_weight()
        # print("STOCKFISH VALUE MATRIX")
        # self.print_array_as_board(self.stockfishArray)

        #Calculate and print piece value
        self.tile_weight_by_piece()
        # print("PIECE VALUE MATRIX:")
        # self.print_array_as_board(self.pieceArray)

        #Fulfill array for every tile
        toSense = self.select_tile()
        print(toSense)

        self.sensed_tile = toSense[0]
        return toSense[0]


    def handle_sense_result(self, sense_result: List[Tuple[Square, Optional[chess.Piece]]]):
        if self.board.fullmove_number == 1 and self.color: return

        move = ""
        # Create a copy of the board
        tmp_board = self.board.copy()

        #Add the pieces in the sense result to our board and compare the two board differences
        from_tile, to_tile, found_piece = self.fill_tmp_board(tmp_board, sense_result)

        # Found both from where e to where the piece was from
        if not from_tile == -1 and not to_tile == -1:
            move = self.intToNotation(from_tile) + self.intToNotation(to_tile)

        # Found just where the piece arrived, not where it came from
        elif from_tile == -1 and to_tile !=-1:
            print("?" + self.intToNotation(to_tile))
            move = self.get_move_to_tile(tmp_board, to_tile, found_piece)

        # Found just where the piece came from, not where arrived
        elif to_tile == -1 and from_tile !=-1:
            print(self.intToNotation(from_tile) + "?")
            moves_from_tile = self.get_moves_from_tile(from_tile)
            move = self.get_best_move(moves_from_tile)

        # Found nothing
        else:
            print("TOP MOVE o PANIC")
            moves = self.top5Move
            self.top5Move = list(self.delete_checked_moves(self.top5Move))
            self.uncertanty = True
            print(self.top5Move)
            move = self.top5Move[0]
            print("ORA IMPAZZISCE")

        print(move)
        if move != None : self.board.push(chess.Move.from_uci(move))

    def choose_move(self, move_actions: List[chess.Move], seconds_left: float) -> Optional[chess.Move]:
        # if we might be able to take the king, try to
        self.board.fullmove_number+=1
        enemy_king_square = self.board.king(not self.color)
        if enemy_king_square:
            # if there are any ally pieces that can take king, execute one of those moves
            enemy_king_attackers = self.board.attackers(self.color, enemy_king_square)
            if enemy_king_attackers:
                attacker_square = enemy_king_attackers.pop()
                return chess.Move(attacker_square, enemy_king_square)
        
        # durante il sensing non ho trovato nulla, devo gestire l'incertezza con la matrice
        if  self.uncertanty : self.get_best_response_move(self.top5Move)

        # otherwise, try to move with the stockfish chess engine
        try:
            self.board.turn = self.color
            self.board.clear_stack()
            result = self.engine.play(self.board, chess.engine.Limit(time=0.5))
            return result.move
        except chess.engine.EngineTerminatedError:
            print('Stockfish Engine died')
        except chess.engine.EngineError:
            print('Stockfish Engine bad state at "{}"'.format(self.board.fen()))

        # if all else fails, pass
        return None

    def handle_move_result(self, requested_move: Optional[chess.Move], taken_move: Optional[chess.Move],
                           captured_opponent_piece: bool, capture_square: Optional[Square]):
        # if a move was executed, apply it to our board
        self.top5Move.clear()
        if taken_move is not None:
            self.board.push(taken_move)

    def handle_game_end(self, winner_color: Optional[Color], win_reason: Optional[WinReason],
                        game_history: GameHistory):
        try:
            # if the engine is already terminated then this call will throw an exception
            self.engine.quit()
        except chess.engine.EngineTerminatedError:
            pass

####################################### CHOOSE SENSE FUNCTIONS #######################################


    #convert from "a8" to its index in an array
    def notationToInt(self, notation):
        tile = (ord(notation[0])-97) + (((int(notation[1]))-1)*8)
        #print(tile)
        return tile

    #convert from index to string of position 8->"a7"
    def intToNotation(self, value):
        x1 = int((value % 8) + 97)
        tile = str(chr(x1)) + str(int(value/8)+1)
        #print(tile)
        return tile

    #util for matrix printing
    def print_array_as_board(self, arr):
        matrix = np.reshape(arr, (8, 8))
        matrix = np.flipud(matrix)
        print(matrix)
        print()

    #Assign 5 points to Stockfish suggested moves' tiles
    def stockfish_tile_weight(self):
        #Set board position for engine and get top moves
        self.top5Move = set(self.top5Move)
        analysis = self.engine.analyse(self.board, chess.engine.Limit(depth=DEPTH), multipv=5)
        top = [move["pv"][0] for move in analysis]
        for t in top:
            move = str(t)
            #Save analyzed moves
            self.top5Move.add(move)
            print(move + ',',end='')
            fromTile = move[0:2]
            toTile = move[2:4]
            #Add values on weight arrays for left piece and arrival tile
            self.pieceArray[self.notationToInt(fromTile)] += 1
            self.stockfishArray[self.notationToInt(toTile)] += 5
        print()

    #Fulfill with weigth of piece arriving in a tile
    def count_piece_arriving(self, fromTile, toTile):
        #Getting piece type and its value
        piece = str(self.board.piece_at(chess.parse_square(fromTile)))
        pieceVal = pieceValue[piece]
        #Fulfilling with piece value on arriving tile
        self.pieceArray[self.notationToInt(toTile)] += pieceVal

    #Fulfill with weigth of piece leaving a tile
    def count_piece_leaving(self, fromTile, alreadyLeaved):
        #Count only new arriving tiles
        if not fromTile in alreadyLeaved:
            #Getting piece type and its value
            piece = str(self.board.piece_at(chess.parse_square(fromTile)))
            pieceVal = pieceValue[piece]
            #Fulfilling with piece value on starting tile
            self.pieceArray[self.notationToInt(fromTile)] += pieceVal
            #Set as already counted tile
            alreadyLeaved.add(fromTile)

    #Assign points based on how many pieces could end up on every tile
    def tile_weight_by_piece(self):
        alreadyLeaved = set()
        for m in self.board.legal_moves:
            move = str(chess.Move.from_uci(m.uci()))
            fromTile = move[0:2]
            toTile = move[2:4]
            self.count_piece_arriving(fromTile, toTile)
            self.count_piece_leaving(fromTile, alreadyLeaved)


    #Assign a value to a tile based on its 3x3 square
    def calculate_tile_value(self, arr, arrTo, i):
        arrTo[i] = arr[i] + arr[i-1] + arr[i+1] + arr[i-8] + arr[i+8] + arr[i-7] + arr[i+7] + arr[i-9] + arr[i+9]
        return arrTo[i]

    #Find heaviest tile in array
    def get_heaviest_tiles(self, fromArr, toArr):
        tiles = set()
        maxVal = -1
        for i in range(9,55):
            #Not evaluating border tiles
            if i%8 == 0 or i%8 == 7: continue
            #Calculating 3x3 square value
            val = self.calculate_tile_value(fromArr, toArr, i)
            #Adding for draw situations
            if(val == maxVal):
                tiles.add(i)
            #Adding only this tile if it is the best until now
            if(val > maxVal):
                maxVal = val
                tiles.clear()
                tiles.add(i)
        return tiles, maxVal

    #First gets heaviest tile by Stockfish, in case of draw it is chosen by PieceArray
    def select_tile(self):
        maxVal = -1
        tiles,_ = self.get_heaviest_tiles(self.stockfishArray, self.stockfishArraySum)
        #If there is a draw situation, use PieceArray
        if(len(tiles) > 1):
            #Calculate value for every tile on board
            for t in tiles:
                val = self.calculate_tile_value(self.pieceArray, self.pieceArraySum, t)
                if(val > maxVal):
                    maxVal = val
                    tile = t
        else:
            tile = list(tiles)[0]
        return tile, self.intToNotation(tile)

####################################### MANAGE SENSE FUNCTIONS #######################################


    # Update tmp_board with new piece from sensing and spot the difference with self.board
    def fill_tmp_board(self, tmp_board, sense_result):
        for square, piece in sense_result:
            tmp_board.set_piece_at(square, piece)
        print(self.board)
        print()
        print(tmp_board)
        print()
        from_tile = -1
        to_tile = -1
        found_piece = tmp_board.piece_at(0)
        for tile in range(0, 64):
            old_piece = self.board.piece_at(tile)
            new_piece = tmp_board.piece_at(tile)
            if new_piece != old_piece:
                found_piece = new_piece
                if new_piece == None:
                    from_tile = tile
                else:
                    to_tile = tile
        return from_tile, to_tile, found_piece

    # Getting a piece and the tile where it is return where it came from
    def get_move_to_tile(self, tmp_board, to_tile, found_piece):
        for tile in range(0, 64):
            new_piece = tmp_board.piece_at(tile)
            if found_piece == new_piece and tile != to_tile:
                print("Trovata partenza " + str(tile))
                move = self.intToNotation(tile) + self.intToNotation(to_tile)
                if self.board.is_legal(chess.Move.from_uci(move)):
                    return move
        self.board.set_piece_at(to_tile, found_piece)

    # Getting a tile gives a list of all the moves arriving in that tile
    def get_moves_from_tile(self, from_tile):
        moves_from_tile = []
        for move in self.board.legal_moves:
            if str(move)[0:2] == self.intToNotation(from_tile) and not self.checktile(self.notationToInt(str(move)[2:4]), self.sensed_tile):
                moves_from_tile.append(str(move))
        return moves_from_tile

    # Getting a list of moves, evaluate and return the best one
    def get_best_move(self, moves_from_tile):
        max_eval = -9999
        best_move = ""
        for move in moves_from_tile:
            self.board.push(chess.Move.from_uci(move))
            e = self.engine.analyse(self.board, chess.engine.Limit(depth=DEPTH))["score"]
            if self.color == True:
                print("Score per il nero, con mossa " + str(move) + " : " + str(e.black()))
                e = int(str(e.black()))
            else:
                print("Score per il bianco: " + str(e.white()))
                e = int(str(e.white()))
            if e > max_eval:
                max_eval = e
                best_move = move
            self.board.pop()
        return best_move

    #controlla se una casella era contenuta in quelle sensed
    def checktile(self, tile, sensedTile):
        if tile==sensedTile or tile==sensedTile-1 or tile==sensedTile+1 or tile==sensedTile-7 or tile==sensedTile+7 or tile==sensedTile-9 or tile==sensedTile+9 or tile==sensedTile-8 or tile==sensedTile+8:
            return True
        return False

    # Given a list of moves delete all the move that was on sensed tile
    def delete_checked_moves(self, moves):
        print(moves)
        for t in moves.copy():
            from_tile = self.notationToInt(t[0:2])
            to_tile = self.notationToInt(t[2:4])
            if self.checktile(from_tile, self.sensed_tile) or self.checktile(to_tile, self.sensed_tile):
                print("Eliminating:"+ t)
                moves.remove(t)
            else: print(t)
        return moves

    # Given a list of moves generate the best top 5 response for every move
    # Initialize matrix and dict_of_top_moves
    def generatePossibleMoves(self, matrix, moves):
        dict_of_moves = {}
        return matrix, moves, dict_of_moves

    # Fill the matrix and calculate the maxmin value, corresponding at the best move on average
    def fullFillMatrix(self, matrix, moves, dictOfMoves):
        return

    #given a list of moves create a matrix and calculate minmax value, so the best average move in response 
    def evaluation_matrix(self, list_of_move):
        n = len(list_of_move)
        matrix = np.empty((5*n, n))
        matrix.fill(np.nan)
        print(matrix)
        print(list_of_move)
        matrix, moves, dict_of_moves = self.generatePossibleMoves(matrix, list_of_move)
        print(matrix)
        matrix = self.fullFillMatrix(matrix, moves, dict_of_moves)
        return

    # Given a list of moves, return the best move as response
    def get_best_response_move(self, moves):
        if len(moves) <= 0:
            print("nessuna mossa rimasta vado random")
            return

        if len(moves) == 1:
            self.board.push(chess.Move.from_uci(list(moves)[0]))
            move = self.engine.play(self.board, chess.engine.Limit(depth=DEPTH))
            self.board.pop()
            print("Una sola mossa rimasta")
            print(move)
            return move
        else :
            print("evaluating best move between " + str(len(moves)) + " board")
            self.evaluation_matrix(moves)
            return
    
    
