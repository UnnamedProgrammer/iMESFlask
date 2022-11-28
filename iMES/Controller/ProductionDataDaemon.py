from threading import Thread
from time import sleep
from iMES.Model.SQLManipulator import SQLManipulator
from iMES import app



class ProductionDataDaemon():
    def __init__(self):
        self.shift = 0
        self.tpalist = self.GetAllTpa()
        self.completed_clousers = {}
        self.offsetlist = {}
    def Start(self):
        thread = Thread(target=self.TpaProductionDataMonitoring, args=())
        thread.start()
        app.logger.info("Демон мониторинга продукции запущен")

    def TpaProductionDataMonitoring(self):
        while True:
            for tpanum in range(0,len(self.tpalist)):
                try:
                    if len(self.tpalist[tpanum][3]['ShiftTask']) > 0:
                        for shift_task in self.tpalist[tpanum][3]['ShiftTask']: 
                            self.CreateProductionDataRecord(shift_task)
                            self.UpdateCountClosures(shift_task[0],
                                                    shift_task[16],
                                                    shift_task[5],
                                                    shift_task[11],
                                                    shift_task[10],
                                                    shift_task[2])
                    else:
                        shift_task_list = self.GetShiftTaskForTpa(self.tpalist[tpanum][0])
                        self.tpalist[tpanum][3]["ShiftTask"] = shift_task_list
                except IndexError:
                    continue
                except Exception as error:
                    app.logger.info(error, "on", str(self.tpalist[tpanum]))
                    continue
            sleep(3)

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
        result_sql = SQLManipulator.SQLExecute(sql)
        for tpa in result_sql:
            tpa_obj = list(tpa)
            tpa_obj.append({'ShiftTask':[]})
            TpaList.append(tpa_obj)
        return TpaList

    def GetShiftTaskForTpa(self,tpaoid):
        shift_tasks = self.GetShiftTaskByEquipmentPerformance(tpaoid)
        
        return shift_tasks
    
    def GetShiftTaskByEquipmentPerformance(self,tpaoid):
        shift_tasks = []
        pressform = self.GetTpaPressFrom(tpaoid)
        equipment_performance = self.GetEquipmentPerformance(tpaoid,pressform)
        if equipment_performance != None:
            total_socket_count = equipment_performance[4]
            if total_socket_count == 0:
                total_socket_count = 1
            products = self.GetProductionProducts(equipment_performance[0])
            for product in products:
                empty_sockets = total_socket_count
                shift = self.GetCurrentShift()
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
                
        return shift_tasks
    
    # Метод возвращает Oid текущей смены
    def GetCurrentShift(self):
        sql = """
            SELECT TOP(1) [Oid]
            FROM [MES_Iplast].[dbo].[Shift] ORDER BY StartDate DESC
        """
        shift_oid = SQLManipulator.SQLExecute(sql)
        return shift_oid[0][0]

    # Метод ищет совпадающее по заданным параметрам сменное задание
    def GetShiftTask(self,shift,equipment,product,cycle):
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
        shift_task = SQLManipulator.SQLExecute(sql_ST)
        if len(shift_task) > 0:
            for st in shift_task:
                sql = f"""
                    SELECT [Oid] ,[CountFact]
                    FROM [MES_Iplast].[dbo].[ProductionData] 
                    WHERE ShiftTask = '{st[0]}' AND Status = 2
                """
                find_shifttask_ended = SQLManipulator.SQLExecute(sql)
                if len(find_shifttask_ended):
                    shift_task.remove(st)
                    offset += find_shifttask_ended[0][1]
        self.offsetlist[equipment] = offset
        return shift_task
        
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
            EP = SQLManipulator.SQLExecute(sql)
            if bool(EP):
                return EP[0]
            else:
                return None

    def GetProductionProducts(self,equipment_performance_oid):
        sql = f"""
            SELECT [EquipmentPerformance]
                ,[Product]
                ,[SocketCount]
                ,[Cycle]
            FROM [MES_Iplast].[dbo].[Relation_ProductPerformance]
            WHERE EquipmentPerformance = '{equipment_performance_oid}'
        """
        list = SQLManipulator.SQLExecute(sql)
        products = []
        for product in list:
            products.append(product)
        return products

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
        result = SQLManipulator.SQLExecute(sql)
        if len(result) > 0:
            return True
        else:
            return False

    def CreateProductionDataRecord(self, shifttaskdata):
        sql = ''
        if shifttaskdata != '':
            if not self.ProductionDataRecordIsCreated(shifttaskdata[0]):
                pressform = self.GetTpaPressFrom(shifttaskdata[2])
                if pressform != '':
                    sql = f"""
                    INSERT INTO ProductionData (Oid, ShiftTask, RigEquipment,Status, StartDate, EndDate, CountFact, CycleFact,WeightFact,SpecificationFact)
                    VALUES (NEWID(),'{shifttaskdata[0]}','{pressform}', 0, NULL,NULL,NULL,NULL,NULL,'{shifttaskdata[5]}')
                    """
                    SQLManipulator.SQLExecute(sql)
                elif pressform == '':
                    sql = f"""
                    INSERT INTO ProductionData (Oid, ShiftTask, RigEquipment,Status, StartDate, EndDate, CountFact, CycleFact,WeightFact,SpecificationFact)
                    VALUES (NEWID(),'{shifttaskdata[0]}',NULL, 0, NULL,NULL,NULL,NULL,NULL,'{shifttaskdata[5]}')
                    """
                    SQLManipulator.SQLExecute(sql)

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
        pressform = SQLManipulator.SQLExecute(sql)
        if len(pressform) > 0:
            return pressform[0][0]
        else:
            return None

    def UpdateCountClosures(self, ShiftTaskOid,ShiftOid, specification, plan, socketcount, tpaoid):
        if ShiftTaskOid == '':
            return
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
        result = SQLManipulator.SQLExecute(sql)
        if len(result) > 0:
            count = (len(result)) * socketcount
            startdate = result[0][3].strftime('%Y-%m-%dT%H:%M:%S')
            try:
                enddate = result[(offset+plan)-1][3].strftime('%Y-%m-%dT%H:%M:%S')
            except:
                try:
                    enddate = result[plan-1][3].strftime('%Y-%m-%dT%H:%M:%S')
                except:
                    enddate =result[len(result)-1][3].strftime('%Y-%m-%dT%H:%M:%S')
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
                            ORDER BY Date ASC OFFSET {offset} ROWS   
            """
            cycle_request = SQLManipulator.SQLExecute(sql_get_average_cycle)
            average_cycle = 0
            for num in range(0,len(cycle_request)):
                try:
                    average_cycle += cycle_request[num][4] + cycle_request[num+1][4]
                except:
                    average_cycle = average_cycle / num

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
            production_data = SQLManipulator.SQLExecute(check_date_dataproduction_sql)
            if len(production_data) > 0:
                production_data = production_data[0]
            else: return
            if (production_data[3] == 1):
                update_sql = ""
                get_current_shift = """
                    SELECT TOP (1) [Oid]
                    FROM [MES_Iplast].[dbo].[Shift] 
                    ORDER BY StartDate DESC
                """
                current_shift = SQLManipulator.SQLExecute(get_current_shift)
                current_shift = current_shift[0][0]
                if count >= plan:
                    update_sql = f"""
                        UPDATE ProductionData
                        SET CountFact = '{plan}'
                        WHERE Oid = '{production_data[0]}'
                        UPDATE ProductionData
                        SET CycleFact = '{average_cycle}'
                        WHERE Oid = '{production_data[0]}'
                        UPDATE ProductionData
                        SET SpecificationFact = '{specification}'
                        WHERE Oid = '{production_data[0]}'
                        UPDATE ProductionData
                        SET Status = 2
                        WHERE Oid = '{production_data[0]}'
                    """
                    for i in range(0, len(self.tpalist)):
                        if self.tpalist[i][0] == tpaoid:
                            self.tpalist[i].pop(3)
                else:
                    if current_shift != ShiftOid:
                        update_sql = f"""
                        UPDATE ProductionData
                        SET CountFact = {count}
                        WHERE Oid = '{production_data[0]}'
                        UPDATE ProductionData
                        SET CycleFact = '{average_cycle}'
                        WHERE Oid = '{production_data[0]}'
                        UPDATE ProductionData
                        SET SpecificationFact = '{specification}'
                        WHERE Oid = '{production_data[0]}'
                        UPDATE ProductionData
                        SET Status = 2
                        WHERE Oid = '{production_data[0]}'
                        """
                        for i in range(0, len(self.tpalist)):
                            if self.tpalist[i][0] == tpaoid:
                                self.tpalist[i].pop(3)
                    else:
                        update_sql = f"""
                            UPDATE ProductionData
                            SET CountFact = {count}
                            WHERE Oid = '{production_data[0]}'
                            UPDATE ProductionData
                            SET CycleFact = '{average_cycle}'
                            WHERE Oid = '{production_data[0]}'
                            UPDATE ProductionData
                            SET SpecificationFact = '{specification}'
                            WHERE Oid = '{production_data[0]}'
                            UPDATE ProductionData
                            SET EndDate = '{enddate}'
                            WHERE Oid = '{production_data[0]}'
                        """
                SQLManipulator.SQLExecute(update_sql)
            if ((production_data[3] == 0) and
               (production_data[4] == None) and
               (production_data[5] == None) and
               (production_data[6] != 2)):
               update_sql = f"""
               UPDATE ProductionData
               SET StartDate = '{startdate}'
               WHERE Oid = '{production_data[0]}'
               UPDATE ProductionData
               SET EndDate = '{enddate}'
               WHERE Oid = '{production_data[0]}'
               UPDATE ProductionData
               SET Status = 1
               WHERE Oid = '{production_data[0]}'
               UPDATE ProductionData
               SET SpecificationFact = '{specification}'
               WHERE Oid = '{production_data[0]}'
               """
               SQLManipulator.SQLExecute(update_sql)