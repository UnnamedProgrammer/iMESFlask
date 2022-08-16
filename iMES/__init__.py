from flask_socketio import SocketIO
from flask import Flask
from flask_login import LoginManager
from iMES.Controller.UserCountController import UserCountController
from iMES.Model.SQLManipulator import SQLManipulator



app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.login_message_category = "info"
login_manager.init_app(app=app)
UserController = UserCountController()
OperatorAdjusterAtTerminals = {}
sqldevices = """
                SELECT[DeviceId]
                FROM [MES_Iplast].[dbo].[Device]
            """
Devices = SQLManipulator.SQLExecute(sqldevices)
for device in Devices:
    OperatorAdjusterAtTerminals[device[0]] = {"Оператор":'',"Наладчик":''}
from iMES.View.index import index
from iMES.View.menu import menu
from iMES.View.operator import operator, tableWasteDefect,tableWeight,visualInstructions
from iMES.View.adjuster import adjuster
from iMES.View.navbar_footer import navbar_footer