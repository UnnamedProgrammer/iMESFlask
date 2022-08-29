from iMES import app,socketio,host,port


if __name__ == "__main__":
    socketio.run(app,host="192.168.118.41",port=5000,debug=True)