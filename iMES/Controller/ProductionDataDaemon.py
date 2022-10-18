from threading import Thread
from time import sleep
from iMES.Model.SQLManipulator import SQLManipulator
from iMES import current_tpa,TpaList
from datetime import datetime



class ProductionDataDaemon():
    def __init__(self):
        self.shift = 0
        self.tpalist = self.GetAllTpa()
        self.completed_clousers = {}

    def Start(self):
        thread = Thread(target=self.TpaProductionDataMonitoring, args=())
        thread.start()
        print("Демон мониторинга продукции запущен")

    def TpaProductionDataMonitoring(self):
        while True:
            for tpanum in range(0,len(self.tpalist)):
                try:
                    self.tpalist[tpanum][3]['ShiftTask']
                except IndexError:
                    self.tpalist[tpanum].append({"ShiftTask":self.GetShiftTaskForTpa(self.tpalist[tpanum][0])})
                    self.CreateProductionDataRecord(self.tpalist[tpanum][3]['ShiftTask'])
                if(self.tpalist[tpanum][3]['ShiftTask'] != ''):
                    self.UpdateCountClosures(self.tpalist[tpanum][3]['ShiftTask'][0],
                                             self.tpalist[tpanum][3]['ShiftTask'][16],
                                             self.tpalist[tpanum][3]['ShiftTask'][5],
                                             self.tpalist[tpanum][3]['ShiftTask'][11],
                                             self.tpalist[tpanum][3]['ShiftTask'][10],
                                             self.tpalist[tpanum][0])
            sleep(120)

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
            TpaList.append(list(tpa))
        return TpaList

    def GetShiftTaskForTpa(self,tpaoid):
        self.completed_clousers[tpaoid] = 0
        sql_shiftask = f"""
            SELECT TOP (1000) [ShiftTask].[Oid]
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
            FROM [MES_Iplast].[dbo].[ShiftTask], Product, Shift WHERE 
            [ShiftTask].Equipment = '{tpaoid}' AND
            Shift.Oid = (SELECT TOP(1) Oid FROM Shift ORDER BY StartDate DESC ) AND
            ShiftTask.Product = Product.Oid
        """
        sql_product = f"""
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
            FROM [MES_Iplast].[dbo].[ProductionData] WHERE Status = 2
        """
        completed_products = SQLManipulator.SQLExecute(sql_product)
        shifttasks = SQLManipulator.SQLExecute(sql_shiftask)
        pass_clousers = 0
        new_shift_task = ''
        ended_shifttasks = []
        for shifttask in shifttasks:
            if(completed_products != []):
                for complete_product in completed_products:
                    if complete_product[1] != shifttask[0]:
                        new_shift_task = shifttask
                        continue
                    else:
                        pass_clousers += complete_product[6]
                        ended_shifttasks.append(shifttask[0])
                        new_shift_task = ''
                        continue
                if (new_shift_task == '') or (new_shift_task[0] in ended_shifttasks):
                    continue
                else:
                    break
            else:
                new_shift_task = shifttask
                break
        self.completed_clousers[tpaoid] = pass_clousers
        return new_shift_task
    
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
        if shifttaskdata != '':
            if not self.ProductionDataRecordIsCreated(shifttaskdata[0]):
                pressform = self.GetTpaPressFrom(shifttaskdata[2])
                if pressform != '':
                    sql = f"""
                    INSERT INTO ProductionData (Oid, ShiftTask, RigEquipment,Status, StartDate, EndDate, CountFact, CycleFact,WeightFact,SpecificationFact)
                    VALUES (NEWID(),'{shifttaskdata[0]}','{pressform}', 0, NULL,NULL,NULL,NULL,NULL,'{shifttaskdata[5]}')
                    """
                    SQLManipulator.SQLExecute(sql)

    def GetTpaPressFrom(self,tpaoid):
        sql = f"""
                SELECT TOP (1) Equipment.Oid, RFIDClosureData.Date
                FROM [MES_Iplast].[dbo].[RFIDClosureData], RFIDEquipmentBinding, Equipment 
                WHERE 
                Controller = (SELECT RFIDEquipment 
                                FROM RFIDEquipmentBinding 
                                WHERE Equipment = '{tpaoid}') AND
                RFIDClosureData.Label = RFIDEquipmentBinding.RFIDEquipment AND
                RFIDEquipmentBinding.Equipment = Equipment.Oid
                ORDER BY Date DESC
            """
        pressform = SQLManipulator.SQLExecute(sql)
        if len(pressform) > 0:
            return pressform[0][0]
        else:
            return ''

    def UpdateCountClosures(self, ShiftTaskOid,ShiftOid, specification, plan, socketcount, tpaoid):
        if ShiftTaskOid == '':
            return
        offset = self.completed_clousers[tpaoid]
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
            Date between Shift.StartDate AND Shift.EndDate
            ORDER BY Date ASC OFFSET {offset} ROWS   
        """
        result = SQLManipulator.SQLExecute(sql)
        for ip_addr in TpaList.keys():
            for tpa in TpaList[ip_addr]:
                if tpa['Oid'] == tpaoid:
                    tpa['WorkStatus'] = self.Get_Tpa_Status(ShiftTaskOid)
        if len(result) > 0:
            count = (len(result)/2) * socketcount
            startdate = result[0][3].strftime('%Y-%m-%dT%H:%M:%S')
            enddate = result[len(result)-1][3].strftime('%Y-%m-%dT%H:%M:%S')
            average_cycle = 0
            for num in range(0,len(result)):
                try:
                    average_cycle += result[num][4] + result[num+1][4]
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

    def Get_Tpa_Status(self,shifttaskoid):
        if shifttaskoid == None or shifttaskoid == '':
            self.tpa_is_works = False
            return False
        sql = f"""
            SELECT TOP(1) [Date]
            FROM [MES_Iplast].[dbo].[RFIDClosureData] as RCD, ShiftTask, Shift 
            WHERE 
            Controller = (SELECT RFIDEquipmentBinding.RFIDEquipment 
                                FROM RFIDEquipmentBinding, ShiftTask
                                WHERE ShiftTask.Equipment = RFIDEquipmentBinding.Equipment and 
                                ShiftTask.Oid = '{shifttaskoid}') AND
            ShiftTask.Oid = '{shifttaskoid}' AND
            Shift.Oid = ShiftTask.Shift AND
            Date between Shift.StartDate AND Shift.EndDate
            ORDER BY Date DESC 
        """
        last_closure_date = SQLManipulator.SQLExecute(sql)
        if len(last_closure_date) > 0:
            last_closure_date = last_closure_date[0][0]
            current_date = datetime.now()
            last_closure_date = last_closure_date
            minutes = (current_date - last_closure_date).total_seconds()
            if minutes >= 600:
                return False
            else:
                return True
        else:
            return False