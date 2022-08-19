from iMES import socketio
from iMES import app
from flask_socketio import SocketIO


if __name__ == "__main__":
    socketio.run(app, host='192.168.118.81', port=8080, debug=True)