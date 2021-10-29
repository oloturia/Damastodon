#!/usr/bin/python3

from mastodon import Mastodon
import draughts_engine as dama
import login
import pickle
import random
import os
import time
import re
import sys

api_url = sys.argv[1]
save_position = "/tmp/"
CLEANR = re.compile('<.*?>')
botname = "@damastodon "

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
		if content.lower() == "help":
			mastodon.status_post("Hello @"+account+" \nchallenge an user by writing to me\nCHALL <USERNAME>\nEx. \"CHALL @someone@mastdn.inst.wxyz\"\nThe challenger takes WHITE and begins the match.\nFor movements and jumps, write the coords separated by spaces.\nEx. \"A4 B5\" (normal movement) or \"A4 C6 D8\" (double jump)\nQUIT ends the match.\nCommands are NOT case sensitive..",visibility="direct")
			return
		if not os.path.exists(save_position+account):
			try:
				challenged = notification["status"]["mentions"][1]["acct"]
			except:
				mastodon.status_post("Hello @"+account+" \n your request is not valid")
				return
			if content[:5].lower() == "chall":
				file_save_white = [sv for sv in saves if account in sv]
				file_save_black = [sv for sv in saves if challenged in sv]
				if len(file_save_white) > 0:
					mastodon.status_post("Hello @"+account+" \n you're already playing a match")
					return
				elif len(file_save_black):
					mastodon.status_post("Hello @"+account+" \n the user you challenged is already playing a match")
					return
				else:
					open(save_position+account,"w").close()
					ident = mastodon.status_post("Hello @"+challenged+" \n@"+account+" challenged you to a match of draughts! Answer \n@"+account+" OK\n to accept the chellenge or \n@"+account+" NO\n to cancel.",visibility="direct")
					return
			elif content.split(" ")[1].lower() == "ok":
				try:
					challenger = notification["status"]["mentions"][1]["acct"]
				except:
					mastodon.status_post("Hello @"+account+" \n your request is not valid")
					return
				os.symlink(save_position+challenger,save_position+account)
				board = dama.init_board()
				with open(save_position+account,"wb") as f:
					pickle.dump("@"+account,f)
					pickle.dump("@"+challenger,f)
					pickle.dump(False,f)
					pickle.dump(board,f)
				mastodon.status_post("◾: @"+account+" ◽: @"+challenger+" turn ◽\n"+dama.draw_checkerboard(board,space="🟥 ",white_norm="◽ ",white_knight="⚪ ",black_norm="◾ ",black_knight="⚫ ",empty="🟦 ",frstrow="0🇦 🇧 🇨 🇩 🇪 🇫 🇬 🇭 \n"),visibility="direct")
				return
			elif content.split(" ")[1].lower() == "no":
				os.remove(save_position+content.split(" ")[0][1:])
				mastodon.status_post(account+" you cancelled the challenge from "+content.split(" ")[0],visibility="direct")
				return
			else:
				mastodon.status_post("Hello @"+account+" \nI can't understand your command or you're not in a match.\nWrite HELP to see the list of available commands.",visibility="direct")
				return
		else:
			with open(save_position+account,"rb") as f:
				black = pickle.load(f)
				white = pickle.load(f)
				turn = pickle.load(f)
				board = pickle.load(f)
			if content.lower() == "quit":
				os.remove(save_position+black[1:])
				os.remove(save_position+white[1:])
				mastodon.status_post(black+" "+white+" the match was cancelled.")
				return
			if (black == "@"+account and turn == 1) or (white == "@"+account and turn == 0):
				board = dama.valid_move(content.lower(),turn,board)
				if board == -1:
					mastodon.status_post("@"+account+" \nInvalid move.",visibility="direct")
					return
				else:
					with open(save_position+account,"wb") as f:
						turn = not turn
						pickle.dump(black,f)
						pickle.dump(white,f)
						pickle.dump(turn,f)
						pickle.dump(board,f)
					if turn == 0:
						colour = "◽"
					else:
						colour = "◾"
					winner = dama.checkWin(board)
					if winner == (False,False):
						mastodon.status_post("◾: "+black+" ◽: "+white+" turn "+colour+"\n"+dama.draw_checkerboard(board,space="🟥 ",white_norm="◽ ",white_knight="⚪ ",black_norm="◾ ",black_knight="⚫ ",empty="🟦 ",frstrow="0🇦 🇧 🇨 🇩 🇪 🇫 🇬 🇭 \n"),visibility="direct")
						return
					else:
						if winner == (True,False):
							winner_t = "WHITE"
						else:
							winner_t = "BLACK"
						os.remove(save_position+black[1:])
						os.remove(save_position+white[1:])
						mastodon.status_post("◾: "+black+" ◽: "+white+"\n"+winner_t+" WINS!\n"+dama.draw_checkerboard(board,space="🟥 ",white_norm="◽ ",white_knight="⚪ ",black_norm="◾ ",black_knight="⚫ ",empty="🟦 ",frstrow="0🇦 🇧 🇨 🇩 🇪 🇫 🇬 🇭 \n"),visibility="direct")
						return
			else:
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
