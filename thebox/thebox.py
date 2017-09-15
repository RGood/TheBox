# oauth PRAW template by /u/The1RGood #
# ================================================== Config stuff ====================================================
import time, praw
import webbrowser
from flask import Flask, request
from threading import Thread
import random
import configparser
import pymongo
# ================================================== End Config ======================================================
# ================================================== OAUTH APPROVAL ==================================================
app = Flask(__name__)

Config = configparser.ConfigParser()
Config.read('box_info.cfg')

# Config Oauth
CLIENT_ID = Config.get('Reddit Access','cid')
CLIENT_SECRET = Config.get('Reddit Access','csec')
REDIRECT_URI = Config.get('Reddit Access','callback')

# Config Database
users = pymongo.MongoClient(Config.get('Mongo Access','conn_str'))[Config.get('Mongo Access','database')][Config.get('Mongo Access','collection')]

# Permissions requires for owner
owner_scope = 'identity modothers read'

# Permissions required for participants
participant_scope = 'identity modself'

owner = None
subreddit = ''

# Kill function, to stop server. Unused atm.
def kill():
	func = request.environ.get('werkzeug.server.shutdown')
	if func is None:
		raise RuntimeError('Not running with the Werkzeug Server')
	func()
	return "Shutting down..."

# Callback function to receive auth code
# Needs refactor
@app.route('/authorize_callback')
def authorized():
	if(owner != None):
		return auth_participant(praw.Reddit(
			client_id=CLIENT_ID,
			client_secret=CLIENT_SECRET,
			redirect_uri=REDIRECT_URI,
			user_agent='Mod Permissions'
			), request.args.get('code', ''))
	else:
		return auth_owner(owner_client, request.args.get('code', ''))

# Creates permission URL and displays to the people who click the subreddit link
@app.route('/')
def get_auth_route():
	auth_url = owner_client.auth.url(participant_scope.split(' '), True)
	meta_url = '<meta http-equiv="refresh" content="0; url={0}" />'
	redirect_url = '<p><a href="{0}">Redirect</a></p>'
	return (meta_url + '\n' + redirect_url).format(auth_url)

# When I turn the bot on, this lets it use my account
def auth_owner(client, code):
	global owner, subreddit
	client.auth.authorize(code)
	owner = client.user.me().name
	subreddit = client.subreddit(Config.get('Reddit Access','subreddit'))
	text = 'The Box started on account /u/{0}'.format(owner)
	return text

def auth_participant(client, code):
	client.auth.authorize(code)
	mod_user(client)

	meta_url = '<meta http-equiv="refresh" content="0; url=http://www.reddit.com/r/{0}/about/moderators" />'
	redirect_url = '<p><a href="http://www.reddit.com/r/{0}/about/moderators">Redirect</a></p>'
	return (meta_url + '\n' + redirect_url).format(subreddit.display_name)

def mod_user(participant_client):
	participant = participant_client.user.me()

	# Refresh the config, so I can do this live
	Config.read('box_info.cfg')
	mod_limit = Config.get('Reddit Access','mod_limit')
	mod_count = int(Config.get('Reddit Access','mods'))
	age_restriction = int(Config.get('Reddit Access', 'age_restriction'))

	if(time.time() - participant.created < age_restriction):
		return

	# Make sure user conforms to mod criteria
	entry = users.find_one({'username': participant.name})

	if(entry!=None):
		if(mod_limit != '' and entry['mod_count'] >= int(mod_limit)):
			return
		elif('status' in list(entry.keys()) and entry['status'] == 'banned'):
			return
		else:
			entry['mod_count']+=1
			users.save(entry)
	else:
		users.insert({'username': participant.name, 'mod_count': 1})


	# check mods with owner client
	# filter out owner so you don't demod yourself
	mods = list(filter((lambda user: user.name!=owner), subreddit.moderator()))

	if(participant in mods):
		return

	# maybe remove
	while(len(mods) >= mod_count):
		to_remove = mods[random.randint(0, len(mods)-1)]
		print("Removing {0} of possible:".format(to_remove.name))
		print(mods)
		subreddit.moderator.remove(to_remove)
		mods.remove(to_remove)

	# add participant with owner client
	print("Inviting {0}".format(participant_client.user.me().name))
	subreddit.moderator.invite(participant_client.user.me(), ['access','config','flair','mail','posts'])

	# accept invite with participant client
	print("Accepting for {0}".format(participant_client.user.me().name))
	temp_sub = participant_client.subreddit(subreddit.display_name)
	temp_sub.mod.accept_invite()
	# After this point, all refereces to the client are lost and will be garbage-collected

owner_client = praw.Reddit(
	client_id=CLIENT_ID,
	client_secret=CLIENT_SECRET,
	redirect_uri=REDIRECT_URI,
	user_agent='The Box Bot'
	)

print("Owner Auth")
print(owner_client.auth.url(owner_scope.split(' '),True))
print("User Auth")
print(owner_client.auth.url(participant_scope.split(' '), True))
app.run(debug=False, port=65010)
# ================================================== END OAUTH APPROVAL ==============================================
