import configparser
import imp
import logging
import os
from time import sleep
from datetime import datetime
from threading import Thread

from flask_socketio import SocketIO
from flask import Flask
from flask_login import LoginManager
from flask_cors import CORS
from engineio.payload import Payload
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select
from sqlalchemy.engine import URL

# Контроллеры iMES
from iMES.Controller.ShiftTaskDaemon import ShiftTaskDaemon
from iMES.Controller.ProductionDataDaemon import ProductionDataDaemon
from iMES.Controller.UserCountController import UserCountController
from iMES.Model.UserModel import UserModel
from iMES.Controller.TpaController import TpaController


# Максимальное число обрабатываемых пакетов за раз
Payload.max_decode_packets = 1000


# Настройки логов
if (not os.path.exists('log/')):
    os.mkdir('log/')
file_log = logging.FileHandler(
    "log/"+datetime.now().strftime("%Y_%m_%d_%H_%M_%S")+".log",encoding='cp1251')
console_out = logging.StreamHandler()
logging.basicConfig(handlers=(file_log,), level=logging.ERROR)

try:
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
except:
    pass

# Чтение конфига
config = configparser.ConfigParser()
config.read("iMES/config.cfg")
host = config["Host-data"]["ip_address"]
port = int(config["Host-data"]["port"])

# Соединение с бд
connection_url = URL.create(
    "mssql+pyodbc",
    username="terminal",
    password="xAlTeS3dGrh7",
    host="192.168.107.43",
    port=1433,
    database="MES_Iplast",
    query={
        "driver": "ODBC Driver 18 for SQL Server",
        "TrustServerCertificate": "yes",
    },
)

# Создание объектов 
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['SQLALCHEMY_DATABASE_URI']=connection_url
app.config['SECRET_KEY'] = 'ded06adc-f231-4c99-8932-42b2e2592ba2'

from iMES.Model.BaseObjectModel import BaseObjectModel
Initiator = BaseObjectModel(app)
socketio = SocketIO(app, async_mode='threading',ping_interval=120)
cors = CORS(app)
db = SQLAlchemy(app)


# Модели БД
from iMES.Model.DataBaseModels.DeviceModel import Device
from iMES.Model.DataBaseModels.EquipmentModel import Equipment
from iMES.Model.DataBaseModels.RFIDEquipmentBindingModel import RFIDEquipmentBinding
from iMES.Model.DataBaseModels.Relation_DeviceEquipmentModel import Relation_DeviceEquipment

# Запуск демонов
ShiftTaskMonitoring = ShiftTaskDaemon(app)
ShiftTaskMonitoring.Start()
ProductDataMonitoring = ProductionDataDaemon(app)
ProductDataMonitoring.Start()

# Подключение менеджера авторизации
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.login_message_category = "info"
login_manager.init_app(app=app)
user = UserModel()
user_dict = {}
UserController = UserCountController()

# Переменные текущего ТПА и всех ТПА
current_tpa = {}
TpaList = {}

# Переменные для API
tpasresultapi = []
tpasapi = None

# Инициализация списка и словаря с ТПА
Devices = None
with app.app_context():
    Devices = Device.query.all()

# Проход по всем ТПА, задание начальных значений, и присвоение
# класса-контроллера для ТПА
for device in Devices:
    with app.app_context():
        tpas = Equipment.query.where(
            Relation_DeviceEquipment.Device == device.Oid).where(
                Equipment.Oid == Relation_DeviceEquipment.Equipment).all()
        tpasresult = []
        for tpa in tpas:
            controller = TpaController(app,tpa.Oid)
            tpasresult.append({'Oid': str(tpa.Oid).upper(), 'Name': tpa.Name, 'WorkStatus':False,'Controller':controller})

        TpaList[device.DeviceId] = tpasresult
        current_tpa[device.DeviceId] = [TpaList[device.DeviceId][0]['Oid'],
                                    TpaList[device.DeviceId][0]['Name'],
                                    TpaList[device.DeviceId][0]['Controller']]

# Создание списка ТПА для API mes-ns
with app.app_context():
    tpasapi = Equipment.query.where(
        Equipment.NomenclatureGroup is not None).where(
            Equipment.Area == 'A0DCF91A-6196-4BDE-8541-B76FBCB9F7AC').where(
                RFIDEquipmentBinding.Equipment == Equipment.Oid).where(
                    Equipment.EquipmentType == 'CC019258-D8D7-4286-B2CD-706FA0A2DC9D'
                ).all()

    for tpa in tpasapi:
        controller = TpaController(app,str(tpa.Oid).upper())
        tpasresultapi.append({'Oid': tpa.Oid, 'Name': tpa.Name, 'WorkStatus':False,'Controller':controller})

def UpdateTpa():
    while True:
        for ip in current_tpa.keys():
            current_tpa[ip][2].Check_Downtime(current_tpa[ip][0])
        sleep(30)

def reload_tpa(tpa):
    while True:
        threads = []
        for t in tpa:
            thr = Thread(target=thread_state, args=(t,))
            thr2 = Thread(target=t['Controller'].data_from_shifttask, args=())
            threads.append(thr)
            threads.append(thr2)
        for tr in threads:
            tr.start()
        for tr in threads:
            tr.join()
        threads.clear()
        sleep(30)

def thread_state(t):
    t['Controller'].state = t['Controller'].Check_Downtime(t['Oid'])

UpdateTpaThread = Thread(target=UpdateTpa, args=())
UpdateTpaThread.start()
reload_tpa_Thread = Thread(target=reload_tpa, args=(tpasresultapi,))
reload_tpa_Thread.start()

# Импорт роутингов
from iMES.View.operator import operator, visualInstructions, update_shift_task, norm_documentation
from iMES.View.navbar_footer import navbar_footer
from iMES.View.adjuster import adjuster
from iMES.View.menu import menu
from iMES.View.index import index
from iMES.View.menu.bind_press_form import bind_press_form
from iMES.View.UnloadTo1C import UnloadTo1C
from iMES.View.GetNormDocumentation import GetNormDocumentation
from iMES.View.api import mes_ns_api
