#!/usr/bin/python3

def drawChequerboard(status,players=[],space="░",toprow="1234567"):
	print(toprow)
	for row in status:
		for cell in row:
			if cell == 0:
				print(space,end="")
			else:
				try:
					print(players[cell],end="")
				except IndexError:
					print(str(cell),end="")
		print(" ")
	
def initChequerboard(cols=7,rows=6):
	board = list()
	for row in range(rows):
		board.append([0]*7)
	return board

def dropChip(board,move_str,player):
	failure = (False,0)
	try:
		move = int(move_str)-1
	except ValueError:
		return failure
	if move < 0 or move > 6:
		return failure
	free_space = -1
	for row in board:
		if row[move] != 0:
			break
		else:
			free_space += 1
	if free_space == -1:
		return failure
	board[free_space][move] = player
	return board, checkFour(board,free_space,move)

def checkFour(board,row,col):
	sumOr = lambda a,b : (a[0]+b[0], a[1]+b[1])
	orients = { "N":(1,0),"S":(-1,0),"E":(0,1),"W":(0,-1) }
	player = board[row][col]
	points = 0
	count = 0
	count += countTokens(board,orients["N"],row,col)
	count += countTokens(board,orients["S"],row,col)
	if count >= 3:
		points +=1
	count = 0
	count += countTokens(board,orients["E"],row,col)
	count += countTokens(board,orients["W"],row,col)
	if count >= 3:
		points +=1
	count = 0
	count += countTokens(board,sumOr( orients["N"],orients["E"] ),row,col )
	count += countTokens(board,sumOr( orients["S"],orients["W"] ),row,col )
	if count >= 3:
		points +=1
	count = 0
	count += countTokens(board,sumOr( orients["N"],orients["W"] ),row,col )
	count += countTokens(board,sumOr( orients["S"],orients["E"] ),row,col )
	if count >= 3:
		points +=1

	
	return points

def countTokens(board,check,row,col):
	player = board[row][col]
	offX = check[0]
	offY = check[1]
	count = 0
	while True:
		if row+offY < 0 or row+offY >= len(board[row])-1 or col+offX < 0 or col+offX > len(board) or  (board[row+offY][col+offX] != player) :
			break
		else:
			count += 1
			offX += check[0]
			offY += check[1]
	return count

def checkPly(board,row,col,player):
	if row < 0 or col < 0:
		return False
	try:
		if board[row][col] == player:
			return True
		else:
			return False
	except IndexError:
		return False


if __name__ == "__main__":
	board = initChequerboard()
	match = True
	player = 1
	points_1 = 0
	points_2 = 0
	while match:
		drawChequerboard(board)
		print("Player 1:"+str(points_1))
		print("Player 2:"+str(points_2))
		move = input("Player "+str(player)+" turn:")
		if move == "q":
			print("quitting")
			quit()
		valid, point = dropChip(board,move,player)
		if not(valid):	
			print("Invalid move")
		else:
			board = valid
			if player == 2:
				points_2 += point
				player = 1
			else:
				points_1 += point
				player = 2
		match = False
		for row in board:
			for cell in row:
				if cell == 0:
					match = True
	print("Match over")
	drawChequerboard(board)
	print("Player 1 scored "+str(points_1)+" points")
	print("Player 2 scored "+str(points_2)+" points")
	if points_1 > points_2:
		print("Player 1 won!")
	elif points_2 > points_1:
		print("Player 2 won!")
	else:
		print("Draw!")
