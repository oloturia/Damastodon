#!/usr/bin/python3

from mastodon import Mastodon
import draughts_engine as dama
import login
import pickle
import random
import os
import time
import sys
import re

#configuration server
api_url = sys.argv[1]
save_position = "/tmp/"
CLEANR = re.compile('<.*?>')
botname = "@damastodon "

#board appearence
frstrow = "🇻1️⃣ 2️⃣ 3️⃣ 4️⃣ 5️⃣ 6️⃣ 7️⃣ 8️⃣\n"
column = "🇦🇧🇨🇩🇪🇫🇬🇭"
space="🟥 "
white_norm="◽ "
white_knight="⚪ "
black_norm="◾ "
black_knight="⚫ "
empty="🟦 "


def cleanHTML(raw):
	cleanText = re.sub(CLEANR, '',raw)
	return cleanText

def check_message(notification):
		account = notification["account"]["acct"]
		try:
			content = cleanHTML(notification["status"]["content"])
		except KeyError:
			return
		content = content[len(botname):]
		saves = os.listdir(save_position)
		if "help" in content.lower(): #Ask for help
			mastodon.status_post("Hello @"+account+" \nchallenge an user by writing to me\nCHALL <USERNAME>\nEx. \"CHALL @someone@mastdn.inst.wxyz\"\nThe challenger takes WHITE and begins the match.\nFor movements and jumps, write the coords separated by spaces.\nEx. \"A4 B5\" (normal movement) or \"A4 C6 D8\" (double jump)\nQUIT ends the match.\nCommands are NOT case sensitive.",visibility="direct")
			return
		if not os.path.exists(save_position+account): #If there is no a savegame file, then lobby mode is activated
			try:
				challenged = notification["status"]["mentions"][1]["acct"] #If there isn't another account cited, then the request is malformed
			except:
				mastodon.status_post("Hello @"+account+" \n your request is not valid",visibility="direct")
				return
			if content[:5].lower() == "chall": #Challenge someone, check if a savegame is already existing
				file_save_white = [sv for sv in saves if account in sv]
				file_save_black = [sv for sv in saves if challenged in sv]
				if len(file_save_white) > 0: #We are playing a match
					mastodon.status_post("Hello @"+account+" \n you're already playing a match",visibility="direct") 
					return
				elif len(file_save_black) > 0: #Our opponent is already playing with someone
					mastodon.status_post("Hello @"+account+" \n the user you challenged is already playing a match",visibility="direct")
					return
				else:
					with open(save_position+account,"wb") as f: #The request is valid, writes a savegame with the first element as False, that marks that the game isn't started yet
						pickle.dump("WAIT",f)
					ident = mastodon.status_post("Hello @"+challenged+" \n@"+account+" challenged you to a match of draughts! Answer \n@"+account+" OK\n to accept the chellenge or \n@"+account+" NO\n to cancel.",visibility="direct")
					return
			elif content.split(" ")[1].lower() == "ok": #The opponent accepted the match
				try:
					challenger = notification["status"]["mentions"][1]["acct"] 
				except:
					mastodon.status_post("Hello @"+account+" \n your request is not valid",visibility="direct") #Somehow, the opponent answered with only one account
					return
				try:
					with open(save_position+challenger,"rb") as f:
						start = pickle.load(f)
				except FileNotFoundError:
					mastodon.status_post("Hello @"+account+" \n unfortunately, your savegame is corrupted or missing",visibility="direct") #The file has moved or corrupted
					return
				if start != "WAIT":
					mastodon.status_post("Hello @"+account+" \n your request is not valid",visibility="direct") #The user that challenged us is playing a game with someone else
					return
				os.symlink(save_position+challenger,save_position+account) #Linked the two savegames together
				board = dama.init_board()
				with open(save_position+account,"wb") as f:
					pickle.dump("START",f) #Now the game has started
					pickle.dump("@"+account,f)
					pickle.dump("@"+challenger,f)
					pickle.dump(False,f)
					pickle.dump(board,f)
				mastodon.status_post("◾: @"+account+" ◽: @"+challenger+" \nturn ◽\n"+dama.draw_checkerboard(board,space,white_norm,white_knight,black_norm,black_knight,empty,column,frstrow),visibility="direct")
				return
			elif content.split(" ")[1].lower() == "no": #The opponent refused the game
				try:
					challenger = notification["status"]["mentions"][1]["acct"]
				except:
					mastodon.status_post("Hello @"+account+" \n your request is not valid",visibility="direct") #Only one user in the message
					return
				os.remove(save_position+challenger)
				mastodon.status_post("@"+account+" you cancelled the challenge from @"+challenger,visibility="direct") #Game is cancelled, free to challenge someone else
				return
			else:
				mastodon.status_post("Hello @"+account+" \nI can't understand your command or you're not in a match.\nWrite HELP to see the list of available commands.",visibility="direct") #Every other command for the lobby ends here
				return
		else: #We are in a game, so movements are parsed and lobby commands are disabled
			with open(save_position+account,"rb") as f:
				start = pickle.load(f)
				if start: #The game is started, load other parameters
					black = pickle.load(f)
					white = pickle.load(f)
					turn = pickle.load(f)
					board = pickle.load(f)
			if (start == "WAIT"): #The game is not started yet
				if "quit" in content.lower(): #Game withdrawn
					os.remove(save_position+account)
					mastodon.status_post("Hello @"+account+" \nthe challenge has been withdrawn.",visibility="direct")
				else: #Lobby is disabled if a challenge request is active
					mastodon.status_post("Hello @"+account+" \nyou have already challenged someone, type QUIT to withdraw,",visibility="direct")
				return
			if "quit" in content.lower(): #The game is quitted
				os.remove(save_position+black[1:])
				os.remove(save_position+white[1:])
				mastodon.status_post(black+" "+white+" the match was cancelled.",visibility="direct")
				return
			if (black == "@"+account and turn == 1) or (white == "@"+account and turn == 0): #Check if the turn is right
				board = dama.valid_move(content.lower(),turn,board,inversion=True) #Function dama.valid_move parses the input for couples of letter and number
				if board == -1: #We made an invalid move
					mastodon.status_post("@"+account+" \nInvalid move.",visibility="direct")
					return
				else:
					with open(save_position+account,"wb") as f: #Save the updated board
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
						os.remove(save_position+black[1:])
						os.remove(save_position+white[1:])
						mastodon.status_post("◾: "+black+" ◽: "+white+"\n"+winner_t+" WINS!\n"+dama.draw_checkerboard(board,space,white_norm,white_knight,black_norm,black_knight,empty,column,frstrow),visibility="direct")
						return
			else: #We moved in a wrong turn
				mastodon.status_post("@"+account+" \nIt's not your turn.",visibility="direct")
				return		

if __name__ == "__main__":
	if api_url[:4] != "http":
		print("Invalid address.")
		quit()
	mastodon = login.login(api_url)
	while True:
		time.sleep(10)
		for x in mastodon.notifications():
			check_message(x)
			mastodon.notifications_dismiss(x["id"])
