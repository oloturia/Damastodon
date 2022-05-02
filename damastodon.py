#!/usr/bin/python3

from mastodon import Mastodon
import draughts_engine as dama
import four_engine
import login
import pickle
import random
import os
import time
import sys
import re
import logging

#configuration server
api_url = sys.argv[1]
save_position = "/tmp/"
CLEANR = re.compile('<.*?>')
#botname = "@damastodon "
botname = "@dama "

available_games = ("draughts","conn4")

#board appearence
frstrow = "🇻1️⃣ 2️⃣ 3️⃣ 4️⃣ 5️⃣ 6️⃣ 7️⃣ 8️⃣\n"
column = "🇦🇧🇨🇩🇪🇫🇬🇭"
space="🟥 "
white_norm="◽ "
white_knight="⚪ "
black_norm="◾ "
black_knight="⚫ "
empty="🟦 "

#conn4
conn4row = "1️⃣ 2️⃣ 3️⃣ 4️⃣ 5️⃣ 6️⃣ 7️⃣\n"

#logging config
logging.basicConfig(filename="/tmp/dama.log",level=logging.DEBUG)

def cleanHTML(raw):
	cleanText = re.sub(CLEANR, '',raw)
	return cleanText

def lobby(notification,content,account,extension):
		try:
			challenged = notification["status"]["mentions"][1]["acct"] #If there isn't another account cited, then the request is malformed
		except:
			mastodon.status_post("Hello @"+account+" \n your request is not valid",visibility="direct")
			return

		if challenged == account: #The user tried to challenge him/herself
			mastodon.status_post("Hello @"+account+"\n You can't challenge yourself",visibility="direct")
			return

		if content.split(" ")[0].lower() == extension: #Challenge someone, check if a savegame is already existing
			if os.path.exists(save_position+challenged+"."+extension):
				mastodon.status_post("Hello @"+account+" \n the user you challenged is already playing a match",visibility="direct")
				return
			else:
				with open(save_position+account+"."+extension,"wb") as f: #The request is valid, writes a savegame with the first element as False, that marks that the game isn't started yet
					pickle.dump("WAIT",f)
				ident = mastodon.status_post("Hello @"+challenged+" \n@"+account+" challenged you to a match of "+extension+"! Reply \n @"+account+" OK "+extension.upper()+"\n to accept the challenge or \n@"+account+" NO "+extension.upper()+"\n to cancel.",visibility="direct")
				return
		elif content.split(" ")[1].lower() == "ok" and content.split(" ")[2].lower() == extension: #The opponent accepted the match
			try:
				challenger = notification["status"]["mentions"][1]["acct"] 
			except:
				mastodon.status_post("Hello @"+account+" \n your request is not valid",visibility="direct") #Somehow, the opponent answered with only one account
				return
			try:
				with open(save_position+challenger+"."+extension,"rb") as f:
					start = pickle.load(f)
			except FileNotFoundError:
				mastodon.status_post("Hello @"+account+" \n unfortunately, your savegame is corrupted or missing",visibility="direct") #The file has moved or corrupted
				logging.warning("%s file not found",account)
				return
			if start != "WAIT":
				mastodon.status_post("Hello @"+account+" \n your request is not valid",visibility="direct") #The user that challenged us is playing a game with someone else
				return
			os.symlink(save_position+challenger+"."+extension,save_position+account+"."+extension) #Linked the two savegames together
			
			
			if extension == "draughts": #Draughts init
				board = dama.init_board()
				mastodon.status_post("◾: @"+account+" ◽: @"+challenger+" \nturn ◽\n"+dama.draw_checkerboard(board,space,white_norm,white_knight,black_norm,black_knight,empty,column,frstrow),visibility="direct")
			elif extension == "conn4": #Conn4 init
				board = four_engine.initChequerboard()
				mastodon.status_post("⚪: @"+account+" \n⚫: @"+challenger+" \nturn ⚪\n"+four_engine.drawChequerboard(board,players=[white_knight,black_knight],space=empty,toprow=conn4row),visibility="direct")			
			with open(save_position+account+"."+extension,"wb") as f: #Writing the file with the status of the game
				pickle.dump("START",f) #Now the game has started
				pickle.dump("@"+account,f)
				pickle.dump("@"+challenger,f)
				pickle.dump(False,f)
				pickle.dump(board,f)
			return
		elif content.split(" ")[1].lower() == "no" and content.split(" ")[2].lower == extension: #The opponent refused the game
			try:
				challenger = notification["status"]["mentions"][1]["acct"]
			except:
				mastodon.status_post("Hello @"+account+" \n your request is not valid",visibility="direct") #Only one user in the message
				return
			os.remove(save_position+challenger+"."+extension)
			mastodon.status_post("@"+account+" you cancelled the challenge from @"+challenger,visibility="direct") #Game is cancelled, free to challenge someone else
			return
		else:
			mastodon.status_post("Hello @"+account+" \nI can't understand your command or you're not in a match.\nWrite HELP to see the list of available commands.",visibility="direct") #Every other command for the lobby ends here
			return

def load_status(account,extension,content):
	with open(save_position+account+"."+extension,"rb") as f: #Open the status file - extension is the type of the game
		try:
			start = pickle.load(f)
		except EOFError: #Something wrong happened
			mastodon.status_post("Hello @"+account+" \n unfortunately your savegame is corrupted or missing. The game is cancelled.",visibility="direct")
			os.remove(save_position+account+"."+extension)
			logging.warning("% file corrupted or missing",account+"."+extension)
			return False

		player_1 = pickle.load(f) #Read status from file
		player_2 = pickle.load(f)
		turn = pickle.load(f)
		board = pickle.load(f)

		if (start == "WAIT"): #The game is not started yet
			if "quit" in content.lower(): #Game withdrawn
				os.remove(save_position+account+"."+extension)
				mastodon.status_post("Hello @"+account+" \nthe challenge has been withdrawn.",visibility="direct")
			else: #Lobby is disabled if a challenge request is active
				mastodon.status_post("Hello @"+account+" \nyou have already challenged someone, type QUIT to withdraw,",visibility="direct")
				return False
			if "quit" in content.lower(): #The game is quitted
				os.remove(save_position+player_1[1:]+"."+extension)
				os.remove(save_position+player_2[1:]+"."+extension)
				mastodon.status_post(player_2+" "+player_1+" the match was cancelled.",visibility="direct")
				return False

		return True,player_1,player_2,turn,board

def check_message(notification):
		account = notification["account"]["acct"]
		try:
			content = cleanHTML(notification["status"]["content"])
		except KeyError:
			return
		content = content[len(botname):]
		if "help" in content.lower(): #Ask for help
			mastodon.status_post("Hello @"+account+" \nchallenge an user in a game of draughts by writing to me\nDRAUGHTS <USERNAME>\nEx. \"DRAUGHTS @someone@mastdn.inst.wxyz\"\nThe challenger takes WHITE and begins the match.\nFor movements and jumps, write the coords separated by spaces.\nEx. \"A4 B5\" (normal movement) or \"A4 C6 D8\" (double jump)\nQUIT ends the match.\nCommands are NOT case sensitive.\nTo challenge someone in a game of Connect 4 write CONN4 <USERNAME>.",visibility="direct")
			return
		

		#Conn4
		if os.path.exists(save_position+account+".conn4"):
			start,player_1,player_2,turn,board = load_status(account,"conn4",content)
			if not(start):
				return
			
			if (player_2 == "@"+account and turn == 1) or (player_1 == "@"+account and turn == 0):
				board,win = four_engine.dropChip(board,content.lower()[-1],turn+1)
				if not(board): 
					mastodon.status_post("@"+account+" \nInvalid move.",visibility="direct")
					return
				else:
					with open(save_position+account+".conn4","wb") as f:
						pickle.dump("START",f)
						turn = not turn
						pickle.dump(player_1,f)
						pickle.dump(player_2,f)
						pickle.dump(turn,f)
						pickle.dump(board,f)
					if turn == 0: #the first is the current turn, the second is the last turn
						colour = (white_knight,black_knight)
					else:
						colour = (black_knight,white_knight)
					if win == 0:
						mastodon.status_post("⚪: "+player_1+" \n⚫: "+player_2+" \nturn "+colour[0]+"\n"+four_engine.drawChequerboard(board,players=[white_knight,black_knight],space=empty,toprow=conn4row),visibility="direct")			
						return
					else: #Someone won!
						mastodon.status_post("⚪: "+player_1+" \n⚫: "+player_2+" \n"+colour[1]+" WINS!\n"+four_engine.drawChequerboard(board,players=[white_knight,black_knight],space=empty,toprow=conn4row),visibility="direct")			
						os.remove(save_position+player_1[1:]+".conn4")
						os.remove(save_position+player_2[1:]+".conn4")
						return
			else: #We moved in a wrong turn
				mastodon.status_post("@"+account+" \nIt's not your turn.",visibility="direct")
				return					
		
		#Draughts
		if os.path.exists(save_position+account+".draughts"): #We are in a game, so movements are parsed and lobby commands are disabled
			start,black,white,turn,board = load_status(account,"conn4")
			if not(start):
				return


			if (black == "@"+account and turn == 1) or (white == "@"+account and turn == 0): #Check if the turn is right
				board = dama.valid_move(content.lower(),turn,board,inversion=True) #Function dama.valid_move parses the input for couples of letter and number
				if board == -1: #We made an invalid move
					mastodon.status_post("@"+account+" \nInvalid move.",visibility="direct")
					return
				else:
					with open(save_position+account+".draughts","wb") as f: #Save the updated board
						pickle.dump("START",f)
						turn = not turn
						pickle.dump(black,f)
						pickle.dump(white,f)
						pickle.dump(turn,f)
						pickle.dump(board,f)
					if turn == 0:
						colour = "◽"
					else:
						colour = "◾"
					winner = dama.checkWin(board) #Check for winner
					if winner == (False,False): #No one is winning yet
						mastodon.status_post("◾: "+black+" ◽: "+white+" \nturn "+colour+"\n"+dama.draw_checkerboard(board,space,white_norm,white_knight,black_norm,black_knight,empty,column,frstrow),visibility="direct")
						return
					else: #Someone won
						if winner == (True,False):
							winner_t = "WHITE"
						else:
							winner_t = "BLACK"
						os.remove(save_position+black[1:]+".draughts")
						os.remove(save_position+white[1:]+".draughts")
						mastodon.status_post("◾: "+black+" ◽: "+white+"\n"+winner_t+" WINS!\n"+dama.draw_checkerboard(board,space,white_norm,white_knight,black_norm,black_knight,empty,column,frstrow),visibility="direct")
						return
			else: #We moved in a wrong turn
				mastodon.status_post("@"+account+" \nIt's not your turn.",visibility="direct")
				return	
		
		#Lobby			
		for game in available_games:
			if game in content.lower():
				if not os.path.exists(save_position+account+"."+game): #If there is no a savegame file, then lobby mode is activated
					lobby(notification,content,account,game)	

if __name__ == "__main__":
	if api_url[:4] != "http":
		logging.error("Invalid address")
		quit()
	mastodon = login.login(api_url)
	while True:
		time.sleep(10)
		for x in mastodon.notifications():
			check_message(x)
			mastodon.notifications_dismiss(x["id"])
