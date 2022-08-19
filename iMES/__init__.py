from flask_socketio import SocketIO
from flask import Flask
from flask_login import LoginManager
from iMES.Controller.UserCountController import UserCountController
from iMES.Model.SQLManipulator import SQLManipulator
from iMES.Model.UserModel import UserModel
import configparser


config = configparser.ConfigParser()
config.read("iMES/config.cfg")

host = config["Host-data"]["ip_address"]
port = int(config["Host-data"]["port"])
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.login_message_category = "info"
login_manager.init_app(app=app)
user = UserModel()
UserController = UserCountController()
sqldevices = """
                SELECT[DeviceId]
                FROM [MES_Iplast].[dbo].[Device]
            """

Devices = SQLManipulator.SQLExecute(sqldevices)
current_tpa = {}

TpaList = {}
for device in Devices:
    sqltpa = f"""
                SELECT [Equipment].[Oid],[Equipment].[Name]
                FROM [MES_Iplast].[dbo].[Relation_DeviceEquipment], Equipment, Device 
                WHERE 	Device.DeviceId = '{device[0]}' AND
                        Equipment.Oid = Relation_DeviceEquipment.Equipment AND
                        Device.Oid = Relation_DeviceEquipment.Device
            """
    tpas = SQLManipulator.SQLExecute(sqltpa)
    tpasresult = []
    for tpa in tpas:
        tpasresult.append({'Oid':tpa[0], 'Name':tpa[1]})
    TpaList[device[0]] = tpasresult
    
    current_tpa[device[0]] = [TpaList[device[0]][0]['Oid'],TpaList[device[0]][0]['Name']]
   
from iMES.View.index import index
from iMES.View.menu import menu
from iMES.View.operator import operator, tableWasteDefect,tableWeight,visualInstructions
from iMES.View.adjuster import adjuster
from iMES.View.navbar_footer import navbar_footer
from iMES.View.bind_press_form import bind_press_form