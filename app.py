from flask import Flask,render_template, Response
import sys
# Tornado web server
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tinytag import TinyTag
from flask_socketio import SocketIO
from time import sleep
import threading
from lib.hand_gesture_control import Main
import json

#Debug logger
import logging 
root = logging.getLogger()
root.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)

import os

def return_dict():
    dict_here = []
    i = 1
    for filename in os.listdir("./music"):
        f = os.path.join("./music", filename)
        print(f)
        if os.path.isfile(f):
            tag = TinyTag.get(f)
            dict_here.append({ "id": i, "name": tag.title, "link": "music/"+filename, "genre": tag.genre, "artist": tag.artist})
            print(dict_here)
            i = i + 1
    return dict_here

# Initialize Flask.
app = Flask(__name__)
socket = SocketIO(app)



class MusicController:
    playOrPause = False
    currentSongIndex=1
    debounceTime = 0.3

    @staticmethod
    def playAndPause():
        
        if MusicController.playOrPause:
            socket.send("pause")
            MusicController.playOrPause = False
        else:
            socket.send("play")
            MusicController.playOrPause = True
        sleep(MusicController.debounceTime)
    @staticmethod
    def nextSong():
        if MusicController.currentSongIndex < len(return_dict()):
            MusicController.currentSongIndex = MusicController.currentSongIndex + 1
        else :
            MusicController.currentSongIndex = 1
        x =  '''{ "type":"changeSong", "songId":"''' + str(MusicController.currentSongIndex) + '''"}'''
        socket.emit( 'message', json.loads(x))
        
        
        sleep(MusicController.debounceTime)
    
    @staticmethod
    def previousSong():
        if MusicController.currentSongIndex > 1:
            MusicController.currentSongIndex = MusicController.currentSongIndex - 1
            x =  '''{ "type":"changeSong", "songId":"''' + str(MusicController.currentSongIndex) + '''"}'''
            socket.emit( 'message', json.loads(x))
            
        sleep(MusicController.debounceTime)
    @staticmethod
    def updateSongMetadata():
        socket.emit( 'updateMetaData', json.loads(json.dumps(return_dict()[MusicController.currentSongIndex -1])) )    
        # socket.send("asdnajsdk")
mHandGesture = Main.HandGesture(MusicController.playAndPause, MusicController.nextSong, MusicController.previousSong)

#Route to render GUI
@app.route('/')
def show_entries():
    general_Data = {
        'title': 'Music Player'}
    # print(return_dict())
    stream_entries = return_dict()[0] #remember to set this to return_dict()[i] to switch song
    socket.emit( 'updateMetaData', json.loads(json.dumps(stream_entries)) )
    print(json.loads(json.dumps(stream_entries)))
    return render_template('design.html', entry=stream_entries, **general_Data)


#Route to stream music
@app.route('/<int:stream_id>')
def streammp3(stream_id):
    def generate(stream_id):
        item = return_dict()[stream_id - 1] #remember to set this to return_dict()[i] to switch song
        count = 1
        if item['id'] == stream_id:
            song = item['link']
        with open(song, "rb") as fwav:
            data = fwav.read(1024)
            while data:
                yield data
                data = fwav.read(1024)
                logging.debug('Music data fragment : ' + str(count))
                count += 1
                
    return Response(generate(stream_id), mimetype="audio/mp3")
@socket.on('connect')
def on_connect(msg):
    print('Server received connection')

    t1 = threading.Thread(target=task)
    t1.start()

@socket.on('message')
def onSongChange(msg):
    if msg == "onSongChange":
        MusicController.updateSongMetadata()
def task():
    mHandGesture.run()


if __name__ == "__main__":
    socket.run(app)
    
