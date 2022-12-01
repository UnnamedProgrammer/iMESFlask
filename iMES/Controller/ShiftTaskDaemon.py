from lib2to3.pytree import Base
from iMES.Model.ShiftTaskModels.ShiftTaskLoad import ShiftTaskLoader
from iMES.Model.BaseObjectModel import BaseObjectModel
from time import sleep
from datetime import datetime
from threading import Thread
from iMES import app

class ShiftTaskDaemon(BaseObjectModel):
    """
        Класс мониторинга сменяемости смен для получения сменных заданий на новую смену
    """
    def __init__(self):
        # Инициализация начальных значений
        self.tpa_list = []
        self.insertedToDay = False

    # Метод запускающий основной метод в отдельном потоке выполнения
    def Start(self):
        thread = Thread(target=self.DoWork, args=())
        thread.start()
        app.logger.info("Демон сменных заданий запущен")

    # Основной метод
    def DoWork(self):
        # Запуск бесконечного цикла с определённой переодичностью
        while True:
            # Проверяем текущую смену, было ли получено сменное задание
            self.insertedToDay = self.CheckShift()
            now = datetime.now()
            if (self.insertedToDay == False):
                # Если сменное задание небыло получено, то получаем
                app.logger.info(f"Нет сменного задания, получение нового сменного задания на {now}")
                # Получаем список всех ТПА
                get_tpa_list = """
                    SELECT NomenclatureGroup.Code
                    FROM Equipment, NomenclatureGroup, RFIDEquipmentBinding
                    WHERE RFIDEquipmentBinding.Equipment = Equipment.Oid and
                        Equipment.NomenclatureGroup = NomenclatureGroup.Oid and
                        RFIDEquipmentBinding.[State] = 1 and
                        Equipment.EquipmentType = 'CC019258-D8D7-4286-B2CD-706FA0A2DC9D'
                        """
                tpa_list = self.SQLExecute(get_tpa_list)
                for NomGroup in tpa_list:
                    self.tpa_list.append(NomGroup[0])
                # Определяем текущую дату
                year = str(now.year)
                month = str(now.month)
                day = str(now.day)
                if now.month < 10:
                    month = '0' + month
                if now.day < 10:
                    day = '0' + day
                date = int(str(year + month + day))
                # Если список ТПА небыл пуст то получаем сменные задания и
                # добавляем их в базу данных в таблицу ShiftTask
                if len(tpa_list) > 0:
                    self.SQLExecute("""
                        UPDATE [MES_Iplast].[dbo].[ProductionData]
                        SET Status = 2
                        WHERE Status = 1    
                    """)
                    Loader = ShiftTaskLoader(self.tpa_list, date, 3)
                    Loader.Get_ShiftTask()
                    Loader.InsertToDataBase()
                app.logger.info("Новое сменное задание успешно получено")
            sleep(10)

    # Метод проверки текущей смены
    def CheckShift(self):
        now = datetime.now()
        hour = now.hour
        shift = 0
        if ((hour >= 0 and hour < 7) or 
            (hour >= 19 and hour <= 23)):
            shift = 1
        elif hour >= 7 and hour < 19:
            shift = 0

        # Если день то ищем дневную дату смены
        if shift == 0:
            shiftsql = """
                SELECT [Oid]
                    ,[StartDate]
                    ,[EndDate]
                    ,[Note]
                FROM [MES_Iplast].[dbo].[Shift] WHERE 
                    DATENAME(HOUR, [StartDate]) = 7 AND 
                    DATENAME(YEAR, [StartDate]) = DATENAME(YEAR, GETDATE()) AND
                    DATENAME(MONTH, [StartDate]) = DATENAME(MONTH, GETDATE()) AND
                    DATENAME(DAY, [StartDate]) = DATENAME(DAY, GETDATE())
                        """
        # Если ночь то ищем ночную дату смены
        elif shift == 1:
            if hour >= 0 and hour < 7:
                return True
            shiftsql = """
                SELECT [Oid]
                    ,[StartDate]
                    ,[EndDate]
                    ,[Note]
                FROM [MES_Iplast].[dbo].[Shift] WHERE 
                    DATENAME(HOUR, [StartDate]) = 19 AND 
                    DATENAME(YEAR, [StartDate]) = DATENAME(YEAR, GETDATE()) AND
                    DATENAME(MONTH, [StartDate]) = DATENAME(MONTH, GETDATE()) AND
                    DATENAME(DAY, [StartDate]) = DATENAME(DAY, GETDATE())
                        """
        getshift = self.SQLExecute(shiftsql)
        # Если была найдена смена значит сменное задание уже было получено ранее
        if len(getshift) == 0:
            return False
        else:
            return True
