from iMES.Model.SQLManipulator import SQLManipulator

class ModelView():
        
    def GetAllTPA (self, request):
        allTPA = [] # Временный список всех ТПА
        deviceTPAList = [] # Временный ТПА привязанных конкретному терминалу
        TPAList = {} # Главный список ТПА
        
        ip_addr = request.remote_addr  # Получение IP-адресса пользователя
        
        # Получение полного списка ТПА
        cursor =SQLManipulator.SQLReturnCursor(f''' SELECT [RFIDBind].[RFIDEquipment], [RFIDBind].[Equipment], [Equipment].[Name]
                                                    FROM [MES_Iplast].[dbo].[RFIDEquipmentBinding] AS [RFIDBind]
                                                    LEFT JOIN  [MES_Iplast].[dbo].[Equipment] AS [Equipment] ON [RFIDBind].[Equipment] = [Equipment].[Oid]
                                                    WHERE [Equipment].[EquipmentType] = 'CC019258-D8D7-4286-B2CD-706FA0A2DC9D' ''')
        columns = [column[0] for column in cursor.description]
        for row in cursor.fetchall():
            allTPA.append(dict(zip(columns, row)))

        cursor = SQLManipulator.SQLReturnCursor(f''' SELECT [RFIDBind].[RFIDEquipment], [RFIDBind].[Equipment], [Equipment].[Name]
                                                    FROM [MES_Iplast].[dbo].[RFIDEquipmentBinding] AS [RFIDBind]
                                                    LEFT JOIN [MES_Iplast].[dbo].[Device] AS [Device] ON [Device].[DeviceId] = '{ip_addr}'
                                                    LEFT JOIN [MES_Iplast].[dbo].[Relation_DeviceEquipment] AS [DeviceEquipment] ON [DeviceEquipment].[Device] = [Device].[Oid]
                                                    LEFT JOIN  [MES_Iplast].[dbo].[Equipment] AS [Equipment] ON [RFIDBind].[Equipment] = [Equipment].[Oid] AND [Equipment].[Oid] = [DeviceEquipment].[Equipment]
                                                    WHERE [Equipment].[EquipmentType] = 'CC019258-D8D7-4286-B2CD-706FA0A2DC9D' ''')
        columns = [column[0] for column in cursor.description]
        for row in cursor.fetchall():
            deviceTPAList.append(dict(zip(columns, row)))
                
        # Формирование списка с ID ключами ТПА
        for tpa in allTPA:
            for i in range(0, len(deviceTPAList)):
                if tpa['Equipment'] == deviceTPAList[i]['Equipment']:
                    tpa['Binding'] = 1
                    TPAList[tpa['Equipment']] = tpa
                elif 'Binding' not in tpa:
                    tpa['Binding'] = 0
                    TPAList[tpa['Equipment']] = tpa
        
        return TPAList
    
    # def GetTpaPressform(self, request, tpaIndex):
    #     connection = pyodbc.connect(сonnectionsStrings['EAM_Iplast'])
    #     connections['EAM_Iplast'] = connection.cursor()
        
    #     tpaPressForm = '' # Список пресс-форм привязанных к ТПА
        
    #     # Получение списка пресс-форм привязанных к ТПА
    #     connections['EAM_Iplast'].execute(f'''  SELECT TOP(1) [OBR].[Наименование]
	#                                             FROM [EAM_test].[dbo].[RFIDReader] AS [RFR]
	#                                             LEFT JOIN [EAM_test].[dbo].[RFIDData] AS [RFD] ON [RFD].[Reader] = [RFR].[Oid]
	#                                             LEFT JOIN [EAM_test].[dbo].[RFIDLabel] AS [RFL] ON [RFL].[Oid] = [RFD].[Label]
	#                                             LEFT JOIN [EAM_Iplast].[dbo].[ОбъектРемонта] AS [OBR] ON [RFL].[Asset] = [OBR].[Oid]
	#                                             WHERE [RFR].[Asset] = '{tpaIndex}' AND
	#                                             	  [RFR].[Active] = '1'
	#                                             ORDER BY [RFD].[Date] DESC ''')
    #     pressFormList = connections['EAM_Iplast'].fetchall()
        
    #     connection.commit()
        
    #     if pressFormList[0][0] != None:
    #         tpaPressForm = pressFormList[0][0]
    #     else:
    #         tpaPressForm = ''
  
    #     return tpaPressForm
    
    # # Получение сменного задания и ID продукта
    # def GetShiftTaskData(self, request, tpaIndex):
    #     connection = pyodbc.connect(сonnectionsStrings['EAM_Iplast'])
    #     connections['EAM_Iplast'] = connection.cursor()
        
    #     shiftTaskData = [] 
    #     productID = []

    #     connections['EAM_Iplast'].execute(f''' DECLARE @now datetime,  @morning datetime, @taskdate datetime, @night datetime
    #                                             , @shifttype int ;
                                        
    #                                             SET @now = GETDATE();
    #                                             SET @morning = DATEADD( hour, 7, DATEDIFF( dd, 0, @now ) );
    #                                             SET @night = DATEADD( hour, 19, DATEDIFF( dd, 0, @now ) );
                                        
    #                                             IF @now >= @morning AND @now < @night
    #                                                 SET @shifttype = 0;
    #                                             ELSE 
    #                                                 SET @shifttype = 1;
                                        
    #                                             IF @now >= @morning
    #                                                 SET @taskdate = CAST( @now AS date );
    #                                             ELSE 
    #                                                 SET @taskdate = DATEADD(DAY, -1, CAST( @now AS date ));
                                                    
    #                                             SELECT STD.[Oid], 
    #                                                 STD.[RepairObject], 
    #                                                 OBR.[Наименование],
    #                                                 STD.[ProductionStart], 
    #                                                 STD.[ProductionEnd], 
    #                                                 STD.[SocketsCount],
    #                                                 STD.[OrdinalNumber]
    #                                             FROM [EAM_test].[dbo].[MESShiftTask] AS ST
    #                                             LEFT JOIN [EAM_test].[dbo].[MESShiftTaskData] AS STD ON STD.[ShiftTask] = ST.[Oid]
    #                                             LEFT JOIN [EAM_Iplast].[dbo].[ОбъектРемонта]  AS [OBR] ON STD.[RepairObject] = OBR.[Oid]
    #                                             WHERE ST.[TaskDate] = @taskdate 
    #                                             AND ST.[ShiftType] = @shifttype
    #                                             AND STD.[TaskStatus] IS NOT NULL
    #                                             AND RepairObject = '{tpaIndex}' ''')
    #     shiftTask = connections['EAM_Iplast'].fetchall()
        
    #     connection.commit()
        
    #     if not shiftTask:
    #         shiftTask = 'None'
    #         shiftTaskData.append(shiftTask)
    #         productID.append(shiftTask)
    #     else:
    #         shiftTaskData.append(shiftTask)
    #         productID.append(shiftTask[0])
            
    #     return productID

    # # Получение данных о продукте (план, цикл, вес и тд.)
    # def GetProduct(self, request, tpaIndex):
    #     connection = pyodbc.connect(сonnectionsStrings['EAM_Iplast'])
    #     connections['EAM_Iplast'] = connection.cursor()
        
    #     productID = self.GetShiftTaskData(request,tpaIndex)
    #     productList = {}
    #     columns = []

    #     for id in productID:
    #         if id != 'None':
    #             cursor = connections['EAM_Iplast'].execute(f''' SELECT TOP(1) [ShiftTask],[NomenclatureGroup],[RepairObject],[OrdinalNumber],[Product],[Name],
    #                                                                 [Article],[Specification],[SocketsCount],[CycleNorm],[CycleFact],[WeightNorm],[WeightFact],
    #                                                                 [ProductionPlan],[ProductionFact],[Traits],[ExtraTraits],[Ingredients],[Packing],[PackingCount],
    #                                                                 [NomenclatureURL],[PackingURL],[ProductivityURL],[TaskStatus],[CreateDate],[ProductionStart],
    #                                                                 [ProductionEnd],[Flags]
    #                                                             FROM [EAM_test].[dbo].[MESShiftTaskData] AS STD
    #                                                             LEFT JOIN [EAM_test].[dbo].[MESProduct1C]  AS P1C ON STD.[Product] = P1C.[Oid]
    #                                                             WHERE STD.[Oid] = '{id[0]}'
    #                                                             ORDER BY ProductionStart DESC ''')
    #             columns = [column[0] for column in cursor.description]
    #             for row in cursor.fetchall():
    #                 productList = (dict(zip(columns, row)))
    #         else:
    #             productList = (dict(zip(columns, '')))
        
    #     connection.commit()
                
    #     return productList