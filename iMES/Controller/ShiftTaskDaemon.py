from iMES.Model.DataBaseModels.EquipmentModel import Equipment
from iMES.Model.DataBaseModels.ProductionDataModel import ProductionData
from iMES.Model.DataBaseModels.RFIDEquipmentBindingModel import RFIDEquipmentBinding
from iMES.Model.ShiftTaskModels.ShiftTaskLoad import ShiftTaskLoader
from iMES.Model.DataBaseModels.NomenclatureGroupModel import NomenclatureGroup
from iMES.Model.DataBaseModels.ShiftModel import Shift
from iMES import db, app

from time import sleep
from datetime import datetime
from threading import Thread
from sqlalchemy import extract

class ShiftTaskDaemon():
    """
        Класс мониторинга сменяемости смен для получения сменных заданий на новую смену
    """
    def __init__(self, _app):
        # Инициализация начальных значений
        self.tpa_list = []
        self.insertedToDay = False
        self.app = _app
    # Метод запускающий основной метод в отдельном потоке выполнения
    def Start(self):
        thread = Thread(target=self.DoWork, args=())
        thread.start()
        self.app.logger.info("Мониторинг сменных заданий запущен")

    # Основной метод
    def DoWork(self):
        with app.app_context():
            # Запуск бесконечного цикла с определённой переодичностью
            while True:
                # Проверяем текущую смену, было ли получено сменное задание
                self.insertedToDay = self.CheckShift()
                now = datetime.now()
                if (self.insertedToDay == False):
                    # Если сменное задание небыло получено, то получаем
                    self.app.logger.info(f"[{datetime.now()}] <ShiftTaskDaemon->DoWork()> Нет сменного задания, получение нового сменного задания на {now}")
                    # Получаем список всех ТПА
                    tpa_list = (db.session.query(NomenclatureGroup.Code)
                                                .select_from(NomenclatureGroup, Equipment, RFIDEquipmentBinding)
                                                .where(RFIDEquipmentBinding.Equipment == Equipment.Oid)
                                                .where(Equipment.NomenclatureGroup == NomenclatureGroup.Oid)
                                                .where(RFIDEquipmentBinding.State == 1)
                                                .where(Equipment.EquipmentType == 'CC019258-D8D7-4286-B2CD-706FA0A2DC9D')
                                                .all())
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
                        prod_data = db.session.query(ProductionData).where(ProductionData.Status == 1).all()
                        for pd in prod_data:
                            pd.Status = 2
                        db.session.commit()
                        Loader = ShiftTaskLoader(self.tpa_list, date, self.get_shift(), self.app)
                        Loader.Get_ShiftTask()
                        Loader.InsertToDataBase()
                    self.app.logger.info("Новое сменное задание успешно получено")
                sleep(10)

    def get_shift(self):
        now = datetime.now()
        hour = now.hour
        shift = 0
        if ((hour >= 0 and hour < 7) or 
            (hour >= 19 and hour <= 23)):
            shift = 1
        elif hour >= 7 and hour < 19:
            shift = 0
        return shift

    # Метод проверки текущей смены
    def CheckShift(self):
        now = datetime.now()
        hour = now.hour
        shift = self.get_shift()

        # Если день то ищем дневную дату смены
        if shift == 0:
            shift_db = (db.session.query(Shift.Oid, Shift.Note)
             .filter(extract('year', Shift.StartDate) == datetime.now().year)
             .filter(extract('month', Shift.StartDate) == datetime.now().month)
             .filter(extract('day', Shift.StartDate) == datetime.now().day)
             .filter(extract('hour', Shift.StartDate) == 7).one_or_none())
        # Если ночь то ищем ночную дату смены
        elif shift == 1:
            if hour >= 0 and hour < 7:
                return True
            shift_db = (db.session.query(Shift.Oid, Shift.Note)
             .filter(extract('year', Shift.StartDate) == datetime.now().year)
             .filter(extract('month', Shift.StartDate) == datetime.now().month)
             .filter(extract('day', Shift.StartDate) == datetime.now().day)
             .filter(extract('hour', Shift.StartDate) == 19).one_or_none())
        # Если была найдена смена значит сменное задание уже было получено ранее
        if shift_db is None:
            return False
        else:
            return True
