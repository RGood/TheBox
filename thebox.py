# oauth PRAW template by /u/The1RGood #
#==================================================Config stuff====================================================
import time, praw
import webbrowser
from flask import Flask, request
from threading import Thread

#==================================================End Config======================================================
#==================================================OAUTH APPROVAL==================================================
app = Flask(__name__)

CLIENT_ID = '24s3PNTHFbHsoA' #SET THIS TO THE ID UNDER PREFERENCES/APPS
CLIENT_SECRET = '5HuUzRcISFNWza5Bm-CkHipm0-A' #SET THIS TO THE SECRET UNDER PREFERENCES/APPS
owner_scope = 'modothers' #SET THIS. SEE http://praw.readthedocs.org/en/latest/pages/oauth.html#oauth-scopes FOR DETAILS.
participant_scope = 'identity modself'

REDIRECT_URI = 'http://127.0.0.1:65010/authorize_callback'

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
	if(r.user.me()):
		return auth_participant(praw.Reddit(
			client_id=CLIENT_ID,
			client_secret=CLIENT_SECRET,
			redirect_uri=REDIRECT_URI,
			user_agent='Mod Permissions'
			), request.args.get('code', ''))
	else:
		return auth_owner(owner_client, request.args.get('code', ''))

def auth_owner(client, code):
	client.auth.authorize(code)
	user = r.user.me()
	text = 'The Box started on account /u/'+user.name
	return text

def auth_participant(client, code):
	client.auth.authorize(code)
	mod_user(client)
	return '<meta http-equiv="refresh" content="0; url=http://www.reddit.com/r/thebox/about/moderators" />\
			<p><a href="http://www.reddit.com/r/thebox/about/moderators">Redirect</a></p>'

def mod_user(participant_client):
	#check mods with owner client
	#maybe remove one
	#add user with owner client
	#accept user with participant client

owner_client = praw.Reddit(
	client_id=CLIENT_ID,
	client_secret=CLIENT_SECRET,
	redirect_uri=REDIRECT_URI,
	user_agent='The Box Bot'
	)

webbrowser.open(r.auth.url(scope.split(' '),True))
app.run(debug=False, port=65010)
#==================================================END OAUTH APPROVAL-=============================================