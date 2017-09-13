# oauth PRAW template by /u/The1RGood #
#==================================================Config stuff====================================================
import time, praw
import webbrowser
from flask import Flask, request
from threading import Thread
from random import Random
import configparser
#==================================================End Config======================================================
#==================================================OAUTH APPROVAL==================================================
app = Flask(__name__)

Config = configparser.ConfigParser()
Config.read('box_info.cfg')

CLIENT_ID = Config.get('Reddit Access','cid')
CLIENT_SECRET = Config.get('Reddit Access','csec')
REDIRECT_URI = Config.get('Reddit Access','callback')

owner_scope = 'identity modothers read' #SET THIS. SEE http://praw.readthedocs.org/en/latest/pages/oauth.html#oauth-scopes FOR DETAILS.
participant_scope = 'identity modself'

owner = None
subreddit = ''
temp_mods = int(Config.get('Reddit Access','mods'))
rand = Random()

#Kill function, to stop server once auth is granted
def kill():
	func = request.environ.get('werkzeug.server.shutdown')
	if func is None:
		raise RuntimeError('Not running with the Werkzeug Server')
	func()
	return "Shutting down..."

#Callback function to receive auth code
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

@app.route('/')
def get_auth_route():
	auth_url = owner_client.auth.url(participant_scope.split(' '), True)
	return '<meta http-equiv="refresh" content="0; url='+auth_url+'" />\
			<p><a href="'+ auth_url +'">Redirect</a></p>'

def auth_owner(client, code):
	global owner, subreddit
	client.auth.authorize(code)
	owner = client.user.me().name
	subreddit = client.subreddit(Config.get('Reddit Access','subreddit'))
	text = 'The Box started on account /u/'+owner
	return text

def auth_participant(client, code):
	client.auth.authorize(code)
	mod_user(client)
	return '<meta http-equiv="refresh" content="0; url=http://www.reddit.com/r/'+ subreddit.display_name +'/about/moderators" />\
			<p><a href="http://www.reddit.com/r/'+ subreddit.display_name +'/about/moderators">Redirect</a></p>'

def mod_user(participant_client):
	#check mods with owner client
	#filter out owner so you don't demod yourself
	mods = list(filter((lambda user: user.name!=owner), subreddit.moderator()))
	
	#maybe remove
	while(len(mods) >= temp_mods):
		to_remove = mods[rand.randint(0, len(mods))]
		print("Removing " + to_remove.name + " of possible:")
		print(mods)
		subreddit.moderator.remove(to_remove)
		mods.remove(to_remove)

	#add participant with owner client
	print("Inviting " + participant_client.user.me().name)
	subreddit.moderator.invite(participant_client.user.me(), ['access','config','flair','mail','posts'])

	#accept user with participant client
	print("Accepting for " +participant_client.user.me().name)
	temp_sub = participant_client.subreddit(subreddit.display_name)
	temp_sub.mod.accept_invite()

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
#==================================================END OAUTH APPROVAL-=============================================