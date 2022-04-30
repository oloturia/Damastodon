#!/usr/bin/python3

def drawChequerboard(status,players=[],toprow="1234567"):
	print(toprow)
	for row in status:
		for cell in row:
			if cell == 0:
				print("░",end="")
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
	offset_pairs = ( ((0,1),(0,-1)) , ((1,0),(-1,0)) , ((1,1),(-1,-1)) , ((-1,1),(1,-1)) )
	points = 0
	for offset in offset_pairs:
		count = 0
		count += checkSide(board,row,col,offset[0])
		count += checkSide(board,row,col,offset[1])
		if count >= 4:
			points += 1
	return points
	
			
def checkSide(board,row,col,incs):
	incY,incX = incs
	count = 0
	player = board[row][col]
	offsetX = 0
	offsetY = 0
	while count < 4:
		try:
			if board[row+offsetX][col+offsetY] == player:
				count += 1
				offsetX += incX
				offsetY += incY
			else:
				break
		except IndexError:
			break
	return count
		

if __name__ == "__main__":
	board = initChequerboard()
	match = True
	player = 1
	points_1 = 0
	points_2 = 0
	while match:
		drawChequerboard(board)
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
	print("Player 1 scored "+str(points_1)+" points")
	print("Player 2 scored "+str(points_2)+" points")
	if points_1 > points_2:
		print("Player 1 won!")
	elif points_2 > points_2:
		print("Player 2 won!")
	else:
		print("Draw!")
