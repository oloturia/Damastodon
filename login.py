from mastodon import Mastodon
import os

fileDir = os.path.dirname(os.path.abspath(__file__))
fileDir = fileDir +"/"

def login(url):
	mastodon = Mastodon(
		access_token = fileDir+"DAMA.SECRET.LOCAL",
		api_base_url = url
	)	
	return mastodon
