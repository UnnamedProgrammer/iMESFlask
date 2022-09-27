from iMES.Model.SQLManipulator import SQLManipulator
from dataclasses import dataclass
from datetime import datetime

@dataclass
class IndexController():
    tpa: str = ''
    pressform: str = ''
    product: str = ''
    production_plan: int = 0
    cycle: int = 0
    cycle_fact: float = 0
    plan_weight: float = 0
    average_weight: float = 0
    shift: str = ''
    print_paper: int = 0
    shift_task_oid: str = ''
    product_fact: str = 0
    label: str = ''
    controller: str = ''
    tpa_is_works: bool = False

    def data_from_shifttask(self):
        sql = f"""
            SELECT TOP (100) [ShiftTask].[Oid]
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
            [ShiftTask].Equipment = '{self.tpa}' AND
            Shift.Oid = (SELECT TOP(1) Oid FROM Shift ORDER BY StartDate DESC ) AND
            ShiftTask.Product = Product.Oid
        """
        data = SQLManipulator.SQLExecute(sql)
        pf = ''
        if len(data) > 0:
            data = data[0]
            self.shift_task_oid = data[0]
            self.product = data[4]
            self.production_plan = data[11]
            self.cycle = data[12]
            self.plan_weight = data[13].normalize()
            self.shift = data[1]
            sql = f"""
                SELECT TOP (1) Equipment.Name, RFIDClosureData.Date
                FROM [MES_Iplast].[dbo].[RFIDClosureData], RFIDEquipmentBinding, Equipment 
                WHERE 
                Controller = (SELECT RFIDEquipment 
                                FROM RFIDEquipmentBinding 
                                WHERE Equipment = '{self.tpa}') AND
                RFIDClosureData.Label = RFIDEquipmentBinding.RFIDEquipment AND
                RFIDEquipmentBinding.Equipment = Equipment.Oid
                ORDER BY Date DESC
            """
            pf = SQLManipulator.SQLExecute(sql)
        else:
            self.shift_task_oid = ''
            self.product = ''
            self.production_plan = 0
            self.cycle = 0
            self.plan_weight = 0
            self.shift = SQLManipulator.SQLExecute("""
            SELECT TOP (1) [Note]
            FROM [MES_Iplast].[dbo].[Shift] ORDER BY StartDate DESC            
            """)[0][0]
        if len(pf) > 0:
            self.pressform = pf[0][0]
        else:
            self.pressform = ''
        if self.shift_task_oid != None and self.shift_task_oid != '':
            production_data_sql = f"""
                SELECT
                    [CountFact]
                    ,[CycleFact]
                    ,[WeightFact]
                FROM [MES_Iplast].[dbo].[ProductionData] WHERE ShiftTask = '{self.shift_task_oid}'
            """
            production_data = SQLManipulator.SQLExecute(production_data_sql)
            if len(production_data) > 0:
                production_data = production_data[0]
                if production_data[0] == None:               
                    self.product_fact = 0
                else:
                    self.product_fact = production_data[0]
                if production_data[1] == None:
                    self.cycle_fact = 0
                else:
                    self.cycle_fact = round(float(production_data[1]))