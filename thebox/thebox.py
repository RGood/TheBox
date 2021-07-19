# oauth PRAW template by /u/The1RGood #
#==================================================Config stuff====================================================
import time, praw
import webbrowser
from flask import Flask, request
from threading import Thread
import random
import configparser
import pymongo
#==================================================End Config======================================================
#==================================================OAUTH APPROVAL==================================================
app = Flask(__name__)

Config = configparser.ConfigParser()
Config.read('box_info.cfg')

#Config Oauth
CLIENT_ID = Config.get('Reddit Access','cid')
CLIENT_SECRET = Config.get('Reddit Access','csec')
REDIRECT_URI = Config.get('Reddit Access','callback')

#Config Database
users = pymongo.MongoClient(Config.get('Mongo Access','conn_str'))[Config.get('Mongo Access','database')][Config.get('Mongo Access','collection')]

#Permissions requires for owner
owner_scope = 'identity modothers read'

#Permissions required for participants
participant_scope = 'identity modself'

#Callback function to receive auth code
#Needs refactor
@app.route('/authorize_callback')
def authorized():
	return auth_participant(praw.Reddit(
		client_id=CLIENT_ID,
		client_secret=CLIENT_SECRET,
		redirect_uri=REDIRECT_URI,
		user_agent='Mod Permissions'
		), request.args.get('code', ''))

#Creates permission URL and displays to the people who click the subreddit link
@app.route('/')
def get_auth_route():
	auth_url = owner_client.auth.url(participant_scope.split(' '), True)
	return '<meta http-equiv="refresh" content="0; url='+auth_url+'" />\
			<p><a href="'+ auth_url +'">Redirect</a></p>'

def auth_participant(client, code):
	client.auth.authorize(code)
	mod_user(client)
	return '<meta http-equiv="refresh" content="0; url=http://www.reddit.com/r/'+ subreddit.display_name +'/about/moderators" />\
			<p><a href="http://www.reddit.com/r/'+ subreddit.display_name +'/about/moderators">Redirect</a></p>'

def mod_user(participant_client):
	participant = participant_client.user.me()

	#Refresh the config, so I can do this live
	Config.read('box_info.cfg')
	mod_limit = Config.get('Reddit Access','mod_limit')
	mod_count = int(Config.get('Reddit Access','mods'))
	age_restriction = int(Config.get('Reddit Access', 'age_restriction'))

	if(time.time() - participant.created < age_restriction):
		return

	#Make sure user conforms to mod criteria
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


	#check mods with owner client
	#filter out owner so you don't demod yourself
	seen_self = False
	mods = []
	for mod in subreddit.moderator():
		if(seen_self):
			mods+=[mod]
		if(mod.name == owner):
			seen_self = True

	if(participant in mods):
		return

	#maybe remove
	while(len(mods) >= mod_count):
		to_remove = mods[random.randint(0, len(mods)-1)]
		print("Removing " + to_remove.name + " of possible:")
		print(mods)
		subreddit.moderator.remove(to_remove)
		mods.remove(to_remove)

	#add participant with owner client
	print("Inviting " + participant_client.user.me().name)
	subreddit.moderator.invite(participant_client.user.me(), ['access','flair','mail','posts'])

	#accept invite with participant client
	print("Accepting for " +participant_client.user.me().name)
	temp_sub = participant_client.subreddit(subreddit.display_name)
	temp_sub.mod.accept_invite()
	#After this point, all refereces to the client are lost and will be garbage-collected

owner_client = praw.Reddit(
	client_id=CLIENT_ID,
	client_secret=CLIENT_SECRET,
	redirect_uri=REDIRECT_URI,
	username=Config.get('Reddit Access','username'),
	password=Config.get('Reddit Access','password'),
	user_agent='The Box Bot'
	)

owner = owner_client.user.me().name
subreddit = owner_client.subreddit(Config.get('Reddit Access','subreddit'))

print("User Auth")
print(owner_client.auth.url(participant_scope.split(' '), True))
app.run(debug=False, port=65010)
#==================================================END OAUTH APPROVAL-=============================================
