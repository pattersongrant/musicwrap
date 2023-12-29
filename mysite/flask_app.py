from flask import Flask, request, render_template, redirect, session
from flask_session import Session
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import spotipy.util as util
import mysql.connector
import os
from dotenv import load_dotenv, find_dotenv
import hashlib
load_dotenv(find_dotenv())

#citation
#Authorization code is from https://github.com/spotipy-dev/spotipy/blob/master/examples/app.py



#mySQL boilerplate
#conn = mysql.connector.connect(host='musicwrap.mysql.pythonanywhere-services.com', password='MySQL123$sleep11', user='musicwrap', database='musicwrap$default')
#cursor = conn.cursor(buffered=True)
class DB:
  conn = None

  def connect(self):
    self.conn = mysql.connector.connect(host='musicwrap.mysql.pythonanywhere-services.com', password='MySQL123$sleep11', user='musicwrap', database='musicwrap$default')
  def commit(self):
    self.conn.commit()
  def query(self, sql):
    try:
      cursor = self.conn.cursor()
      cursor.execute(sql)
    except:
      self.connect()
      cursor = self.conn.cursor()
      cursor.execute(sql)
    return cursor


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
    db = DB()
    load_dotenv(find_dotenv())
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(scope='user-modify-playback-state',
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
    sql = "SELECT wrap_name FROM wraps WHERE spotify_id = '" + info['id'] + "';"
    cursor = db.query(sql)
    nlist = []
    num = 0
    for wrap_name in cursor:
        wrap_name = str(wrap_name)
        wrap_name = wrap_name.replace("('", "")
        wrap_name = wrap_name.replace("',)", "")
        nlist.append(wrap_name)
        num+=1
    session['errorCode'] = ''
    session['shareCode'] = ''
    try:
        pfp1=info['images'][1]['url']
    except:
        pfp1="https://i.scdn.co/image/ab6761610000e5eba1b1a48354e9a91fef58f651"
    return render_template("home.html", name=info['display_name'], pfp=pfp1, strings_array = nlist, num=num)

#CLICK ABOUT
@app.route('/about', methods=['POST', 'GET'])
def showAbout():
    return render_template("about.html")

#CLICK TUTORIAL
@app.route('/tutorial', methods=['POST', 'GET'])
def showTutorial():
    return render_template("tutorial.html")

#Privacy Policy
@app.route('/privacy', methods=['POST', 'GET'])
def showPrivacy():
    return render_template("privacy.html")

#SIGN OUT
@app.route('/sign_out', methods=['POST', 'GET'])
def sign_out():
    session.pop("token_info", None)
    return redirect('/')

#CREATE NEW WRAP
@app.route('/newWrap', methods=['POST', 'GET'])
def newWrap():
    db = DB()
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    info = spotify.me()

    wrapName = request.form['wrapName']
    nlist = []
    try:
        db.query("CREATE TABLE " + (wrapName + "sp0tify92id" + info['id']) + " (spotify_id TEXT, row_id INT AUTO_INCREMENT, playlist VARCHAR(1000), background VARCHAR(1000), PRIMARY KEY(row_id));")
        db.query("INSERT INTO wraps(spotify_id, wrap_name) VALUES('" + info['id'] + "', '" + wrapName + "')")
        db.commit()
    except:
        session['errorCode'] = "Error: Invalid Name(Special Characters/Spaces/Duplicate Name?)"
    else:
        session['errorCode'] = ""
    cursor = db.query("SELECT wrap_name FROM wraps WHERE spotify_id = '" + info['id'] + "';")
    num=0
    for wrap_name in cursor:
        wrap_name = str(wrap_name)
        wrap_name = wrap_name.replace("('", "")
        wrap_name = wrap_name.replace("',)", "")
        nlist.append(wrap_name)
        num+=1
    try:
        pfp1=info['images'][1]['url']
    except:
        pfp1="https://i.scdn.co/image/ab6761610000e5eba1b1a48354e9a91fef58f651"
    return render_template("home.html", strings_array = nlist, name=info['display_name'], pfp=pfp1, errorCode=session['errorCode'], num=num)

#OPEN (X) WRAP
@app.route('/openWrap', methods=['POST', 'GET'])
def openWrap():
    db = DB()
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
    cursor = db.query("SELECT playlist FROM " + (current_wrap + "sp0tify92id" + info['id']) + ";")
    for playlist in cursor:
        playlist = str(playlist)
        playlist = playlist.replace("('", "")
        playlist = playlist.replace("',)", "")
        playlists_array.append(playlist)
        try:
            covers_array.append(spotify.playlist_cover_image(playlist)[0]['url'])
        except:
            covers_array.append("https://community.spotify.com/t5/image/serverpage/image-id/25294i2836BD1C1A31BDF2/image-size/original?v=mpbl-1&px=-1")
        results = spotify.user_playlist(user=None, playlist_id=playlist, fields="name")
        names_array.append(results["name"])
    bg=""
    cursor = db.query("SELECT background FROM " + (current_wrap + "sp0tify92id" + info['id']) + " WHERE row_id=1;")
    for background in cursor:
        background = str(background)
        background = background.replace("('", "")
        background = background.replace("',)", "")
        bg = background
    return render_template("builder.html", current=current_wrap, playlists_array=playlists_array,covers_array=covers_array,background=bg, names_array=names_array)

#ADD PLAYLIST
@app.route('/addPlaylist', methods=['POST', 'GET'])
def addPlaylist():
    db = DB()
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    info = spotify.me()
    newPlaylist = request.form['newPlaylist']
    newPlaylist = str(newPlaylist)
    current_wrap = request.form['selected_item']

    db.query("INSERT INTO " + (current_wrap + "sp0tify92id" + info['id']) + "(playlist) VALUES('" + newPlaylist + "');")
    db.commit()
    #playlists_array=[]
    #covers_array=[]
    #db.query("SELECT playlist FROM " + (current_wrap + "sp0tify92id" + info['id']) + ";")
    #for playlist in cursor:
    #    playlist = str(playlist)
    #    playlists_array.append(playlist)
    #    #covers_array.append(spotify.playlist_cover_image(playlist)[0]['url'])
    return redirect('/reloadBuild')

#ADD BACKGROUND
@app.route('/addBackground', methods=['POST', 'GET'])
def addBackground():
    db = DB()
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    info = spotify.me()
    newBackground = request.form['newBackground']
    newBackground = str(newBackground)
    current_wrap = request.form['selected_item']

    db.query("UPDATE " + (current_wrap + "sp0tify92id" + info['id']) + " SET background = '" + newBackground + "' WHERE row_id=1;")
    db.commit()
    #playlists_array=[]
    #covers_array=[]
    #db.query("SELECT playlist FROM " + (current_wrap + "sp0tify92id" + info['id']) + ";")
    #for playlist in cursor:
    #    playlist = str(playlist)
    #    playlists_array.append(playlist)
    #    #covers_array.append(spotify.playlist_cover_image(playlist)[0]['url'])
    return redirect('/reloadBuild')

#DELETE WRAP
@app.route('/deleteWrap', methods=['POST', 'GET'])
def deleteWrap():
    db = DB()
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    info = spotify.me()

    toDelete = request.form['selected_item']
    toDelete = toDelete.replace("('", "")
    toDelete = toDelete.replace("',)", "")
    db.query("DELETE FROM wraps WHERE spotify_id = '" + info['id'] + "' AND wrap_name = '" + toDelete + "';")
    db.query("DROP TABLE " + (toDelete + "sp0tify92id" + info['id']) + ";")
    db.commit()

    cursor = db.query("SELECT wrap_name FROM wraps WHERE spotify_id = '" + info['id'] + "';")
    nlist = []
    num=0
    for wrap_name in cursor:
        wrap_name = str(wrap_name)
        wrap_name = wrap_name.replace("('", "")
        wrap_name = wrap_name.replace("',)", "")
        nlist.append(wrap_name)
        num+=1
    try:
        pfp1=info['images'][1]['url']
    except:
        pfp1="https://i.scdn.co/image/ab6761610000e5eba1b1a48354e9a91fef58f651"

    return render_template("home.html", strings_array = nlist, name=info['display_name'], pfp=pfp1, num=num)

#CLICK PLAYLIST
@app.route('/startPlayback', methods=['POST', 'GET'])
def startPlayback():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    #info = spotify.me()
    print("started playing!")
    try:
        spotify.start_playback(context_uri=str(request.form['playlist_item']))
    except:
        session['errorCode'] = "Error: Need an Active Device (Go hit play on any spotify device!) OR You need Spotify Premium"
    else:
        session['errorCode'] = ""
    return redirect('/reloadBuild')

#GENERATE SHARE LINK
@app.route('/generateCode', methods=['POST', 'GET'])
def generateCode():
    db = DB()
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    info = spotify.me()
    serialized_obj = str(session['current_wrap'] + "sp0tify92id" + info['id'])  # Serialize the object (you might need to customize this)
    hash_value = hashlib.sha256(serialized_obj.encode()).hexdigest()
    db.query("UPDATE wraps SET list_playlists = '"+ str(hash_value) +"' WHERE spotify_id = '" + str(info['id']) + "' AND wrap_name = '" + str(session['current_wrap']) + "' ;")
    db.commit()
    session['shareCode'] = ("https://musicwrap.pythonanywhere.com/view/" + hash_value)
    return redirect('/reloadBuild')

#OPENED SHARE LINK
@app.route('/view/<hash_value>')
def showWrap(hash_value):
    db = DB()
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    #info = spotify.me()
    current_wrap2 = ''
    cursor = db.query("SELECT wrap_name FROM wraps WHERE list_playlists ='" + hash_value + "';")
    for wrap_name in cursor:
        current_wrap=str(wrap_name)
        current_wrap = current_wrap.replace("('", "")
        current_wrap = current_wrap.replace("',)", "")
        current_wrap2=current_wrap
    spotid=''
    cursor = db.query("SELECT spotify_id FROM wraps WHERE list_playlists ='" + hash_value + "';")
    for spotify_id in cursor:
        spid = str(spotify_id)
        spid = spid.replace("('", "")
        spid = spid.replace("',)", "")
        spotid=spid
    playlists_array=[]
    covers_array=[]
    names_array=[]
    cursor = db.query("SELECT playlist FROM " + (current_wrap2 + "sp0tify92id" + spotid) + ";")
    for playlist in cursor:
        playlist = str(playlist)
        playlist = playlist.replace("('", "")
        playlist = playlist.replace("',)", "")
        playlists_array.append(playlist)
        try:
            covers_array.append(spotify.playlist_cover_image(playlist)[0]['url'])
        except:
            covers_array.append("https://community.spotify.com/t5/image/serverpage/image-id/25294i2836BD1C1A31BDF2/image-size/original?v=mpbl-1&px=-1")
        results = spotify.user_playlist(user=None, playlist_id=playlist, fields="name")
        names_array.append(results["name"])
        print(spotify.playlist_cover_image(playlist)[0]['url'])
    bg=""
    cursor = db.query("SELECT background FROM " + (current_wrap2 + "sp0tify92id" + spotid) + " WHERE row_id=1;")
    for background in cursor:
        background = str(background)
        background = background.replace("('", "")
        background = background.replace("',)", "")
        bg = background
    session['currentlyViewing'] = hash_value
    session['shareCode'] = ''
    return render_template("viewer.html", current=current_wrap, names_array=names_array, playlists_array=playlists_array,covers_array=covers_array, errorCode=session['errorCode'], background=bg)


#VIEWER CLICK PLAYLIST
@app.route('/viewerPlayback', methods=['POST', 'GET'])
def viewerPlayback():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    #info = spotify.me()
    print("started playing!")
    try:
        spotify.start_playback(context_uri=str(request.form['playlist_item']))
    except:
        session['errorCode'] = "Error: Need an Active Device (Go hit play on any spotify device!) OR You need Spotify Premium"
    else:
        session['errorCode'] = ""
    return redirect('/view/' + session['currentlyViewing'])

#reloadbuilder
@app.route('/reloadBuild')
def reload():
    db = DB()
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    info = spotify.me()
    current_wrap = session['current_wrap']
    playlists_array=[]
    covers_array=[]
    names_array=[]
    cursor = db.query("SELECT playlist FROM " + (current_wrap + "sp0tify92id" + info['id']) + ";")
    for playlist in cursor:
        playlist = str(playlist)
        playlist = playlist.replace("('", "")
        playlist = playlist.replace("',)", "")
        playlists_array.append(playlist)
        try:
            covers_array.append(spotify.playlist_cover_image(playlist)[0]['url'])
        except:
            covers_array.append("https://community.spotify.com/t5/image/serverpage/image-id/25294i2836BD1C1A31BDF2/image-size/original?v=mpbl-1&px=-1")
        results = spotify.user_playlist(user=None, playlist_id=playlist, fields="name")
        names_array.append(results["name"])
        print(spotify.playlist_cover_image(playlist)[0]['url'])
    bg=""
    cursor = db.query("SELECT background FROM " + (current_wrap + "sp0tify92id" + info['id']) + " WHERE row_id=1;")
    for background in cursor:
        background = str(background)
        background = background.replace("('", "")
        background = background.replace("',)", "")
        bg = background
    return render_template("builder.html", current=current_wrap, names_array=names_array, playlists_array=playlists_array,covers_array=covers_array, errorCode=session['errorCode'],background=bg, shareCode=session['shareCode'])

#Flask Boilerplate
#if __name__=='__main__':
#    app.debug = True
#    app.run(host='0.0.0.0', port=8000)



