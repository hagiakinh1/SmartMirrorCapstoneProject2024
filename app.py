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
    i = 0
    for filename in os.listdir("./music"):
        f = os.path.join("./music", filename)
        print(f)
        if os.path.isfile(f):
            i = i + 1
            tag = TinyTag.get(f)
            dict_here.append({'id': i, 'name': tag.title, 'link': 'music/'+filename, 'genre': tag.genre, 'artist': tag.artist})


    #Dictionary to store music file information
    # dict_here = [
    #     {'id': 1, 'name': 'Acoustic Breeze', 'link': 'music/'+'acousticbreeze.mp3', 'genre': 'General', 'chill out': 5},
    #     {'id': 2, 'name': 'Happy Rock','link': 'music/'+'happyrock.mp3', 'genre': 'Bollywood', 'rating': 4},
    #     {'id': 3, 'name': 'Ukulele', 'link': 'music/'+'ukulele.mp3', 'genre': 'Bollywood', 'rating': 4}
    #     ]
    return dict_here

# Initialize Flask.
app = Flask(__name__)
socket = SocketIO(app)



class MusicController:
    playOrPause = False

    @staticmethod
    def playAndPause():
        
        if MusicController.playOrPause:
            socket.send("pause")
            MusicController.playOrPause = False
        else:
            socket.send("play")
            MusicController.playOrPause = True
        sleep(0.2)

mHandGesture = Main.HandGesture(MusicController.playAndPause)

#Route to render GUI
@app.route('/')
def show_entries():
    general_Data = {
        'title': 'Music Player'}
    # print(return_dict())
    stream_entries = return_dict()[0] #remember to set this to return_dict()[i] to switch song
    return render_template('design.html', entry=stream_entries, **general_Data)

#Route to stream music
@app.route('/<int:stream_id>')
def streammp3(stream_id):
    def generate():
        item = return_dict()[0] #remember to set this to return_dict()[i] to switch song
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
                
    return Response(generate(), mimetype="audio/mp3")
@socket.on('connect')
def on_connect(msg):
    print('Server received connection')

    t1 = threading.Thread(target=task)
    t1.start()
def task():
    mHandGesture.run()


#launch a Tornado server with HTTPServer.
if __name__ == "__main__":
    port = 5000
    http_server = HTTPServer(WSGIContainer(app))
    logging.debug("Started Server, Kindly visit http://localhost:" + str(port))
    http_server.listen(port)
    IOLoop.instance().start()
    socket.run(app)
    
