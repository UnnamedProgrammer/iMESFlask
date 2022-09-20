from iMES.Model.SQLManipulator import SQLManipulator
from dataclasses import dataclass

@dataclass
class IndexController():
    tpa: str
    pressform: str = None
    product: str = None
    production_plan: int = None
    cycle: int = None
    cycle_fact: float = None
    plan_weight: float = None
    average_weight: float = None
    shift: str = None
    print_paper: int = None

    def data_from_shifttask(self):
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
            [ShiftTask].Equipment = '{self.tpa}' AND
            ShiftTask.Shift = Shift.Oid AND
            ShiftTask.Product = Product.Oid
        """
        data = SQLManipulator.SQLExecute(sql)
        data = data[0]
        self.product = data[4]
        self.production_plan = data[11]
        self.cycle = data[12]
        self.plan_weight = round(data[13])
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
        if len(pf) > 0:
            self.pressform = pf[0][0]
        else:
            self.pressform = ''