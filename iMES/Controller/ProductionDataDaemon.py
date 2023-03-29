from threading import Thread
from time import sleep
from sqlalchemy import func
from datetime import datetime

from iMES.Model.DataBaseModels.EquipmentModel import Equipment
from iMES.Model.DataBaseModels.NomenclatureGroupModel import NomenclatureGroup
from iMES.Model.DataBaseModels.ProductWeightModel import ProductWeight
from iMES.Model.DataBaseModels.RFIDClosureDataModel import RFIDClosureData
from iMES.Model.DataBaseModels.RFIDEquipmentBindingModel import RFIDEquipmentBinding
from iMES.Model.DataBaseModels.RFIDEquipmentModel import RFIDEquipment
from iMES.Model.DataBaseModels.ShiftModel import Shift
from iMES.Model.DataBaseModels.ShiftTaskModel import ShiftTask
from iMES.Model.DataBaseModels.ProductModel import Product
from iMES.Model.DataBaseModels.ProductionDataModel import ProductionData
from iMES.Model.DataBaseModels.EquipmentPerformanceModel import EquipmentPerformance
from iMES.Model.DataBaseModels.Relation_ProductPerformanceModel import Relation_ProductPerformance
from iMES.Model.DataBaseModels.DowntimeFailureModel import DowntimeFailure
from iMES import db



class ProductionDataDaemon():
    """
        Класс отвечающий за подсчёт продукции для ТПА по сменному заданию, а так же
        и за саму выдачу сменных заданий из базы данных для ТПА 
    """
    def __init__(self, _app):
        # Инициализация начальных значений спика ТПА, совершенных ТПА смыканий
        self.app = _app
        self.offsetlist = {}
        self.last_shift = None
        self.tpalist = self.GetAllTpa()

    # Метод запускающий основную функцию в отдельном потоке    
    def Start(self):
        thread = Thread(target=self.TpaProductionDataMonitoring, args=())
        thread.start()
        self.app.logger.info("Диспетчер сменных заданий запущен")

    # Основной метод класса
    def TpaProductionDataMonitoring(self):
        # Запуск бесконечного цикла с определенной переодичностью заданной методом sleep()
        while True:
            # Перебор всех ТПА
            self.GetCurrentShift()
            for tpanum in range(0,len(self.tpalist)):
                try:
                    # Проверяем наличие сменных заданий у ТПА
                    if len(self.tpalist[tpanum][3]['ShiftTask']) > 0:
                        # Перебор сменных заданий у ТПА
                        for shift_task in self.tpalist[tpanum][3]['ShiftTask']:
                            # Проверяем наличие записи в таблице ProductionData
                            # для выбранного сменного задания
                            if self.ProductionDataRecordIsCreated(shift_task[0]):
                                # Если есть запись то подсчитываем и обновляем значения
                                self.UpdateCountClosures(shift_task[0],
                                                        shift_task[16],
                                                        shift_task[5],
                                                        shift_task[11],
                                                        shift_task[10],
                                                        shift_task[2])
                            else:
                                # Иначе создаём новую запись и заполняем её подсчитанными значениями
                                self.CreateProductionDataRecord(shift_task)
                                self.UpdateCountClosures(shift_task[0],
                                                        shift_task[16],
                                                        shift_task[5],
                                                        shift_task[11],
                                                        shift_task[10],
                                                        shift_task[2])
                    else:
                        # Если у ТПА нет сменных заданий то выдаём новое
                        shift_task_list = self.GetShiftTaskByEquipmentPerformance(self.tpalist[tpanum][0])
                        self.tpalist[tpanum][3]["ShiftTask"] = shift_task_list
                except IndexError:
                    continue
                except Exception as error:
                    # Вывод в лог возникших ошибок
                    self.app.logger.info(f"[{datetime.now()}] {error} in {str(self.tpalist[tpanum])}")
                    continue
            sleep(30)
    
    def OnceMonitoring(self):
        for tpanum in range(0,len(self.tpalist)):
            try:
                # Проверяем наличие сменных заданий у ТПА
                if len(self.tpalist[tpanum][3]['ShiftTask']) > 0:
                    # Перебор сменных заданий у ТПА
                    for shift_task in self.tpalist[tpanum][3]['ShiftTask']:
                        # Проверяем наличие записи в таблице ProductionData
                        # для выбранного сменного задания
                        if self.ProductionDataRecordIsCreated(shift_task[0]):
                            # Если есть запись то подсчитываем и обновляем значения
                            self.UpdateCountClosures(shift_task[0],
                                                    shift_task[16],
                                                    shift_task[5],
                                                    shift_task[11],
                                                    shift_task[10],
                                                    shift_task[2])
                        else:
                            # Иначе создаём новую запись и заполняем её подсчитанными значениями
                            self.CreateProductionDataRecord(shift_task)
                            self.UpdateCountClosures(shift_task[0],
                                                    shift_task[16],
                                                    shift_task[5],
                                                    shift_task[11],
                                                    shift_task[10],
                                                    shift_task[2])
                else:
                    # Если у ТПА нет сменных заданий то выдаём новое
                    shift_task_list = self.GetShiftTaskByEquipmentPerformance(self.tpalist[tpanum][0])
                    self.tpalist[tpanum][3]["ShiftTask"] = shift_task_list
            except IndexError:
                continue
            except Exception as error:
                # Вывод в лог возникших ошибок
                self.app.logger.info(f"[{datetime.now()}] {error} in {str(self.tpalist[tpanum])}")
                continue

    # Метод получающий весь список ТПА, и задающий им новую опцию "Сменное задание"
    def GetAllTpa(self):
        with self.app.app_context():
            TpaList = []
            result_sql = (db.session.query(Equipment.Oid,
                                            Equipment.Name,
                                            Equipment.NomenclatureGroup)
                                            .select_from(Equipment, NomenclatureGroup, RFIDEquipmentBinding)
                                            .where(RFIDEquipmentBinding.Equipment == Equipment.Oid)
                                            .where(Equipment.NomenclatureGroup == NomenclatureGroup.Oid)
                                            .where(RFIDEquipmentBinding.State == 1)
                                            .where(Equipment.EquipmentType == 'CC019258-D8D7-4286-B2CD-706FA0A2DC9D')
                                            .all())
            for tpa in result_sql:
                tpa_obj = list(tpa)
                tpa_obj.append({'ShiftTask':[]})
                TpaList.append(tpa_obj)
            return TpaList
    
    # Метод выдающий сменные задания для ТПА по справочнику производительности
    def GetShiftTaskByEquipmentPerformance(self,tpaoid):
        # Смотрим какая пресс-форма стоит на ТПА
        shift_tasks = []
        pressform = self.GetTpaPressFrom(tpaoid)
        # Получаем справочник производительности по связке ТПА + ПФ
        equipment_performance = self.GetEquipmentPerformance(tpaoid,pressform)
        shift = self.GetCurrentShift()
        if equipment_performance != None:
            # Задаём кол-во продукции за смыкание из производительности
            total_socket_count = equipment_performance[4]
            if total_socket_count == 0:
                total_socket_count = 1
            # Получаем список продуктов возможных для производства по СП
            products = self.GetProductionProducts(equipment_performance)
            # Перебираем продукты, смотрим сокетность в сменном задании, и заполняем
            # сокеты продукцией чтобы в сумме их количество совпало с количеством
            # выпускаемой продукции за одно смыкание
            empty_sockets = total_socket_count
            for product in products:
                shift_task = self.GetShiftTask(shift,tpaoid,product[1],product[3])
                if len(shift_task) > 0:
                    if total_socket_count == product[2]:
                        if product[2] > empty_sockets:
                            continue
                        shift_tasks.append(shift_task)
                        break
                    else:
                        if empty_sockets != 0:
                            empty_sockets -= product[2]
                            shift_tasks.append(shift_task)
                        else:
                            break
        else:
            return self.GetShiftTaskWithoutEP(shift, tpaoid)
        if len(shift_tasks) == 0:
            shift_tasks = self.GetShiftTaskWithoutEP(shift,tpaoid)          
        return shift_tasks
    
    # Метод возвращает Oid текущей смены
    def GetCurrentShift(self):
        with self.app.app_context():
            shift_oid = db.session.query(Shift.Oid).order_by(Shift.StartDate.desc()).first()
            if len(shift_oid) > 0:
                if self.last_shift != shift_oid[0]:
                    self.last_shift = shift_oid[0]
                    for key in self.offsetlist.keys():
                        self.offsetlist[key] = 0
                    return shift_oid[0]
                else:
                    return shift_oid[0]
            else:
                return None

    # Метод вытягивает сменное задание без справочника производительности
    def GetShiftTaskWithoutEP(self, shift, equipment):
        with self.app.app_context():
            shift_task_l = []
            if shift == None:
                return []
            shift_task = (db.session.query(ShiftTask.Oid,
                                           Shift.Note,
                                           ShiftTask.Equipment,
                                           ShiftTask.Ordinal,
                                           Product.Name,
                                           ShiftTask.Specification,
                                           ShiftTask.Traits,
                                           ShiftTask.ExtraTraits,
                                           ShiftTask.PackingScheme,
                                           ShiftTask.PackingCount,
                                           ShiftTask.SocketCount,
                                           ShiftTask.ProductCount,
                                           ShiftTask.Cycle,
                                           ShiftTask.Weight,
                                           ShiftTask.ProductURL,
                                           ShiftTask.PackingURL,
                                           ShiftTask.Shift)
                                          .select_from(ShiftTask)
                                          .where(ShiftTask.Equipment == equipment)
                                          .join(Product).filter(Product.Oid == ShiftTask.Product)
                                          .join(Shift).filter(Shift.Oid == shift)
                                          .all())
            offset = 0
            if len(shift_task) > 0:
                for st in shift_task:
                    find_shifttask_ended = (db.session.query(ProductionData.Oid,
                                                            ProductionData.CountFact)
                                                            .where(ProductionData.ShiftTask == st[0])
                                                            .where(ProductionData.Status == 2)
                                                            .all())
                    if len(find_shifttask_ended) > 0:
                        shift_task.remove(st)
                        offset += find_shifttask_ended[0][1]
            self.offsetlist[equipment] = offset
            if len(shift_task) > 0:
                shift_task_l = [shift_task[0]]
            return shift_task_l

    # Метод ищет совпадающее по заданным параметрам сменное задание
    def GetShiftTask(self, shift, equipment, product, cycle):
        with self.app.app_context():
            if shift == None:
                return []
            offset = 0
            shift_task = (db.session.query(ShiftTask.Oid,
                                            Shift.Note,
                                            ShiftTask.Equipment,
                                            ShiftTask.Ordinal,
                                            Product.Name,
                                            ShiftTask.Specification,
                                            ShiftTask.Traits,
                                            ShiftTask.ExtraTraits,
                                            ShiftTask.PackingScheme,
                                            ShiftTask.PackingCount,
                                            ShiftTask.SocketCount,
                                            ShiftTask.ProductCount,
                                            ShiftTask.Cycle,
                                            ShiftTask.Weight,
                                            ShiftTask.ProductURL,
                                            ShiftTask.PackingURL,
                                            ShiftTask.Shift)
                                            .select_from(ShiftTask)
                                            .where(ShiftTask.Equipment == equipment)
                                            .where(ShiftTask.Cycle == cycle)
                                            .where(ShiftTask.Shift == shift)
                                            .join(Shift).filter(Shift.Oid == shift)
                                            .join(Product).filter(Product.Oid == product)
                                            .all())
            if len(shift_task) > 0:
                for st in shift_task:
                    find_shifttask_ended = (db.session.query(ProductionData.Oid,
                                                            ProductionData.CountFact)
                                                            .where(ProductionData.ShiftTask == st[0])
                                                            .where(ProductionData.Status == 2)
                                                            .all())
                    if len(find_shifttask_ended) > 0:
                        shift_task.remove(st)
                        offset += find_shifttask_ended[0][1]
            self.offsetlist[equipment] = offset
            if len(shift_task) == 0:
                return []
            return shift_task[0]

    # Метод получает справочник производительности по связке ТПА + ПФ    
    def GetEquipmentPerformance(self,tpaoid,rigoid):
        with self.app.app_context():
            if rigoid != None:
                EP = (db.session.query(EquipmentPerformance.Oid,
                                      EquipmentPerformance.NomenclatureGroup,
                                      EquipmentPerformance.MainEquipment,
                                      EquipmentPerformance.RigEquipment,
                                      EquipmentPerformance.TotalSocketCount)
                                      .select_from(EquipmentPerformance)
                                      .where(EquipmentPerformance.MainEquipment == tpaoid)
                                      .where(EquipmentPerformance.RigEquipment == rigoid)
                                      .one_or_none())
                if bool(EP):
                    return EP
                else:
                    return None

    # Метод получает возможные для производства продукты по справочнику
    # производительности 
    def GetProductionProducts(self,equipment_performance_oid):
        with self.app.app_context():
            list = (db.session.query(Relation_ProductPerformance.EquipmentPerformance,
                                    Relation_ProductPerformance.Product,
                                    Relation_ProductPerformance.SocketCount,
                                    Relation_ProductPerformance.Cycle)
                                    .select_from(Relation_ProductPerformance)
                                    .where(Relation_ProductPerformance.EquipmentPerformance == equipment_performance_oid[0])
                                    .all())
            products = []
            for product in list:
                products.append(product)
            return products

    # Метод проверяет создана ли запись для сменного задания в таблице ProductionData
    def ProductionDataRecordIsCreated(self,ShiftTaskOid):
        with self.app.app_context():
            result = (db.session.query(ProductionData.Oid,
                                       ProductionData.ShiftTask,
                                       ProductionData.RigEquipment,
                                       ProductionData.Status,
                                       ProductionData.StartDate,
                                       ProductionData.EndDate,
                                       ProductionData.CountFact,
                                       ProductionData.CycleFact,
                                       ProductionData.WeightFact,
                                       ProductionData.SpecificationFact)
                                       .select_from(ProductionData)
                                       .where(ProductionData.ShiftTask == ShiftTaskOid)
                                       .all())
            if len(result) > 0:
                return True
            else:
                return False

    # Метод создаёт запись в базе данных в таблице ProductionData
    # по заданному Oid сменного задания
    def CreateProductionDataRecord(self, shifttaskdata):
        with self.app.app_context():
            if shifttaskdata != '':
                pressform = self.GetTpaPressFrom(shifttaskdata[2])
                if pressform != '':
                    new_pd = ProductionData()
                    new_pd.ShiftTask = shifttaskdata[0]
                    new_pd.RigEquipment = pressform
                    new_pd.Status = 0
                    new_pd.StartDate = None
                    new_pd.EndDate = None
                    new_pd.CountFact = 0
                    new_pd.CycleFact = 0
                    new_pd.WeightFact = 0
                    new_pd.SpecificationFact = shifttaskdata[5]
                    db.session.add(new_pd)
                    db.session.commit()
                elif pressform == '':
                    new_pd = ProductionData()
                    new_pd.ShiftTask = shifttaskdata[0]
                    new_pd.RigEquipment = None
                    new_pd.Status = 0
                    new_pd.StartDate = None
                    new_pd.EndDate = None
                    new_pd.CountFact = 0
                    new_pd.CycleFact = 0
                    new_pd.WeightFact = 0
                    new_pd.SpecificationFact = shifttaskdata[5]
                    db.session.add(new_pd)
                    db.session.commit()

    # Метод определяет прессформу на ТПА
    def GetTpaPressFrom(self,tpaoid):
        with self.app.app_context():
            pressform = None
            try:
                pressform = (db.session.query(RFIDEquipmentBinding.Equipment)
                                            .select_from(RFIDEquipmentBinding, RFIDClosureData)
                                            .where(RFIDClosureData.Controller == \
                                                    db.session.query(RFIDEquipmentBinding.RFIDEquipment)
                                                        .where(RFIDEquipmentBinding.Equipment == tpaoid).one_or_none()[0])
                                            .where(RFIDEquipmentBinding.RFIDEquipment == RFIDClosureData.Label)
                                            .order_by(RFIDClosureData.Date.desc())
                                            .first()[0])
            except:
                pass
            if pressform is not None:
                return pressform
            else:
                return None

    # Метод обновляет данные в таблице ProductionData для сменного задания
    def UpdateCountClosures(self, ShiftTaskOid,ShiftOid, specification, plan, socketcount, tpaoid):
        with self.app.app_context():
            # Если случано передали пустое сменное задание возвращаем пустое значние
            if ShiftTaskOid == '':
                return
            # Проверяем не закрыто ли сменное задание в таблице ProductionData
            # Если статус ProductionData == 2 тогда обнуляем сменное задание у ТПА
            production_data = (db.session.query(ProductionData.Oid,
                                               ProductionData.ShiftTask,
                                               ProductionData.RigEquipment,
                                               ProductionData.Status,
                                               ProductionData.StartDate,
                                               ProductionData.EndDate,
                                               ProductionData.CountFact,
                                               ProductionData.CycleFact,
                                               ProductionData.WeightFact,
                                               ProductionData.SpecificationFact)
                                               .select_from(ProductionData)
                                               .where(ProductionData.ShiftTask == ShiftTaskOid)
                                               .all())
            if len(production_data) > 0:
                production_data = production_data[0]
                if production_data[3] == 2:
                    for i in range(0, len(self.tpalist)):
                        if self.tpalist[i][0] == tpaoid:
                            for task in self.tpalist[i][3]['ShiftTask']:
                                if task[0] == ShiftTaskOid:
                                    self.tpalist[i][3]['ShiftTask'].remove(task)
                            return
            else: return

            # Получаем количество смыканий сделанных во время исполнения сменного задания
            # с учётом исключения смыканий прошлых сменных заданий за смену переменной offset
            offset = self.offsetlist[tpaoid]
            result = (db.session.query(RFIDClosureData.Oid,
                                       RFIDClosureData.Controller,
                                       RFIDClosureData.Label,
                                       RFIDClosureData.Date,
                                       RFIDClosureData.Cycle,
                                       RFIDClosureData.Status,
                                       Shift.Note)
                                       .select_from(RFIDClosureData, ShiftTask, Shift)
                                       .where(RFIDClosureData.Controller == \
                                            db.session.query(RFIDEquipmentBinding.RFIDEquipment)
                                                .select_from(RFIDEquipmentBinding)
                                                .where(ShiftTask.Equipment == RFIDEquipmentBinding.Equipment)
                                                .where(ShiftTask.Oid == ShiftTaskOid)
                                                .one_or_none()[0])
                                       .where(ShiftTask.Oid == ShiftTaskOid)
                                       .where(Shift.Oid == ShiftTask.Shift)
                                       .where(RFIDClosureData.Date >= Shift.StartDate)
                                       .where(RFIDClosureData.Date <= Shift.EndDate)
                                       .where(RFIDClosureData.Status == 1)
                                       .order_by(RFIDClosureData.Date.asc())
                                       .offset(offset)
                                       .all())
            # Если есть смыкания то определяем дату начала и дату окончания для записи
            if len(result) > 0:
                # Определяем количество и дату начала а так же дату окончания, дата окончания
                # по умолчанию является дата последнего смыкания
                count = (len(result)) * socketcount
                startdate = result[0][3].strftime('%Y-%m-%dT%H:%M:%S')
                try:
                    enddate = result[(offset+plan)-1][3].strftime('%Y-%m-%dT%H:%M:%S')
                except:
                    try:
                        enddate = result[plan-1][3].strftime('%Y-%m-%dT%H:%M:%S')
                    except:
                        enddate =result[len(result)-1][3].strftime('%Y-%m-%dT%H:%M:%S')
                # Высчитываем средний цикл
                cycle_request = result
                average_cycle = 0
                if len(cycle_request) > 0:
                    for num in range(0,len(cycle_request)):
                        try:
                            average_cycle += cycle_request[num][4] + cycle_request[num+1][4]
                        except:
                            if average_cycle != 0:
                                average_cycle = average_cycle / num
                
                # Прибавляем к факту выпуска годные из простоев
                if tpaoid != '' and ShiftOid != '':
                    get_idle_val_clausers = (db.session.query(DowntimeFailure.Oid,
                                                              DowntimeFailure.StartDate,
                                                              DowntimeFailure.EndDate,
                                                              DowntimeFailure.ValidClosures)
                                                              .select_from(DowntimeFailure, Shift)
                                                              .where(DowntimeFailure.Equipment == tpaoid)
                                                              .where(DowntimeFailure.EndDate is not None)
                                                              .where(DowntimeFailure.ValidClosures != 0)
                                                              .where(Shift.Oid == ShiftOid)
                                                              .where(DowntimeFailure.StartDate >= Shift.StartDate)
                                                              .all())
                    if len(get_idle_val_clausers):
                        for val_clausers in get_idle_val_clausers:
                            count += int(val_clausers[3])
                # Проверяем статусы записи
                # Если статус 1 то обновляем значения
                if (production_data[3] == 1):
                    current_shift = db.session.query(Shift.Oid).order_by(Shift.StartDate.desc()).first()[0]
                    average_weight = (db.session.query(func.sum(ProductWeight.Weight), func.count(ProductWeight.Weight))
                                                      .where(ProductWeight.ProductionData == production_data[0])
                                                      .all())
                    if len(average_weight) > 0:
                        if average_weight[0][0] != None:
                            average_weight = average_weight[0][0]
                        else:
                            average_weight = 0
                    # Если количество произведенного продукта больше плана
                    # То присваиваем записи статус 2 тем самым закрывая сменное задание,
                    # и обнуляем его у ТПА чтобы ТПА смог получить новое
                    if count >= plan:
                        pd = db.session.query(ProductionData).where(ProductionData.Oid == production_data[0]).one_or_none()
                        if pd is not None:
                            pd.CountFact = plan
                            pd.CycleFact = average_cycle
                            pd.SpecificationFact = specification
                            pd.Status = 2
                            pd.WeightFact = average_weight
                        for i in range(0, len(self.tpalist)):
                            if self.tpalist[i][0] == tpaoid:
                                self.tpalist[i][3]['ShiftTask'] = []
                                break
                    else:
                        # Если срок сменного задания ограниченного сменой закончился
                        # То присваиваем записи статус 2 для её закрытия и обнуляем
                        # сменное задание у ТПА для получения нового
                        if current_shift != ShiftOid:
                            pd = db.session.query(ProductionData).where(ProductionData.Oid == production_data[0]).one_or_none()
                            if pd is not None:
                                pd.CountFact = plan
                                pd.CycleFact = average_cycle
                                pd.SpecificationFact = specification
                                pd.Status = 2
                                pd.WeightFact = average_weight
                            for i in range(0, len(self.tpalist)):
                                if self.tpalist[i][0] == tpaoid:
                                    self.tpalist[i][3]['ShiftTask'] = []
                                    break
                        else:
                            # Иначе просто обновляем запись с новыми значениями
                            pd = db.session.query(ProductionData).where(ProductionData.Oid == production_data[0]).one_or_none()
                            if pd is not None:
                                pd.CountFact = count
                                pd.CycleFact = average_cycle
                                pd.SpecificationFact = specification
                                pd.EndDate = enddate
                                pd.WeightFact = average_weight
                    db.session.commit()                            
                # Если запись была только создана и она не закрыта задаём начальные значения
                # далее при следующей итерации цикла она заполнится подсчитываемыми значениями
                if ((production_data[3] == 0) and
                (production_data[4] == None) and
                (production_data[5] == None) and
                (production_data[6] != 2)):
                    pd = db.session.query(ProductionData).where(ProductionData.Oid == production_data[0]).one_or_none()
                    if pd is not None:
                        pd.StartDate = startdate
                        pd.EndDate = enddate
                        pd.Status = 1
                        pd.SpecificationFact = specification
                        db.session.commit()