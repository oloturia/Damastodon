#!/usr/bin/python3
from mastodon import Mastodon
from os.path import exists
import sys

try:
	API_URL = sys.argv[1]
	username = sys.argv[2]
	password = sys.argv[3]
except:
	print("createcred.py url username password")

if API_URL[:4] != "http":
	print("Invalid URL")
	quit()

if not (exists("TOKEN")):
	Mastodon.create_app(
		"dama",
		api_base_url = API_URL,
		to_file="TOKEN"
	)

mastodon = Mastodon(
	client_id = 'TOKEN',
    api_base_url = API_URL
)

mastodon.log_in(
	username,
	password,
	to_file = "DAMA.SECRET"
)
