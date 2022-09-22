from threading import Thread
from time import sleep
from iMES.Model.SQLManipulator import SQLManipulator

class ProductionDataDaemon():
    def __init__(self):
        self.shift = 0
        self.tpalist = self.GetAllTpa()
    
    def Start(self):
        thread = Thread(target=self.TpaProductionDataMonitoring, args=())
        thread.start()
        print("Демон мониторинга продукции запущен")

    def TpaProductionDataMonitoring(self):
        while True:
            for tpanum in range(0,len(self.tpalist)):
                self.tpalist[tpanum].append({"ShiftTask":self.GetShiftTaskForTpa(self.tpalist[tpanum][0])})
                self.CreateProductionDataRecord(self.tpalist[tpanum][3]['ShiftTask'])
                if(self.tpalist[tpanum][3]['ShiftTask'] != ''):
                    self.UpdateCountClosures(self.tpalist[tpanum][3]['ShiftTask'][0],
                                             self.tpalist[tpanum][3]['ShiftTask'][5],
                                             self.tpalist[tpanum][3]['ShiftTask'][11],
                                             self.tpalist[tpanum][3]['ShiftTask'][10])
            sleep(60)

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
        sql = f"""
            SELECT TOP (1) [ShiftTask].[Oid]
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
            FROM [MES_Iplast].[dbo].[ShiftTask], Product, Shift WHERE 
            [ShiftTask].Equipment = '{tpaoid}' AND
            Shift.Oid = (SELECT TOP(1) Oid FROM Shift ORDER BY StartDate DESC ) AND
            ShiftTask.Product = Product.Oid
        """
        result = SQLManipulator.SQLExecute(sql)
        if len(result) > 0: return result[0]
        else: return ''
    
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

    def UpdateCountClosures(self, ShiftTaskOid, specification, plan,socketcount):
        if ShiftTaskOid == '':
            return
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

            ORDER BY Date ASC    
        """
        result = SQLManipulator.SQLExecute(sql)
        if len(result) > 0:
            get_production_data_sql = f"""
                SELECT   COUNT(RCD.[Oid])/2
                        ,MIN([Date])
                        ,MAX([Date])
                        ,SUM(RCD.Cycle)/COUNT(RCD.[Oid])
                FROM [MES_Iplast].[dbo].[RFIDClosureData] as RCD, ShiftTask, Shift 
                WHERE 
                Controller = (SELECT RFIDEquipmentBinding.RFIDEquipment 
                                    FROM RFIDEquipmentBinding, ShiftTask
                                    WHERE ShiftTask.Equipment = RFIDEquipmentBinding.Equipment and 
                                    ShiftTask.Oid = '{ShiftTaskOid}') AND
                ShiftTask.Oid = '{ShiftTaskOid}' AND
                Shift.Oid = ShiftTask.Shift AND
                Date between Shift.StartDate AND Shift.EndDate
            """
            count_result = SQLManipulator.SQLExecute(get_production_data_sql)
            if len(count_result) > 0:
                count_result = count_result[0]
            else: return
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
            if (production_data[6] == plan):
                sql = f"""
                        UPDATE ProductionData
                        SET Status = 2
                        WHERE Oid = '{production_data[0]}'  
                    """
                SQLManipulator.SQLExecute(sql)
            if (production_data[3] == 1):
                count = count_result[0] * socketcount
                update_sql = f"""
                    UPDATE ProductionData
                    SET CountFact = '{count}'
                    WHERE Oid = '{production_data[0]}'
                    UPDATE ProductionData
                    SET CycleFact = '{count_result[3]}'
                    WHERE Oid = '{production_data[0]}'
                    UPDATE ProductionData
                    SET SpecificationFact = '{specification}'
                    WHERE Oid = '{production_data[0]}'
                """
                SQLManipulator.SQLExecute(update_sql)
            if ((production_data[3] == 0) and
               (production_data[4] == None) and
               (production_data[5] == None) and
               (production_data[6] != 2)):
               datestart = count_result[1].strftime('%Y-%m-%dT%H:%M:%S')
               dateend = count_result[2].strftime('%Y-%m-%dT%H:%M:%S')
               update_sql = f"""
               UPDATE ProductionData
               SET StartDate = '{datestart}'
               WHERE Oid = '{production_data[0]}'
               UPDATE ProductionData
               SET EndDate = '{dateend}'
               WHERE Oid = '{production_data[0]}'
               UPDATE ProductionData
               SET Status = 1
               WHERE Oid = '{production_data[0]}'
               UPDATE ProductionData
               SET SpecificationFact = '{specification}'
               WHERE Oid = '{production_data[0]}'
               """
               SQLManipulator.SQLExecute(update_sql)