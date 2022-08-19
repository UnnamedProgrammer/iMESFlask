from iMES import app,socketio,host,port


if __name__ == "__main__":
    socketio.run(app,host=host,port=port,debug=True)