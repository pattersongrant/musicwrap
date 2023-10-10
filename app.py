from flask import Flask, request, render_template, redirect, session
from flask_session import Session
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import spotipy.util as util
import mysql.connector
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

#citation
#Authorization code is from https://github.com/spotipy-dev/spotipy/blob/master/examples/app.py


#mySQL boilerplate
conn = mysql.connector.connect(host='localhost', password='Grant12549', user='root', database='musicwrap')
cursor = conn.cursor(buffered=True)


#Startup
#Flask Boilerplate
app = Flask(__name__)

app.config['SECRET_KEY'] = os.urandom(64)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session/'
Session(app)

@app.route('/', methods=['POST', 'GET'])
def hello_world():
    load_dotenv(find_dotenv())
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    #CLIENT_ID = "6935cdfb27164343bad89b9ee5128309"
    #CLIENT_SECRET = "894aa7f0f33c4ac4be55664f5ea5d960"
    #REDIRECT_URI = "https://anchovy-emerging-definitely.ngrok-free.app/"
    
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
    return render_template("home.html", name=info['display_name'], pfp=info['images'][1]['url'], strings_array = nlist)

@app.route('/sign_out', methods=['POST', 'GET'])
def sign_out():
    session.pop("token_info", None)
    return redirect('/')
#Continue with Spotify
#Spotify Authorization Code Flow
#@app.route('/home', methods=['POST', 'GET'])
#def login():
#    #global sp
#    #global info
#    #CLIENT_ID = "6935cdfb27164343bad89b9ee5128309"
#    #CLIENT_SECRET = "894aa7f0f33c4ac4be55664f5ea5d960"
#    #REDIRECT_URI = "http://localhost:8000"
#    #scope = "playlist-read-private playlist-read-collaborative user-library-read user-modify-playback-state"
#    #token = util.prompt_for_user_token(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI, show_dialog=True, scope=scope)
#    #if token:
#    #    sp = spotipy.Spotify(auth=token)
#    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
#    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
#    if not auth_manager.validate_token(cache_handler.get_cached_token()):
#        return redirect('/')
#    spotify = spotipy.Spotify(auth_manager=auth_manager)
#    info = spotify.me()
#
#    cursor.execute("SELECT wrap_name FROM wraps WHERE spotify_id = '" + info['id'] + "';")
#    nlist = []
#    for wrap_name in cursor:
#        wrap_name = str(wrap_name)
#        wrap_name = wrap_name.replace("('", "")
#        wrap_name = wrap_name.replace("',)", "")
#        nlist.append(wrap_name)
#    return render_template("home.html", name=info['display_name'], pfp=info['images'][1]['url'], strings_array = nlist)


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
        session['errorCode'] = "Error: Invalid Name(Special Characters, Spaces?)"
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
        session['errorCode'] = "Error: Need an Active Device"
    else:
        session['errorCode'] = ""
    return redirect('/reloadBuild')

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
    return render_template("builder.html", current=current_wrap, playlists_array=playlists_array,covers_array=covers_array, errorCode=session['errorCode'],background=bg)
    
#Flask Boilerplate
if __name__=='__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=8000)



