from flask import Flask, request, render_template, redirect, session
from flask_session import Session
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import spotipy.util as util
import mysql.connector
import os


#citation
#Authorization code is from https://github.com/spotipy-dev/spotipy/blob/master/examples/app.py



#global var
global sp
global info


#mySQL boilerplate
conn = mysql.connector.connect(host='localhost', password='Grant12549', user='root', database='musicwrap')
cursor = conn.cursor()


#Startup
#Flask Boilerplate
app = Flask(__name__)

app.config['SECRET_KEY'] = os.urandom(64)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session/'
Session(app)

@app.route('/', methods=['POST', 'GET'])
def hello_world():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    CLIENT_ID = "6935cdfb27164343bad89b9ee5128309"
    CLIENT_SECRET = "894aa7f0f33c4ac4be55664f5ea5d960"
    REDIRECT_URI = "https://anchovy-emerging-definitely.ngrok-free.app/"
    auth_manager = spotipy.oauth2.SpotifyOAuth(scope='user-read-currently-playing playlist-modify-private',client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI,
                                               cache_handler=cache_handler,
                                               show_dialog=True)
    if request.args.get("code"):
        # Step 2. Being redirected from Spotify auth page
        auth_manager.get_access_token(request.args.get("code"))
        return redirect('/')

    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        # Step 1. Display sign in link when no token
        auth_url = auth_manager.get_authorize_url()
        return f'<h2><a href="{auth_url}">Sign in</a></h2>'
    spotify = spotipy.Spotify(auth_manager=auth_manager)

    return (spotify.me()["display_name"])


#Continue with Spotify
#Spotify Authorization Code Flow
@app.route('/home', methods=['POST', 'GET'])
def login():
    global sp
    global info
    CLIENT_ID = "6935cdfb27164343bad89b9ee5128309"
    CLIENT_SECRET = "894aa7f0f33c4ac4be55664f5ea5d960"
    REDIRECT_URI = "http://localhost:8000"
    scope = "playlist-read-private playlist-read-collaborative user-library-read user-modify-playback-state"
    token = util.prompt_for_user_token(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI, show_dialog=True, scope=scope)
    if token:
        sp = spotipy.Spotify(auth=token)
    info = sp.me()

    cursor.execute("SELECT wrap_name FROM wraps WHERE spotify_id = '" + info['id'] + "';")
    nlist = []
    for wrap_name in cursor:
        wrap_name = str(wrap_name)
        wrap_name = wrap_name.replace("('", "")
        wrap_name = wrap_name.replace("',)", "")
        nlist.append(wrap_name)
    return render_template("home.html", name=info['display_name'], pfp=info['images'][1]['url'], strings_array = nlist)


#CREATE NEW WRAP
@app.route('/newWrap', methods=['POST', 'GET'])
def newWrap():
    global info
    wrapName = request.form['wrapName']
    print("INSERT INTO wraps(spotify_id, wrap_name) VALUES('" + info['id'] + "', '" + wrapName + "')")
    cursor.execute("INSERT INTO wraps(spotify_id, wrap_name) VALUES('" + info['id'] + "', '" + wrapName + "')")
    conn.commit()
    cursor.execute("SELECT wrap_name FROM wraps WHERE spotify_id = '" + info['id'] + "';")
    nlist = []
    for wrap_name in cursor:
        wrap_name = str(wrap_name)
        wrap_name = wrap_name.replace("('", "")
        wrap_name = wrap_name.replace("',)", "")
        nlist.append(wrap_name)

    return render_template("home.html", strings_array = nlist, name=info['display_name'], pfp=info['images'][1]['url'])


#OPEN (X) WRAP
@app.route('/openWrap', methods=['POST', 'GET'])
def openWrap():
    request.form['selected_item']
    return(render_template("builder.html"))

#ADD PLAYLIST
@app.route('/addPlaylist', methods=['POST', 'GET'])
def addPlaylist():
    return("wowie")

#DELETE WRAP
@app.route('/deleteWrap', methods=['POST', 'GET'])
def deleteWrap():
    global info
    toDelete = request.form['selected_item']
    toDelete = toDelete.replace("('", "")
    toDelete = toDelete.replace("',)", "")
    cursor.execute("DELETE FROM wraps WHERE spotify_id = '" + info['id'] + "' AND wrap_name = '" + toDelete + "';")
    conn.commit()

    cursor.execute("SELECT wrap_name FROM wraps WHERE spotify_id = '" + info['id'] + "';")
    nlist = []
    for wrap_name in cursor:
        wrap_name = str(wrap_name)
        wrap_name = wrap_name.replace("('", "")
        wrap_name = wrap_name.replace("',)", "")
        nlist.append(wrap_name)
    return render_template("home.html", strings_array = nlist, name=info['display_name'], pfp=info['images'][1]['url'])



#Flask Boilerplate
if __name__=='__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8000)



