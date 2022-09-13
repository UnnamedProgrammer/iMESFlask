from ast import Load
from iMES.Model.ShiftTaskModels.ShiftTaskLoad import ShiftTaskLoader
from iMES.Model.SQLManipulator import SQLManipulator
from time import sleep
from datetime import datetime
from threading import Thread

class ShiftTaskDaemon():
    def __init__(self):
        self.tpa_list = []
        self.shift = 0
        
    def Start(self):
        thread = Thread(target=self.DoWork,args=())
        thread.start()
        print("Демон сменных заданий запущен")

    def DoWork(self):
        while True:
            sleep(10)
            now = datetime.now()
            if ((now.hour == 18 and now.minute >= 55) or
               (now.hour == 6 and now.minute >= 55)):
                get_tpa_list = """
            SELECT NomenclatureGroup.Code
            FROM Equipment, NomenclatureGroup, RFIDEquipmentBinding
            WHERE RFIDEquipmentBinding.Equipment = Equipment.Oid and
                Equipment.NomenclatureGroup = NomenclatureGroup.Oid and
                RFIDEquipmentBinding.[State] = 1 and
                Equipment.EquipmentType = 'CC019258-D8D7-4286-B2CD-706FA0A2DC9D'
                """
                tpa_list = SQLManipulator.SQLExecute(get_tpa_list)
                for NomGroup in tpa_list:
                    self.tpa_list.append(NomGroup[0])
                year = str(now.year)
                month = ''
                day = 0
                if now.month < 10:
                    month = '0'+str(now.month)
                if now.day < 10:
                    day = '0' + str(now.day)
                date = int(year + month + day)
                print(date)
                hour = now.hour
                if (hour >= 1 and hour < 7) or (hour >= 19 and hour <= 24):
                    self.shift = 1
                elif hour >= 7 and hour < 19:
                    self.shift = 0
                if len(tpa_list) > 0:
                    Loader = ShiftTaskLoader(self.tpa_list,date,self.shift)
                    Loader.Get_ShiftTask()
                    Loader.InsertToDataBase()

