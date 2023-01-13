from threading import Thread
from time import sleep
from iMES.Model.BaseObjectModel import BaseObjectModel



class ProductionDataDaemon(BaseObjectModel):
    """
        Класс отвечающий за подсчёт продукции для ТПА по сменному заданию, а так же
        и за саму выдачу сменных заданий из базы данных для ТПА 
    """
    def __init__(self, _app):
        # Инициализация начальных значений спика ТПА, совершенных ТПА смыканий
        self.tpalist = self.GetAllTpa()
        self.offsetlist = {}
        self.last_shift = None
        self.app = _app
    # Метод запускающий основную функцию в отдельном потоке    
    def Start(self):
        thread = Thread(target=self.TpaProductionDataMonitoring, args=())
        thread.start()
        self.app.logger.info("Демон мониторинга продукции запущен")

    # Основной метод класса
    def TpaProductionDataMonitoring(self):
        # Запуск бесконечного цикла с определенной переодичностью заданной методом sleep()
        while True:
            # Перебор всех ТПА
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
                    self.app.logger.info(f"{error} in {str(self.tpalist[tpanum])}")
                    continue
            sleep(8)
    
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
                    self.app.logger.info(f"{error} in {str(self.tpalist[tpanum])}")
                    continue

    # Метод получающий весь список ТПА, и задающий им новую опцию "Сменное задание"
    def GetAllTpa(self):
        TpaList = []
        sql = """
            SELECT Equipment.Oid, Equipment.Name,Equipment.NomenclatureGroup
            FROM Equipment, NomenclatureGroup, RFIDEquipmentBinding
            WHERE RFIDEquipmentBinding.Equipment = Equipment.Oid and
                Equipment.NomenclatureGroup = NomenclatureGroup.Oid and
                RFIDEquipmentBinding.[State] = 1 and
                Equipment.EquipmentType = 'CC019258-D8D7-4286-B2CD-706FA0A2DC9D'
        """
        result_sql = self.SQLExecute(sql)
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
            products = self.GetProductionProducts(equipment_performance[0])
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
                        shift_tasks.append(shift_task[0])
                        break
                    else:
                        if empty_sockets != 0:
                            empty_sockets -= product[2]
                            shift_tasks.append(shift_task[0])
                        else:
                            break
        else:
            return self.GetShiftTaskWithoutEP(shift, tpaoid)
        if len(shift_tasks) == 0:
            shift_tasks = self.GetShiftTaskWithoutEP(shift,tpaoid)          
        return shift_tasks
    
    # Метод возвращает Oid текущей смены
    def GetCurrentShift(self):
        sql = """
            SELECT TOP(1) [Oid]
            FROM [MES_Iplast].[dbo].[Shift] ORDER BY StartDate DESC
        """
        shift_oid = self.SQLExecute(sql)
        if len(shift_oid) > 0:
            if self.last_shift != shift_oid[0][0]:
                self.last_shift = shift_oid[0][0]
                for key in self.offsetlist.keys():
                    self.offsetlist[key] = 0
                return shift_oid[0][0]
            else:
                return shift_oid[0][0]
        else:
            return None

    # Метод вытягивает сменное задание без справочника производительности
    def GetShiftTaskWithoutEP(self, shift, equipment):
        if shift == None:
            return []
        sql_ST = f"""
            SELECT [ShiftTask].[Oid]
                ,[Shift].Note
                ,[Equipment]
                ,[Ordinal]
                ,[Product].Name
                ,[Specification]
                ,[Traits]
                ,[ExtraTraits]
                ,[PackingScheme]
                ,[PackingCount]
                ,[SocketCount]
                ,[ProductCount]
                ,[Cycle]
                ,[Weight]
                ,[ProductURL]
                ,[PackingURL]
                ,[Shift]
            FROM [MES_Iplast].[dbo].[ShiftTask], Product, Shift 
            WHERE 
                Shift = '{shift}' AND
                Equipment = '{equipment}' AND
                ShiftTask.Product = Product.Oid AND
                Shift.Oid = (SELECT TOP(1) Oid FROM Shift ORDER BY StartDate DESC ) AND
                ShiftTask.Shift = Shift.Oid
        """
        offset = 0
        shift_task = self.SQLExecute(sql_ST)
        if len(shift_task) > 0:
            for st in shift_task:
                sql = f"""
                    SELECT [Oid] ,[CountFact]
                    FROM [MES_Iplast].[dbo].[ProductionData] 
                    WHERE ShiftTask = '{st[0]}' AND Status = 2
                """
                find_shifttask_ended = self.SQLExecute(sql)
                if len(find_shifttask_ended) > 0:
                    shift_task.remove(st)
                    offset += find_shifttask_ended[0][1]
        self.offsetlist[equipment] = offset
        shift_task_l = [shift_task[0]]
        return shift_task_l

    # Метод ищет совпадающее по заданным параметрам сменное задание
    def GetShiftTask(self, shift, equipment, product, cycle):
        if shift == None:
            return []
        sql_ST = f"""
            SELECT [ShiftTask].[Oid]
                ,[Shift].Note
                ,[Equipment]
                ,[Ordinal]
                ,[Product].Name
                ,[Specification]
                ,[Traits]
                ,[ExtraTraits]
                ,[PackingScheme]
                ,[PackingCount]
                ,[SocketCount]
                ,[ProductCount]
                ,[Cycle]
                ,[Weight]
                ,[ProductURL]
                ,[PackingURL]
                ,[Shift]
            FROM [MES_Iplast].[dbo].[ShiftTask], Product, Shift 
            WHERE 
                Shift = '{shift}' AND
                Equipment = '{equipment}' AND
                Product = '{product}' AND
                Cycle = '{cycle}' AND
                ShiftTask.Product = Product.Oid AND
                Shift.Oid = (SELECT TOP(1) Oid FROM Shift ORDER BY StartDate DESC ) AND
                ShiftTask.Shift = Shift.Oid
        """
        offset = 0
        shift_task = self.SQLExecute(sql_ST)
        if len(shift_task) > 0:
            for st in shift_task:
                sql = f"""
                    SELECT [Oid] ,[CountFact]
                    FROM [MES_Iplast].[dbo].[ProductionData] 
                    WHERE ShiftTask = '{st[0]}' AND Status = 2
                """
                find_shifttask_ended = self.SQLExecute(sql)
                if len(find_shifttask_ended) > 0:
                    shift_task.remove(st)
                    offset += find_shifttask_ended[0][1]
        self.offsetlist[equipment] = offset
        return shift_task

    # Метод получает справочник производительности по связке ТПА + ПФ    
    def GetEquipmentPerformance(self,tpaoid,rigoid):
        if rigoid != None:
            sql = f"""
                SELECT [Oid]
                    ,[NomenclatureGroup]
                    ,[MainEquipment]
                    ,[RigEquipment]
                    ,[TotalSocketCount]
                FROM [MES_Iplast].[dbo].[EquipmentPerformance]
                WHERE MainEquipment = '{tpaoid}' AND
                    RigEquipment = '{rigoid}'
            """
            EP = self.SQLExecute(sql)
            if bool(EP):
                return EP[0]
            else:
                return None

    # Метод получает возможные для производства продукты по справочнику
    # производительности 
    def GetProductionProducts(self,equipment_performance_oid):
        sql = f"""
            SELECT [EquipmentPerformance]
                ,[Product]
                ,[SocketCount]
                ,[Cycle]
            FROM [MES_Iplast].[dbo].[Relation_ProductPerformance]
            WHERE EquipmentPerformance = '{equipment_performance_oid}'
        """
        list = self.SQLExecute(sql)
        products = []
        for product in list:
            products.append(product)
        return products

    # Метод проверяет создана ли запись для сменного задания в таблице ProductionData
    def ProductionDataRecordIsCreated(self,ShiftTaskOid):
        sql = f"""
            SELECT TOP (1000) [Oid]
                ,[ShiftTask]
                ,[RigEquipment]
                ,[Status]
                ,[StartDate]
                ,[EndDate]
                ,[CountFact]
                ,[CycleFact]
                ,[WeightFact]
                ,[SpecificationFact]
            FROM [MES_Iplast].[dbo].[ProductionData] WHERE ShiftTask = '{ShiftTaskOid}'
        """
        result = self.SQLExecute(sql)
        if len(result) > 0:
            return True
        else:
            return False

    # Метод создаёт запись в базе данных в таблице ProductionData
    # по заданному Oid сменного задания
    def CreateProductionDataRecord(self, shifttaskdata):
        sql = ''
        if shifttaskdata != '':
            pressform = self.GetTpaPressFrom(shifttaskdata[2])
            if pressform != '':
                sql = f"""
                INSERT INTO ProductionData (Oid, ShiftTask, RigEquipment,Status, StartDate, EndDate, CountFact, CycleFact,WeightFact,SpecificationFact)
                VALUES (NEWID(),'{shifttaskdata[0]}','{pressform}', 0, NULL,NULL,NULL,NULL,NULL,'{shifttaskdata[5]}')
                """
                self.SQLExecute(sql)
            elif pressform == '':
                sql = f"""
                INSERT INTO ProductionData (Oid, ShiftTask, RigEquipment,Status, StartDate, EndDate, CountFact, CycleFact,WeightFact,SpecificationFact)
                VALUES (NEWID(),'{shifttaskdata[0]}',NULL, 0, NULL,NULL,NULL,NULL,NULL,'{shifttaskdata[5]}')
                """
                self.SQLExecute(sql)

    # Метод определяет прессформу на ТПА
    def GetTpaPressFrom(self,tpaoid):
        sql = f"""
            SELECT TOP (1) RFIDEquipmentBinding.Equipment, RFIDClosureData.Date
            FROM [MES_Iplast].[dbo].[RFIDClosureData], RFIDEquipmentBinding, Equipment 
            WHERE 
            Controller = (SELECT RFIDEquipment 
                            FROM RFIDEquipmentBinding 
                            WHERE Equipment = '{tpaoid}') AND
            RFIDEquipmentBinding.RFIDEquipment = RFIDClosureData.Label
            ORDER BY Date DESC
            """
        pressform = self.SQLExecute(sql)
        if len(pressform) > 0:
            return pressform[0][0]
        else:
            return None

    # Метод обновляет данные в таблице ProductionData для сменного задания
    def UpdateCountClosures(self, ShiftTaskOid,ShiftOid, specification, plan, socketcount, tpaoid):
        # Если случано передали пустое сменное задание возвращаем пустое значние
        if ShiftTaskOid == '':
            return
        # Проверяем не закрыто ли сменное задание в таблице ProductionData
        # Если статус ProductionData == 2 тогда обнуляем сменное задание у ТПА
        check_date_dataproduction_sql = f"""
                SELECT [Oid]
                    ,[ShiftTask]
                    ,[RigEquipment]
                    ,[Status]
                    ,[StartDate]
                    ,[EndDate]
                    ,[CountFact]
                    ,[CycleFact]
                    ,[WeightFact]
                    ,[SpecificationFact]
                FROM [MES_Iplast].[dbo].[ProductionData] WHERE ShiftTask = '{ShiftTaskOid}'
            """
        production_data = self.SQLExecute(check_date_dataproduction_sql)
        if len(production_data) > 0:
            production_data = production_data[0]
            if production_data[3] == 2:
                for i in range(0, len(self.tpalist)):
                    if self.tpalist[i][0] == tpaoid:
                        self.tpalist[i][3]['ShiftTask'] = []
                        return
        else: return

        # Получаем количество смыканий сделанных во время исполнения сменного задания
        # с учётом исключения смыканий прошлых сменных заданий за смену переменной offset
        offset = self.offsetlist[tpaoid]
        sql = f"""
            SELECT RCD.[Oid]
                ,[Controller]
                ,[Label]
                ,[Date]
                ,RCD.[Cycle]
                ,[Status]
                ,Shift.Note
            FROM [MES_Iplast].[dbo].[RFIDClosureData] as RCD, ShiftTask, Shift 
            WHERE 
            Controller = (SELECT RFIDEquipmentBinding.RFIDEquipment 
                                FROM RFIDEquipmentBinding, ShiftTask
                                WHERE ShiftTask.Equipment = RFIDEquipmentBinding.Equipment and 
                                ShiftTask.Oid = '{ShiftTaskOid}') AND
            ShiftTask.Oid = '{ShiftTaskOid}' AND
            Shift.Oid = ShiftTask.Shift AND
            Date between Shift.StartDate AND Shift.EndDate AND
            Status = 1
            ORDER BY Date ASC OFFSET {offset} ROWS   
        """
        result = self.SQLExecute(sql)
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
            # Высчитываем средний цикл без учета переменной offset так как нам
            # требуется средний цикл за смену а не за сменное задание
            sql_get_average_cycle = f"""
                            SELECT RCD.[Oid]
                                ,[Controller]
                                ,[Label]
                                ,[Date]
                                ,RCD.[Cycle]
                                ,[Status]
                                ,Shift.Note
                            FROM [MES_Iplast].[dbo].[RFIDClosureData] as RCD, ShiftTask, Shift 
                            WHERE 
                            Controller = (SELECT RFIDEquipmentBinding.RFIDEquipment 
                                                FROM RFIDEquipmentBinding, ShiftTask
                                                WHERE ShiftTask.Equipment = RFIDEquipmentBinding.Equipment and 
                                                ShiftTask.Oid = '{ShiftTaskOid}') AND
                            ShiftTask.Oid = '{ShiftTaskOid}' AND
                            Shift.Oid = ShiftTask.Shift AND
                            Date between Shift.StartDate AND Shift.EndDate
                            ORDER BY Date ASC OFFSET 0 ROWS   
            """
            cycle_request = self.SQLExecute(sql_get_average_cycle)
            average_cycle = 0
            for num in range(0,len(cycle_request)):
                try:
                    average_cycle += cycle_request[num][4] + cycle_request[num+1][4]
                except:
                    average_cycle = average_cycle / num
            # Проверяем статусы записи
            # Если статус 1 то обновляем значения
            if (production_data[3] == 1):
                update_sql = ""
                get_current_shift = """
                    SELECT TOP (1) [Oid]
                    FROM [MES_Iplast].[dbo].[Shift] 
                    ORDER BY StartDate DESC
                """
                current_shift = self.SQLExecute(get_current_shift)
                current_shift = current_shift[0][0]
                average_weight = self.SQLExecute(f"""
                    SELECT SUM(Weight)/COUNT(Weight)
                        FROM [MES_Iplast].[dbo].[ProductWeight]
                        WHERE ProductionData = '{production_data[0]}'
                """)
                if len(average_weight) > 0:
                    if average_weight[0][0] != None:
                        average_weight = average_weight[0][0]
                    else:
                        average_weight = 0
                # Если количество произведенного продукта больше плана
                # То присваиваем записи статус 2 тем самым закрывая сменное задание,
                # и обнуляем его у ТПА чтобы ТПА смог получить новое
                if count >= plan:
                    update_sql = f"""
                        UPDATE ProductionData
                        SET CountFact = '{plan}', 
                            CycleFact = '{average_cycle}', 
                            SpecificationFact = '{specification}', 
                            Status = 2,
                            WeightFact = '{average_weight}'
                        WHERE Oid = '{production_data[0]}'
                    """
                    for i in range(0, len(self.tpalist)):
                        if self.tpalist[i][0] == tpaoid:
                            self.tpalist[i][3]['ShiftTask'] = []
                            break
                else:
                    # Если срок сменного задания ограниченного сменой закончился
                    # То присваиваем записи статус 2 для её закрытия и обнуляем
                    # сменное задание у ТПА для получения нового
                    if current_shift != ShiftOid:
                        update_sql = f"""
                            UPDATE ProductionData
                            SET CountFact = '{plan}', 
                                CycleFact = '{average_cycle}', 
                                SpecificationFact = '{specification}', 
                                Status = 2,
                                WeightFact = '{average_weight}'
                            WHERE Oid = '{production_data[0]}'
                        """
                        for i in range(0, len(self.tpalist)):
                            if self.tpalist[i][0] == tpaoid:
                                self.tpalist[i][3]['ShiftTask'] = []
                                break
                    else:
                        # Иначе просто обновляем запись с новыми значениями
                        update_sql = f"""
                            UPDATE ProductionData
                            SET CountFact = '{count}',
                                CycleFact = '{average_cycle}',
                                SpecificationFact = '{specification}',
                                EndDate = '{enddate}',
                                WeightFact = '{average_weight}'
                            WHERE Oid = '{production_data[0]}'
                        """
                self.SQLExecute(update_sql)
            # Если запись была только создана и она не закрыта задаём начальные значения
            # далее при следующей итерации цикла она заполнится подсчитываемыми значениями
            if ((production_data[3] == 0) and
               (production_data[4] == None) and
               (production_data[5] == None) and
               (production_data[6] != 2)):
               update_sql = f"""
               UPDATE ProductionData
               SET StartDate = '{startdate}',
                    EndDate = '{enddate}',
                    Status = 1,
                    SpecificationFact = '{specification}'
               WHERE Oid = '{production_data[0]}'
               """
               self.SQLExecute(update_sql)