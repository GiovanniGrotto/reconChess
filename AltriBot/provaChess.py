import time
import numpy as np
import chess
from stockfish import Stockfish
stockfish = Stockfish(path="/Python39/Lib/site-packages/stockfish/stockfish_15_x64_avx2.exe",depth=18)

#fenTOCheck = r1bqr1k1/pp1pbppp/2pn4/8/3P4/2N5/PPP2PPP/R1BQRBK1 b - - 4 11
#r1bqk2r/p1ppppbp/n5pn/1p6/8/1PP2N2/P2PPPPP/RNBQKB1R w KQkq - 1 6 con mossa mia h2h3 genera 3 board se null
pieceValue = {"r":1,"R":1,"b":0.7,"B":0.7,"n":0.7,"N":0.7,"q":1.2,"Q":1.2,'k':1.2,"K":1.2,"p":0.3,"P":0.3}
top5Move = set()
stockfishArray = np.zeros(64)
pieceArray = np.zeros(64)
sumWeight = np.zeros(64)
singleTileWeightPiece = np.zeros(64)
singleTileWeightStockfish = np.zeros(64)
dict = {}
fen = "r1bqk2r/p1ppppbp/n5pn/1p6/8/1PP2N2/P2PPPPP/RNBQKB1R w KQkq - 1 6"
#fen = input()
board = chess.Board(fen)

#print an array of 64 as a board, the top left tile is 0-indexed
def printArrayAsBoard(arr):
    matrix = np.reshape(arr, (8, 8))
    print(matrix)
    print()

#convert from "a8" to its index in an array
def notationToInt(notation):
    tile = (ord(notation[0])-96) + ((8-int(notation[1]))*8)-1
    #print(tile)
    return tile

#convert from index to string of position 8->"a7"
def intToNotation(value):
    x1 = int((value % 8) + 97)
    tile = str(chr(x1)) + str(8-int(value/8))
    #print(tile)
    return tile

#give a value to the tile based on how many pieces could end up there
def tileWeightByPiece():
    alreadyLeaved = set()
    for m in board.legal_moves:
        move = str(chess.Move.from_uci(m.uci()))
        fromTile = move[0:2]
        toTile = move[2:4]
        countPieceArriving(fromTile, toTile)
        countPieceLeaving(fromTile, alreadyLeaved)

#fullfill with value of piece arriving in that tile
def countPieceArriving(fromTile, toTile):
    piece = str(board.piece_at(chess.parse_square(fromTile)))
    pieceVal = pieceValue[piece]
    pieceArray[notationToInt(toTile)] += pieceVal

#fullfill with value of piece leaving that tile
def countPieceLeaving(fromTile, alreadyLeaved):
    #the tile is not already couted
    if not fromTile in alreadyLeaved:
        piece = str(board.piece_at(chess.parse_square(fromTile)))
        pieceVal = pieceValue[piece]
        pieceArray[notationToInt(fromTile)] += pieceVal
        alreadyLeaved.add(fromTile)

#da 5 alle celle dove stockfish consiglia di andare
def tileWeightByStockfish():
    stockfish.set_fen_position(board.fen())
    top = stockfish.get_top_moves(5)
    print()
    for t in top:
        move = t["Move"]
        top5Move.add(str(move))
        print(str(move) + ',',end='')
        fromTile = move[0:2]
        toTile = move[2:4]
        pieceArray[notationToInt(fromTile)] += 1
        stockfishArray[notationToInt(toTile)] += 5
    print()

#assegna un valore a una cella rispetto al 3x3
def calculateTileValue(arr, arrTo, i):
    #i,i-1,i+1,i+8,i-8,i+9,i-9,i+7,i-7
    arrTo[i] = arr[i] + arr[i-1] + arr[i+1] + arr[i-8] + arr[i+8] + arr[i-7] + arr[i+7] + arr[i-9] + arr[i+9]
    return arrTo[i]

#controlla se una casella era contenuta in quelle sensed
def checktile(tile, sensedTile):
    if tile==sensedTile or tile==sensedTile-1 or tile==sensedTile+1 or tile==sensedTile-7 or tile==sensedTile+7 or tile==sensedTile-9 or tile==sensedTile+9 or tile==sensedTile-8 or tile==sensedTile+8:
        return True
    return False

#find heaviest tile in array
def getHeaviestTiles(fromArr, toArr):
    tiles = set()
    maxVal = -1
    tile = -1
    for i in range(9,55):
        if i%8 == 0 or i%8 == 7: continue
        val = calculateTileValue(fromArr, toArr, i)
        if(val == maxVal):
            tiles.add(i)
        if(val > maxVal):
            maxVal = val
            tiles.clear()
            tiles.add(i)
    #print(tiles, maxVal)
    return tiles, maxVal

#first get heaviest tile by stockfish, if there is a draw chose from pieceArray
def selectTile():
    maxVal = -1
    tiles,_ = getHeaviestTiles(stockfishArray, singleTileWeightStockfish)
    if(len(tiles) > 1):
        for t in tiles:
            val = calculateTileValue(pieceArray, singleTileWeightPiece, t)
            if(val > maxVal):
                maxVal = val
                tile = t
    else:
        tile = list(tiles)[0]
        return tile, intToNotation(tile)
    return tile, intToNotation(tile)

#decide dove fare sensing
def sense():
    stockfishArray.fill(0)
    pieceArray.fill(0)
    sumWeight.fill(0)
    singleTileWeightPiece.fill(0)
    singleTileWeightStockfish.fill(0)
    #calculate and print stockfish value
    tileWeightByStockfish()
    print("MATRICE VALORE DI STOCKFISH:")
    printArrayAsBoard(stockfishArray)
    #calculate and print piece value
    tileWeightByPiece()
    print("MATRICE VALORE DEI PEZZI:")
    printArrayAsBoard(pieceArray)
    #fullfill the array for every tile
    sensedTile = selectTile()
    print(sensedTile)
    #print result of computation
    print("MATRICE VALORE PER OGNI CASELLA SU STOCKFISH:")
    printArrayAsBoard(singleTileWeightStockfish)
    print("MATRICE VALORE AD OGNI CASELLA DEI PEZZI:")
    printArrayAsBoard(singleTileWeightPiece)
    return sensedTile[1]

#restituisce la migliore mossa di stockfish
def firstStockMove():
    stockfish.set_fen_position(board.fen())
    top = stockfish.get_top_moves(1)
    print(top[0]['Move'])

#gestisce i risultati del sensing
def manageSenseResult(goodSenseCounter, sensedTile):
    info = input("what have you found?")
    fromInfoTile = info[0:2]
    toInfoTile = info[2:4]
    print(toInfoTile)
    if info == "null":
        for t in top5Move.copy():
            fromTile = t[0:2]
            toTile = t[2:4]
            if checktile(notationToInt(fromTile), notationToInt(sensedTile)) or checktile(notationToInt(toTile), notationToInt(sensedTile)):
                print("Eliminating:"+ t)
                top5Move.remove(t)
            else: print(fromTile + ""+ toTile)
        getBestMove()
    elif toInfoTile == '?':
        for t in top5Move.copy():
            if fromInfoTile != t[0:2] or checktile(notationToInt(t[2:4]), notationToInt(sensedTile)):
                print("Eliminating:"+ t)
                top5Move.remove(t)
            else: print(t)
        getBestMove()
    else:
        board.push(chess.Move.from_uci(info))
        #print(board)
        firstStockMove()
        board.pop()
        goodSenseCounter += 1
    return goodSenseCounter

#chiama evaluation matrix
def getBestMove():
    if len(top5Move) <= 0:
        print("random")
        return
    print("evaluating best move between " + str(len(top5Move)) + " board")
    """for t in top5Move:
        board.push(chess.Move.from_uci(t))
        stockfish.set_fen_position(board.fen())
        top = stockfish.get_top_moves(5)
        for move in top:
            move = str(move["Move"])
            try:
                dict[move] += 1
            except KeyError:
                dict[move] = 1
        board.pop()
    print(dict)
    print(max(dict, key=dict.get))"""
    start = time.time()
    if len(top5Move) == 1:
        board.push(chess.Move.from_uci(list(top5Move)[0]))
        #print(board)
        firstStockMove()
        board.pop()
    else:
        evaluationMatrix()
    print("calcolo matrice:"+ str(time.time()-start))

#genera le possibili mosse in risposta alle migliori mosse potenzialmente fatte dall'avversario
def generatePossibleMoves(matrix, moves):
    start = time.time()
    dictOfTop5={}
    dictOfResponse={}
    y=0
    x = 0
    for t in top5Move:
        board.push(chess.Move.from_uci(t))
        stockfish.set_fen_position(board.fen())
        top = stockfish.get_top_moves(5)
        #print("Mosse contro:"+str(t))
        for t2 in top:
            #print(t2)
            moves.append(t2['Move'])
            matrix[y][x] = t2['Centipawn']
            dictOfResponse[t2['Move']] = t2['Centipawn']
            y += 1
        dictOfTop5[str(t)] = dictOfResponse.copy()
        dictOfResponse.clear()
        board.pop()
        x+=1
    print("generazione mosse:"+ str(time.time()-start))
    return matrix, moves, dictOfTop5

#completa il calcolo della matrice e trova il maxmin, cioè la miglior mossa
def fullFillMatrix(matrix, moves, dictOfMoves):
    start = time.time()
    minimum = -10000000
    minIndex = 0
    #idx è un indice che aiuta a mantenere la diagonale, cioè a tenere dove sono i valori già calcolati
    idx = 0
    x=0
    for m in moves:
        y=0
        #se trovo un nan ho finito i prmi valori preCalc, vado a destra di uno per i prossimi
        if np.isnan(matrix[x][idx]) : idx += 1
        #il minimo all inizio è l'unico valore che conosco per la riga in cui sono
        lineMinValue= matrix[x][idx]
        for t in top5Move:
            print("Analizzo: "+str(t)+", "+str(m))
            print("Valori x: "+str(x)+", y: "+str(y))
            print("Riferimento idx: "+str(idx))
            board.push(chess.Move.from_uci(t))
            move = chess.Move.from_uci(m)
            #il valore che è già peggiore del minimo, skip
            if matrix[x][idx] < minimum:
                print(str(matrix[x][idx])+ " < "+str(minimum)+" quindi esco")
                print()
                board.pop()
                break
            #mossa non legale, o sono su valori già calcolati, vado alla prossima cella a destra
            if not move in board.legal_moves:
                print("Mossa illegale dimentico il minimo di questa riga")
                print()
                lineMinValue = -10000000
                board.pop()
                y += 1
                continue
            if y == idx:
                print("y=idx")
                print()
                board.pop()
                y += 1
                continue
            #calcolo evaluation di questa mossa
            board.push(move)
            if t in dictOfMoves and m in dictOfMoves[t]:
                tmp = dictOfMoves[t]
                e = tmp[m]
                print("Il valore per: "+str(t)+", "+str(m)+" è gia stato calcolato ed è: "+str(e))
            else:
                print("evaluating")
                start=time.time()
                stockfish.set_fen_position(board.fen())
                e = stockfish.get_evaluation()
                e = e['value']
                #print("evaluation:"+ str(time.time()-start))
            #se il risultato è peggiore del minimo allora skip, è importante però allora aggiornare il minLine
            if e < minimum :
                lineMinValue = min(lineMinValue, e)
                matrix[x][y] = e
                print(str(e)+" < "+str(minimum)+" esco")
                board.pop()
                board.pop()
                break
            #print("valutazione: "+str(e))
            lineMinValue = min(lineMinValue, e)
            matrix[x][y] = e
            board.pop()
            board.pop()
            y += 1
            print("Line minimum:"+str(lineMinValue))
            print()
        minimum = max(minimum, lineMinValue)
        #se minimo è minLine significa che ho il miglior valore alla riga in cui sono
        if minimum == lineMinValue : minIndex = x
        print("Minimo:"+str(minimum))
        print()
        x += 1
    print()
    print(matrix)
    print(minIndex)
    print(moves[minIndex])
    print("completamento matrice:"+ str(time.time()-start))

#crea e gestisce la matrice di mosse per rispondere alle probabili mosse avversarie
def evaluationMatrix():
    n = len(top5Move)
    matrix = np.empty((5*n, n))
    matrix.fill(np.nan)
    moves = []
    matrix, moves, dictOfMoves = generatePossibleMoves(matrix, moves)
    print(matrix)
    matrix = fullFillMatrix(matrix, moves, dictOfMoves)

stockfish.set_fen_position(board.fen())
print(board)
#print(time.time()-start)
goodSenseCounter = 0
while(True):
    yourMove = input("your move:")
    board.push(chess.Move.from_uci(yourMove))
    print(board)
    print()
    start = time.time()
    sensedTile = sense()
    print("sense:"+ str(time.time()-start))
    goodSenseCounter = manageSenseResult(goodSenseCounter, sensedTile)
    opponentMove = input("opponent move:")
    board.push(chess.Move.from_uci(opponentMove))
    print(board)
    print()
    #print((goodSenseCounter*100)/(board.ply()/2))
    top5Move.clear()
    #print(time.time()-start)



"""
#Gets the set of attacked squares from the given square.
print(board.attacks(chess.F1))
#restituisce una matrice con 1 nelle celle che hanno pezzi del giocatore in input che minacciano la cella in input
attackers = board.attackers(chess.WHITE, chess.F3)
#true se giocatore.colore sta attaccandoo cella in input, se usi tuo colore e una cella con tuo pezzo, vedi se è protetto
print(board.is_attacked_by(chess.WHITE, chess.B4))
print(attackers)
"""
