from iMES.Model.BaseObjectModel import BaseObjectModel


class ShiftTaskDataGrubber(BaseObjectModel):
    def __init__(self) -> None:
        super().__init__()
        self.tpa = ''
        self.pressform = ''
        self.production_plan = ()
        self.cycle = 0
        self.cycle_fact = 0
        self.plan_weight = ()
        self.average_weight = ()
        self.shift = ''
        self.shift_task_oid = ''
        self.product_fact = ()
        self.label = ''
        self.controller = 'Empty'
        self.PackingURL = ''
        self.StartDate = None
        self.EndDate = None
        self.ProductCount = 0
        self.wastes = ()
        self.shift_tasks_traits = ()

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
                ,[Traits]
                ,[ExtraTraits]
            FROM [MES_Iplast].[dbo].[ShiftTask], Product, Shift WHERE 
            [ShiftTask].Equipment = '{self.tpa}' AND
            Shift.Oid = (SELECT TOP(1) Oid FROM Shift ORDER BY StartDate DESC ) AND
            ShiftTask.Product = Product.Oid AND EXISTS
            (SELECT * FROM ProductionData WHERE ProductionData.ShiftTask = ShiftTask.Oid AND Status = 1)
        """
        data = self.SQLExecute(sql)
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
        pf = self.SQLExecute(sql)
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
            plan_weight = []
            traits = []
            for shift_task in data:
                st_oid.append(shift_task[0])
                product_list.append(shift_task[4])
                production_plan.append(shift_task[11])
                self.cycle = shift_task[12]
                plan_weight.append(f"{float(shift_task[13]):.{2}f}")
                self.shift = shift_task[1]
                self.PackingURL = shift_task[15]

            self.shift_task_oid = st_oid
            self.product = tuple(product_list)
            self.production_plan = tuple(production_plan)
            self.plan_weight = tuple(plan_weight)

            for i in range(0,len(data)):
                traits.append([self.product[i],
                               f"{data[i][16]} {data[i][17]}",
                               self.production_plan[i],
                               self.cycle,
                               self.cycle,self.plan_weight[i]])
            self.shift_tasks_traits = tuple(traits)
        else:
            self.shift_task_oid = ()
            self.product = 'Нет сменного задания'
            self.production_plan = 0
            self.cycle = 0
            self.plan_weight = 0
            self.shift = self.SQLExecute("""
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
                result = self.SQLExecute(production_data_sql)
                production_data.append(result)
            if len(production_data) > 0:
                product_fact = []
                for pd in production_data:
                    pd = pd[0]
                    self.StartDate = pd[3]
                    self.EndDate = pd[4]
                    if pd[0] == None:               
                        product_fact = [0]
                    else:
                        product_fact.append(pd[0])
                    if pd[1] == None:
                        self.cycle_fact = 0
                    else:
                        self.cycle_fact = f"{float(pd[1]):.{1}f}"
                self.product_fact = tuple(product_fact)
                self.ProductCount = len(self.product)
        average_weight = []
        wastes = []
        for task_oid in self.shift_task_oid:
            get_production_data_sql = f"""
                SELECT TOP(1) [Oid]
                FROM [MES_Iplast].[dbo].[ProductionData] WHERE ShiftTask = '{task_oid}'
            """
            production_data_oid = self.SQLExecute(get_production_data_sql)
            if len(production_data_oid) > 0:
                production_data_oid = production_data_oid[0][0]
                average_weight_sql = f"""
                    SELECT SUM(Weight)/COUNT(Weight)
                    FROM [MES_Iplast].[dbo].[ProductWeight] 
                    WHERE ProductionData = '{production_data_oid}'
                """
                wastes_sql = f"""
                    SELECT [Count]
                    FROM [MES_Iplast].[dbo].[ProductWaste] WHERE ProductionData = '{production_data_oid}'
                """
                average_weight_result = self.SQLExecute(average_weight_sql)
                wastes_result = self.SQLExecute(wastes_sql)
                if len(average_weight_result) > 0:
                    if (average_weight_result[0][0] != None):
                        average_weight.append(f"{float(average_weight_result[0][0]):.{2}f}")
                    else:
                        average_weight.append(f"{0.00:.{2}f}")
                if len(wastes_result) > 0:
                    if (wastes_result[0][0] != None):
                        wastes.append(f"{float(wastes_result[0][0]):.{0}f}")
                    else:
                        wastes.append(0)
                else:
                    wastes.append(0)

        self.wastes = tuple(wastes)
        self.average_weight = tuple(average_weight)
        sql_controller = self.SQLExecute(f"""
            SELECT [RFIDEquipment]
            FROM [MES_Iplast].[dbo].[RFIDEquipmentBinding]
            WHERE Equipment = '{self.tpa}'
            """)
        if len(sql_controller) > 0:
            self.controller = sql_controller[0][0]
        else:
            self.controller = 'Empty'