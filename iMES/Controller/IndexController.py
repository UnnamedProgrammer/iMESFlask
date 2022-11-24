from iMES.Model.SQLManipulator import SQLManipulator
from dataclasses import dataclass
from datetime import datetime

@dataclass
class IndexController():
    tpa: str = ''
    pressform: str = ''
    product : tuple = ()
    production_plan : tuple = ()
    cycle: int = 0
    cycle_fact: float = 0
    plan_weight: float = 0
    average_weight: float = 0
    shift: str = ''
    print_paper: int = 0
    shift_task_oid : tuple = ()
    product_fact : tuple  = ()
    label: str = ''
    controller: str = ''
    tpa_is_works: bool = False
    PackingURL: str = ''
    StartDate: datetime = None
    EndDate: datetime = None
    ProductCount = 0
    tpa_message: str = ''

    def data_from_shifttask(self):
        sql = f"""
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
            FROM [MES_Iplast].[dbo].[ShiftTask], Product, Shift WHERE 
            [ShiftTask].Equipment = '{self.tpa}' AND
            Shift.Oid = (SELECT TOP(1) Oid FROM Shift ORDER BY StartDate DESC ) AND
            ShiftTask.Product = Product.Oid AND EXISTS
            (SELECT * FROM ProductionData WHERE ProductionData.ShiftTask = ShiftTask.Oid AND Status = 1)
        """
        data = SQLManipulator.SQLExecute(sql)
        # Проверка прессформы
        sql = f"""
            SELECT TOP (1) Equipment.Name, RFIDClosureData.Date
            FROM [MES_Iplast].[dbo].[RFIDClosureData], RFIDEquipmentBinding, Equipment 
            WHERE 
            Controller = (SELECT RFIDEquipment 
                            FROM RFIDEquipmentBinding 
                            WHERE Equipment = '{self.tpa}') AND
            RFIDEquipmentBinding.RFIDEquipment = RFIDClosureData.Label AND
            Equipment.Oid = RFIDEquipmentBinding.Equipment
            ORDER BY Date DESC
            """
        pf = SQLManipulator.SQLExecute(sql)
        if len(pf) > 0:
            if pf[0][0] == None or pf == () or pf == []:
                self.pressform = 'Метка не привязана к прессформе'
                self.tpa_message = 'Для получения сменного задания выберите пресс-форму'
            else:
                self.pressform = pf[0][0]
        else:
            self.pressform = 'Не определена'
        #---------------------------------------------------

        if len(data) > 0:
            st_oid = []
            product_list = []
            production_plan = []
            for shift_task in data:
                st_oid.append(shift_task[0])
                product_list.append(shift_task[4])
                production_plan.append(shift_task[11])
                self.cycle = shift_task[12]
                self.plan_weight = round(shift_task[13])
                self.shift = shift_task[1]
                self.PackingURL = shift_task[15]

            self.shift_task_oid = st_oid
            self.product = tuple(product_list)
            self.production_plan = tuple(production_plan)
        else:
            self.shift_task_oid = ()
            self.product = 'Нет сменного задания'
            self.production_plan = 0
            self.cycle = 0
            self.plan_weight = 0
            self.shift = SQLManipulator.SQLExecute("""
            SELECT TOP (1) [Note]
            FROM [MES_Iplast].[dbo].[Shift] ORDER BY StartDate DESC            
            """)[0][0]

        if self.shift_task_oid != None and len(self.shift_task_oid) > 0:
            production_data = []
            for task_oid in self.shift_task_oid:
                production_data_sql = f"""
                    SELECT
                        [CountFact]
                        ,[CycleFact]
                        ,[WeightFact]
                        ,[StartDate]
                        ,[EndDate]
                    FROM [MES_Iplast].[dbo].[ProductionData] WHERE ShiftTask = '{task_oid}'
                """
                result = SQLManipulator.SQLExecute(production_data_sql)
                production_data.append(result)
            if len(production_data) > 0:
                product_fact = []
                for pd in production_data:
                    pd = pd[0]
                    self.StartDate = pd[3]
                    self.EndDate = pd[4]
                    if pd[0] == None:               
                        product_fact = (0)
                    else:
                        product_fact.append(pd[0])
                    if pd[1] == None:
                        self.cycle_fact = 0
                    else:
                        self.cycle_fact = round(float(pd[1]))
                self.product_fact = tuple(product_fact)
                self.ProductCount = len(self.product)
        
        average_weight_sql = """

        """