from flask import Flask, request, render_template
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import spotipy.util as util
import mysql.connector

#global var
global sp
global info


#mySQL boilerplate
conn = mysql.connector.connect(host='localhost', password='Grant12549', user='root', database='musicwrap')
cursor = conn.cursor()


#Startup
#Flask Boilerplate
app = Flask(__name__)
@app.route('/', methods=['POST', 'GET'])
def hello_world():
    return render_template("login.html")


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
    return(request.form['selected_item'])


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



