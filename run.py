from iMES import app,socketio,host,port
from iMES.Controller.ShiftTaskDaemon import ShiftTaskDaemon




if __name__ == "__main__":
    ShiftTaskMonitoring = ShiftTaskDaemon().Start()
    socketio.run(app,host=host,port=port,debug=True)