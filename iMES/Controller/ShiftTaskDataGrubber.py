from iMES.Model.BaseObjectModel import BaseObjectModel


class ShiftTaskDataGrubber(BaseObjectModel):
    """
        Класс отвечающий за хранение данных по выполняемому на данный момент
        сменному задания на определённом ТПА
    """
    def __init__(self,_app) -> None:
        BaseObjectModel.__init__(self,_app)
        self.tpa = ''
        self.pressform = self.update_pressform()
        self.production_plan = (0,)
        self.cycle = 0
        self.cycle_fact = 0
        self.plan_weight = (0,)
        self.average_weight = (0,)
        self.shift = ''
        self.shift_oid = ''
        self.shift_task_oid = ''
        self.product_fact = (0,)
        self.label = ''
        self.controller = 'Empty'
        self.PackingURL = ''
        self.StartDate = None
        self.EndDate = None
        self.ProductCount = 0
        self.wastes = (0,)
        self.shift_tasks_traits = ()
        self.specifications = []
        self.traits = ()
        self.product = ()
        self.product_oids = ()
        self.pressform_oid = ""
        self.defectives = ()

    def update_pressform(self):
        # Проверка прессформы
        sql = f"""
            SELECT TOP (1) Equipment.Name, RFIDClosureData.Date, Equipment.Oid
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
                pressform = 'Метка не привязана к прессформе'
            else:
                pressform = pf[0][0]
                self.pressform_oid = pf[0][2]
        else:
            pressform = 'Не определена'
            self.pressform_oid = ""
        return pressform
    

    # Метод получения данных из сменного задания
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
                ,[Product]
                ,[Shift].Oid
            FROM [MES_Iplast].[dbo].[ShiftTask], Product, Shift WHERE 
            [ShiftTask].Equipment = '{self.tpa}' AND
            Shift.Oid = (SELECT TOP(1) Oid FROM Shift ORDER BY StartDate DESC ) AND
            ShiftTask.Product = Product.Oid AND EXISTS
            (SELECT * FROM ProductionData WHERE ProductionData.ShiftTask = ShiftTask.Oid AND Status = 1)
        """
        data = self.SQLExecute(sql)
        #---------------------------------------------------
        # Простая передача из БД в поля класса
        if len(data) > 0:
            st_oid = []
            product_list = []
            production_plan = []
            plan_weight = []
            traits = []
            specs = []
            traits_operator = []
            product_oids = []
            for shift_task in data:
                st_oid.append(shift_task[0])
                product_list.append(shift_task[4])
                production_plan.append(shift_task[11])
                plan_weight.append(f"{float(shift_task[13]):.{2}f}")
                traits_operator.append(shift_task[6])
                product_oids.append(shift_task[18])
                self.cycle = shift_task[12]
                self.shift = shift_task[1]
                self.PackingURL = shift_task[15]
                self.shift_oid = shift_task[19]
                spec_code = self.SQLExecute(f"""
                    SELECT [Code]
                        FROM [MES_Iplast].[dbo].[ProductSpecification]
                        WHERE Oid = '{shift_task[5]}'
                """)
                if len(spec_code) > 0:
                    specs.append((spec_code[0][0])[2:])

            self.specifications = specs            
            self.shift_task_oid = st_oid
            self.product = tuple(product_list)
            self.production_plan = tuple(production_plan)
            self.plan_weight = tuple(plan_weight)
            self.traits = tuple(traits_operator)
            self.product_oids = tuple(product_oids)

            for i in range(0,len(data)):
                traits.append([self.product[i],
                               f"{data[i][16]} {data[i][17]}",
                               self.production_plan[i],
                               self.cycle,
                               self.plan_weight[i]])
            self.shift_tasks_traits = tuple(traits)
        else:
            self.shift_task_oid = ()
            self.product = 'Нет сменного задания'
            self.production_plan = 0
            self.cycle = 0
            self.plan_weight = 0
            get_shift_data = self.SQLExecute("""
            SELECT TOP (1) Oid,[Note]
            FROM [MES_Iplast].[dbo].[Shift] ORDER BY StartDate DESC            
            """)
            self.shift = get_shift_data[0][1]
            self.shift_oid = get_shift_data[0][0]

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
                    FROM [MES_Iplast].[dbo].[ProductionData] WHERE ShiftTask = '{task_oid} AND Status = 1'
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
        defectives = []
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
                    SELECT SUM([Weight])
                    FROM [MES_Iplast].[dbo].[ProductWaste] WHERE ProductionData = '{production_data_oid}'
                    AND Type = 0
                """
                defectives_sql = f"""
                    SELECT SUM([Count])
                    FROM [MES_Iplast].[dbo].[ProductWaste] WHERE ProductionData = '{production_data_oid}'
                    AND Type = 1
                """
                average_weight_result = self.SQLExecute(average_weight_sql)
                wastes_result = self.SQLExecute(wastes_sql)
                defectives_result = self.SQLExecute(defectives_sql)
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
                
                if len(defectives_result) > 0:
                    defectives.append(int(defectives_result[0][0]))
                else:
                    defectives.append(0)

        self.wastes = tuple(wastes)
        self.average_weight = tuple(average_weight)
        self.defectives = tuple(defectives)
        sql_controller = self.SQLExecute(f"""
            SELECT [RFIDEquipment]
            FROM [MES_Iplast].[dbo].[RFIDEquipmentBinding]
            WHERE Equipment = '{self.tpa}'
            """)
        if len(sql_controller) > 0:
            self.controller = sql_controller[0][0]
        else:
            self.controller = 'Empty'