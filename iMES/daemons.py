from iMES.Controller.ShiftTaskDaemon import ShiftTaskDaemon
from iMES.Controller.ProductionDataDaemon import ProductionDataDaemon
from iMES.Controller.TpaController import TpaController
from iMES.Model.DataBaseModels.DeviceModel import Device
from iMES.Model.DataBaseModels.EquipmentModel import Equipment
from iMES.Model.DataBaseModels.Relation_DeviceEquipmentModel import Relation_DeviceEquipment
from iMES.Model.DataBaseModels.RFIDEquipmentBindingModel import RFIDEquipmentBinding
from iMES import app, db, TpaList, tpasresultapi

from time import sleep
from threading import Thread



# Создание объектов демонов
ShiftTaskMonitoring = ShiftTaskDaemon(app)
ProductDataMonitoring = ProductionDataDaemon(app)

# Создание списка ТПА для API mes-ns
Devices = None

with app.app_context():
    Devices = Device.query.all()

# Проход по всем ТПА, задание начальных значений, и присвоение
# класса-контроллера для ТПА
with app.app_context():
    with app.app_context():
        tpas = (db.session.query(Equipment)
                                    .select_from(Equipment, RFIDEquipmentBinding)
                                    .where(Equipment.NomenclatureGroup != None)
                                    .where(Equipment.Area == 'A0DCF91A-6196-4BDE-8541-B76FBCB9F7AC')
                                    .where(Equipment.EquipmentType == 'CC019258-D8D7-4286-B2CD-706FA0A2DC9D')
                                    .where(RFIDEquipmentBinding.Equipment == Equipment.Oid)
                                    .all())
        tpasresult = []
        for tpa in tpas:
            controller = TpaController(app,tpa.Oid, db)
            TpaList.append([str(tpa.Oid), tpa.Name, controller, False])

        for tpa in tpas:
            controller = TpaController(app,str(tpa.Oid).upper(), db)
            tpasresultapi.append([str(tpa.Oid), tpa.Name, controller, False])

def UpdateTpa():
    while True:
        for tpa in TpaList:
            tpa[2].Check_Downtime(tpa[0])
            tpa[2].update_pressform()
            tpa[2].data_from_shifttask()
        sleep(30)

def UpdateTpaMESNS():
    while True:
        for tpa in tpasresultapi:
            tpa[2].Check_Downtime(tpa[0])
            tpa[2].update_pressform()
            tpa[2].data_from_shifttask()
        sleep(30) 

UpdateTpaThread = Thread(target=UpdateTpa, args=())
UpdateMESNSThread = Thread(target=UpdateTpaMESNS, args=())