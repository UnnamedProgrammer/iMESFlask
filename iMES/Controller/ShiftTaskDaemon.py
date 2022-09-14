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
        self.insertedToDay = False

    def Start(self):
        thread = Thread(target=self.DoWork,args=())
        thread.start()
        print("Демон сменных заданий запущен")

    def DoWork(self):
        while True:
            sleep(10)
            self.insertedToDay = self.CheckShift()
            now = datetime.now()
            if ((now.hour == 18 and now.minute >= 55) or
               (now.hour == 6 and now.minute >= 55) or 
               (self.insertedToDay == False)):
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
                month = str(now.month)
                day = str(now.day)
                if now.month < 10:
                    month = '0' + month
                if now.day < 10:
                    day = '0' + day
                date = int(str(year + month + day))
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

    def CheckShift(self):
        now = datetime.now()
        hour = now.hour
        if ((hour >= 1 and hour < 7) or 
           (hour >= 19 and hour <= 24)):
            self.shift = 1
        elif hour >= 7 and hour < 19:
            self.shift = 0

        if self.shift == 0:
            shiftsql = """
                SELECT [Oid]
                    ,[StartDate]
                    ,[EndDate]
                    ,[Note]
                FROM [MES_Iplast].[dbo].[Shift] WHERE 
                    DATENAME(HOUR, [StartDate]) >= 7 AND 
                    DATENAME(YEAR, [StartDate]) = DATENAME(YEAR, GETDATE()) AND
                    DATENAME(MONTH, [StartDate]) = DATENAME(MONTH, GETDATE()) AND
                    DATENAME(DAY, [StartDate]) = DATENAME(DAY, GETDATE())
                        """
        # Если ночь то ищем ночную дату смены
        elif self.shift == 1:
            shiftsql = """
                SELECT [Oid]
                    ,[StartDate]
                    ,[EndDate]
                    ,[Note]
                FROM [MES_Iplast].[dbo].[Shift] WHERE 
                    DATENAME(HOUR, [StartDate]) >= 19 AND 
                    DATENAME(YEAR, [StartDate]) = DATENAME(YEAR, GETDATE()) AND
                    DATENAME(MONTH, [StartDate]) = DATENAME(MONTH, GETDATE()) AND
                    DATENAME(DAY, [StartDate]) = DATENAME(DAY, GETDATE())
                        """
        getshift = SQLManipulator.SQLExecute(shiftsql)
        if len(getshift) == 0:
            return False
        else:
            return True

