from datetime import datetime
from flask_socketio import SocketIO
from flask import Flask
from flask_login import LoginManager
from iMES.Controller.UserCountController import UserCountController
from iMES.Model.UserModel import UserModel
from iMES.Controller.TpaController import TpaController 
import configparser
import logging
import os
from engineio.payload import Payload

# Максимальное число обрабатываемых пакетов за раз
Payload.max_decode_packets = 50

# Настройки логов
if (not os.path.exists('log/')):
    os.mkdir('log/')
file_log = logging.FileHandler(
    "log/"+datetime.now().strftime("%Y_%m_%d_%H_%M_%S")+".log")
console_out = logging.StreamHandler()
logging.basicConfig(handlers=(file_log,), level=logging.NOTSET)

# Чтение конфига
config = configparser.ConfigParser()
config.read("iMES/config.cfg")
host = config["Host-data"]["ip_address"]
port = int(config["Host-data"]["port"])

# Создание объектов 
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
from iMES.Model.BaseObjectModel import BaseObjectModel
Initiator = BaseObjectModel(app)
socketio = SocketIO(app)

# Подключение менеджера авторизации
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.login_message_category = "info"
login_manager.init_app(app=app)
user = UserModel()
UserController = UserCountController()

# Переменные текущего ТПА и всех ТПА
current_tpa = {}
TpaList = {}

# Инициализация списка и словаря с ТПА
sqldevices = """
                SELECT[DeviceId]
                FROM [MES_Iplast].[dbo].[Device]
            """
Devices = Initiator.SQLExecute(sqldevices)
# Проход по всем ТПА, задание начальных значенией, и присвоение
# класса-контроллера для ТПА
for device in Devices:
    sqltpa = f"""
                SELECT [Equipment].[Oid],[Equipment].[Name]
                FROM [MES_Iplast].[dbo].[Relation_DeviceEquipment], Equipment, Device 
                WHERE 	Device.DeviceId = '{device[0]}' AND
                        Equipment.Oid = Relation_DeviceEquipment.Equipment AND
                        Device.Oid = Relation_DeviceEquipment.Device
              """
    tpas = Initiator.SQLExecute(sqltpa)

    tpasresult = []
    for tpa in tpas:
        controller = TpaController(app,tpa[0])
        tpasresult.append({'Oid': tpa[0], 'Name': tpa[1], 'WorkStatus':False,'Controller':controller})

    TpaList[device[0]] = tpasresult
    current_tpa[device[0]] = [TpaList[device[0]][0]['Oid'],
                                TpaList[device[0]][0]['Name'],
                                TpaList[device[0]][0]['Controller']]

# Импорт роутингов
from iMES.View.operator import operator, visualInstructions
from iMES.View.navbar_footer import navbar_footer
from iMES.View.adjuster import adjuster
from iMES.View.menu import menu
from iMES.View.index import index
from iMES.View.bind_press_form import bind_press_form