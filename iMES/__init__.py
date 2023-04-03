import configparser
import imp
import logging
import os
from datetime import datetime

from flask_socketio import SocketIO
from flask import Flask
from flask_login import LoginManager
from flask_cors import CORS
from engineio.payload import Payload
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.engine import URL


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
    }
)

# Создание объектов 
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.config['SQLALCHEMY_DATABASE_URI']=connection_url
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
                                            "max_overflow": 15,
                                            "pool_pre_ping": True,
                                            "pool_recycle": 60 * 60,
                                            "pool_size": 30,
                                          }
app.config['SECRET_KEY'] = 'ded06adc-f231-4c99-8932-42b2e2592ba2'

socketio = SocketIO(app, async_mode='threading',ping_interval=120)
cors = CORS(app)
db = SQLAlchemy(app)

# Подключение менеджера авторизации
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.login_message_category = "info"
login_manager.init_app(app=app)
user_dict = {}

# Переменные текущего ТПА и всех ТПА
current_tpa = {}
TpaList = []

# Переменные для API
tpasresultapi = []
tpasapi = None

# Импорт роутингов
from iMES.View.operator import operator, visualInstructions, update_shift_task, norm_documentation
from iMES.View.navbar_footer import navbar_footer
from iMES.View.adjuster import adjuster
from iMES.View.menu import menu
from iMES.View.index import index
from iMES.View.menu.bind_press_form import bind_press_form
from iMES.View.UnloadTo1C import UnloadTo1C
from iMES.View.GetNormDocumentation import GetNormDocumentation
from iMES.View.api import mes_ns_api, mes_ns_wastes
