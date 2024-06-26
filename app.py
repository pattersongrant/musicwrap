from flask import Flask, request, render_template, redirect, session
from flask_session import Session
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import spotipy.util as util
import mysql.connector
import os
from dotenv import load_dotenv, find_dotenv
import hashlib
#For PA deployement:
#add below code; turn all cursor.execute into DB.query;Remove inital connection code thing
#class DB:
#  conn = None
#
#  def connect(self):
#    self.conn = mysql.connector.connect(host='localhost', password='password', user='root', database='musicwrap')
#
#  def query(self, sql):
#    try:
#      cursor = self.conn.cursor()
#      cursor.execute(sql)
#    except:
#      self.connect()
#      cursor = self.conn.cursor()
#      cursor.execute(sql)
#    return cursor

load_dotenv(find_dotenv())


#citation
#Authorization code is from https://github.com/spotipy-dev/spotipy/blob/master/examples/app.py


#mySQL boilerplate
conn = mysql.connector.connect(host='localhost', password='password', user='root', database='musicwrap')
cursor = conn.cursor(buffered=True)

#Startup
#Flask Boilerplate
app = Flask(__name__)

app.config['SECRET_KEY'] = os.urandom(64)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session/'
Session(app)

#STARTUP/MAIN REDIRECT
@app.route('/', methods=['POST', 'GET'])
def hello_world():
    load_dotenv(find_dotenv())
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)    
    auth_manager = spotipy.oauth2.SpotifyOAuth(scope='playlist-read-private playlist-read-collaborative user-library-read user-modify-playback-state user-read-currently-playing user-read-playback-state',
                                               cache_handler=cache_handler,
                                               show_dialog=True)
    if request.args.get("code"):
        # Step 2. Being redirected from Spotify auth page
        auth_manager.get_access_token(request.args.get("code"))
        return redirect('/')

    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        # Step 1. Display sign in link when no token
        auth_url = auth_manager.get_authorize_url()
        #return f'<h2><a href="{auth_url}">Sign in</a></h2>'
        return render_template("login.html", auth=auth_url)
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    info = spotify.me()
    cursor.execute("SELECT wrap_name FROM wraps WHERE spotify_id = '" + info['id'] + "';")
    nlist = []
    for wrap_name in cursor:
        wrap_name = str(wrap_name)
        wrap_name = wrap_name.replace("('", "")
        wrap_name = wrap_name.replace("',)", "")
        nlist.append(wrap_name)
    session['errorCode'] = ''
    session['shareCode'] = ''
    return render_template("home.html", name=info['display_name'], pfp=info['images'][1]['url'], strings_array = nlist)

#CLICK ABOUT
@app.route('/about', methods=['POST', 'GET'])
def showAbout():
    return render_template("about.html")

#SIGN OUT
@app.route('/sign_out', methods=['POST', 'GET'])
def sign_out():
    session.pop("token_info", None)
    return redirect('/')

#CREATE NEW WRAP
@app.route('/newWrap', methods=['POST', 'GET'])
def newWrap():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    info = spotify.me()

    wrapName = request.form['wrapName']
    nlist = []
    try:
        cursor.execute("CREATE TABLE " + (wrapName + "sp0tify92id" + info['id']) + " (spotify_id TEXT, row_id INT AUTO_INCREMENT, playlist VARCHAR(1000), background VARCHAR(1000), PRIMARY KEY(row_id));")
        cursor.execute("INSERT INTO wraps(spotify_id, wrap_name) VALUES('" + info['id'] + "', '" + wrapName + "')")
        conn.commit()
        conn.commit()
    except:
        session['errorCode'] = "Error: Invalid Name(Special Characters/Spaces/Duplicate Name?)"
    else:
        session['errorCode'] = ""
    cursor.execute("SELECT wrap_name FROM wraps WHERE spotify_id = '" + info['id'] + "';")
    for wrap_name in cursor:
        wrap_name = str(wrap_name)
        wrap_name = wrap_name.replace("('", "")
        wrap_name = wrap_name.replace("',)", "")
        nlist.append(wrap_name)
    return render_template("home.html", strings_array = nlist, name=info['display_name'], pfp=info['images'][1]['url'], errorCode=session['errorCode'])

#OPEN (X) WRAP
@app.route('/openWrap', methods=['POST', 'GET'])
def openWrap():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    info = spotify.me()
    current_wrap = request.form['selected_item']
    session['current_wrap'] = current_wrap
    playlists_array=[]
    covers_array=[]
    names_array=[]
    cursor.execute("SELECT playlist FROM " + (current_wrap + "sp0tify92id" + info['id']) + ";")
    for playlist in cursor:
        playlist = str(playlist)
        playlist = playlist.replace("('", "")
        playlist = playlist.replace("',)", "")
        playlists_array.append(playlist) 
        covers_array.append(spotify.playlist_cover_image(playlist)[0]['url'])
        results = spotify.user_playlist(playlist_id=playlist, fields="name")
        names_array.append(results["name"])
        print(spotify.playlist_cover_image(playlist)[0]['url'])
    bg=""
    cursor.execute("SELECT background FROM " + (current_wrap + "sp0tify92id" + info['id']) + " WHERE row_id=1;")
    for background in cursor:
        background = str(background)
        background = background.replace("('", "")
        background = background.replace("',)", "")
        bg = background
    return render_template("builder.html", current=current_wrap, playlists_array=playlists_array,covers_array=covers_array,background=bg)

#ADD PLAYLIST
@app.route('/addPlaylist', methods=['POST', 'GET'])
def addPlaylist():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    info = spotify.me()
    newPlaylist = request.form['newPlaylist']
    newPlaylist = str(newPlaylist)
    current_wrap = request.form['selected_item']
    
    cursor.execute("INSERT INTO " + (current_wrap + "sp0tify92id" + info['id']) + "(playlist) VALUES('" + newPlaylist + "');")
    conn.commit()
    #playlists_array=[]
    #covers_array=[]
    #cursor.execute("SELECT playlist FROM " + (current_wrap + "sp0tify92id" + info['id']) + ";")
    #for playlist in cursor:
    #    playlist = str(playlist)
    #    playlists_array.append(playlist) 
    #    #covers_array.append(spotify.playlist_cover_image(playlist)[0]['url'])
    return redirect('/reloadBuild')

#ADD BACKGROUND
@app.route('/addBackground', methods=['POST', 'GET'])
def addBackground():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    info = spotify.me()
    newBackground = request.form['newBackground']
    newBackground = str(newBackground)
    current_wrap = request.form['selected_item']

    cursor.execute("UPDATE " + (current_wrap + "sp0tify92id" + info['id']) + " SET background = '" + newBackground + "' WHERE row_id=1;")
    conn.commit()
    #playlists_array=[]
    #covers_array=[]
    #cursor.execute("SELECT playlist FROM " + (current_wrap + "sp0tify92id" + info['id']) + ";")
    #for playlist in cursor:
    #    playlist = str(playlist)
    #    playlists_array.append(playlist) 
    #    #covers_array.append(spotify.playlist_cover_image(playlist)[0]['url'])
    return redirect('/reloadBuild')

#DELETE WRAP
@app.route('/deleteWrap', methods=['POST', 'GET'])
def deleteWrap():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    info = spotify.me()

    toDelete = request.form['selected_item']
    toDelete = toDelete.replace("('", "")
    toDelete = toDelete.replace("',)", "")
    cursor.execute("DELETE FROM wraps WHERE spotify_id = '" + info['id'] + "' AND wrap_name = '" + toDelete + "';")
    cursor.execute("DROP TABLE " + (toDelete + "sp0tify92id" + info['id']) + ";")
    conn.commit()

    cursor.execute("SELECT wrap_name FROM wraps WHERE spotify_id = '" + info['id'] + "';")
    nlist = []
    for wrap_name in cursor:
        wrap_name = str(wrap_name)
        wrap_name = wrap_name.replace("('", "")
        wrap_name = wrap_name.replace("',)", "")
        nlist.append(wrap_name)
    
    
    return render_template("home.html", strings_array = nlist, name=info['display_name'], pfp=info['images'][1]['url'])

#CLICK PLAYLIST
@app.route('/startPlayback', methods=['POST', 'GET'])
def startPlayback():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    info = spotify.me()
    print("started playing!")
    try:
        spotify.start_playback(context_uri=str(request.form['playlist_item']))
    except:
        session['errorCode'] = "Error: Need an Active Device (Go hit play on any spotify device!)"
    else:
        session['errorCode'] = ""
    return redirect('/reloadBuild')

#GENERATE SHARE LINK
@app.route('/generateCode', methods=['POST', 'GET'])
def generateCode():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    info = spotify.me()
    serialized_obj = str(session['current_wrap'] + "sp0tify92id" + info['id'])  # Serialize the object (you might need to customize this)
    hash_value = hashlib.sha256(serialized_obj.encode()).hexdigest()
    cursor.execute("UPDATE wraps SET list_playlists = '"+ str(hash_value) +"' WHERE spotify_id = '" + str(info['id']) + "' AND wrap_name = '" + str(session['current_wrap']) + "' ;")
    conn.commit()
    session['shareCode'] = ("https://anchovy-emerging-definitely.ngrok-free.app/view/" + hash_value)
    return redirect('/reloadBuild')

#OPENED SHARE LINK
@app.route('/view/<hash_value>')
def showWrap(hash_value):
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    info = spotify.me()

    current_wrap2 = ''
    cursor.execute("SELECT wrap_name FROM wraps WHERE list_playlists ='" + hash_value + "';")
    for wrap_name in cursor:
        current_wrap=str(wrap_name)
        current_wrap = current_wrap.replace("('", "")
        current_wrap = current_wrap.replace("',)", "")
        current_wrap2=current_wrap
    spotid=''
    cursor.execute("SELECT spotify_id FROM wraps WHERE list_playlists ='" + hash_value + "';")
    for spotify_id in cursor:
        spid = str(spotify_id)
        spid = spid.replace("('", "")
        spid = spid.replace("',)", "")
        spotid=spid
    playlists_array=[]
    covers_array=[]
    cursor.execute("SELECT playlist FROM " + (current_wrap2 + "sp0tify92id" + spotid) + ";")
    for playlist in cursor:
        playlist = str(playlist)
        playlist = playlist.replace("('", "")
        playlist = playlist.replace("',)", "")
        playlists_array.append(playlist) 
        covers_array.append(spotify.playlist_cover_image(playlist)[0]['url'])
        print(spotify.playlist_cover_image(playlist)[0]['url'])
    bg=""
    cursor.execute("SELECT background FROM " + (current_wrap2 + "sp0tify92id" + spotid) + " WHERE row_id=1;")
    for background in cursor:
        background = str(background)
        background = background.replace("('", "")
        background = background.replace("',)", "")
        bg = background
    session['currentlyViewing'] = hash_value
    session['shareCode'] = ''
    return render_template("viewer.html", current=current_wrap, playlists_array=playlists_array,covers_array=covers_array, errorCode=session['errorCode'], background=bg)

#VIEWER CLICK PLAYLIST
@app.route('/viewerPlayback', methods=['POST', 'GET'])
def viewerPlayback():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    info = spotify.me()
    print("started playing!")
    try:
        spotify.start_playback(context_uri=str(request.form['playlist_item']))
    except:
        session['errorCode'] = "Error: Need an Active Device (Go hit play on any spotify device!)"
    else:
        session['errorCode'] = ""
    return redirect('/view/' + session['currentlyViewing'])

#reloadbuilder
@app.route('/reloadBuild')
def reload():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    info = spotify.me()
    current_wrap = session['current_wrap']
    playlists_array=[]
    covers_array=[]
    cursor.execute("SELECT playlist FROM " + (current_wrap + "sp0tify92id" + info['id']) + ";")
    for playlist in cursor:
        playlist = str(playlist)
        playlist = playlist.replace("('", "")
        playlist = playlist.replace("',)", "")
        playlists_array.append(playlist) 
        covers_array.append(spotify.playlist_cover_image(playlist)[0]['url'])
        print(spotify.playlist_cover_image(playlist)[0]['url'])
    bg=""
    cursor.execute("SELECT background FROM " + (current_wrap + "sp0tify92id" + info['id']) + " WHERE row_id=1;")
    for background in cursor:
        background = str(background)
        background = background.replace("('", "")
        background = background.replace("',)", "")
        bg = background
    return render_template("builder.html", current=current_wrap, playlists_array=playlists_array,covers_array=covers_array, errorCode=session['errorCode'],background=bg, shareCode=session['shareCode'])
    
#Flask Boilerplate
if __name__=='__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8000)



