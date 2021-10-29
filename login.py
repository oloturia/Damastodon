from mastodon import Mastodon

def login(url):
	mastodon = Mastodon(
		access_token = "DAMA.SECRET",
		api_base_url = url
	)	
	return mastodon
