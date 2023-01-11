from iMES import app
from flask import request
from iMES import current_tpa
from iMES import socketio
from flask_login import login_required, current_user
from iMES.functions.CheckRolesForInterface import CheckRolesForInterface
from iMES.Model.SQLManipulator import SQLManipulator
from iMES import user_dict
import json

# Метод возвращает окно наладчика


@app.route('/adjuster')
@login_required
def adjuster():
    if current_user.id != None:
        user_dict[str(current_user.id)].interface = "Наладчик"
    return CheckRolesForInterface('Наладчик', 'adjuster/adjuster.html')

# Простои, неполадки и чеклисты


@app.route('/adjuster/journal')
@login_required
def adjusterJournal():
    ip_addr = request.remote_addr
    
    # Получение журнала простоев
    sql_GetDowntimeJournal = f""" SELECT [DF].[Oid],[DF].[Equipment],
                                        [DF].[StartDate],
                                        [DF].[EndDate],
                                    	[MCause].[Name] AS [Cause],
                                        [MDesc].[Name] AS [Description],
                                        [TM].[Name] AS [TakenMeasures],
                                    	[DF].[Note],[DF].[CreateDate],
                                        [UserName].[LastName],[UserName].[FirstName],[UserName].[MiddleName]
                                    FROM [MES_Iplast].[dbo].[DowntimeFailure] AS [DF]
                                    LEFT JOIN [MES_Iplast].[dbo].[MalfunctionCause] AS [MCause] ON [DF].[MalfunctionCause] = [MCause].[Oid]
                                    LEFT JOIN [MES_Iplast].[dbo].[MalfunctionDescription] AS [MDesc] ON [DF].[MalfunctionDescription] = [MDesc].[Oid]
                                    LEFT JOIN [MES_Iplast].[dbo].[TakenMeasures] AS [TM] ON [DF].[TakenMeasures] = [TM].[Oid]
                                    LEFT JOIN [MES_Iplast].[dbo].[User] AS [User] ON [DF].[Creator] = [User].[Oid]
                                    LEFT JOIN [MES_Iplast].[dbo].[Employee] AS [UserName] ON [User].[Employee] = [UserName].[Oid]
                                    WHERE [DF].[Equipment] = '{current_tpa[ip_addr][0]}'
                                    ORDER BY [StartDate] DESC """
    downtimeJournal = SQLManipulator.SQLExecute(sql_GetDowntimeJournal)
    
    return CheckRolesForInterface('Наладчик', 'adjuster/journal.html', downtimeJournal)

# Фиксация простоя


@app.route('/adjuster/journal/idleEnter')
@login_required
def adjusterIdleEnter():
    idleOid = request.args.getlist('oid')
    ip_addr = request.remote_addr
        
    # Получение данных о простое
    sql_GetDowntimeData = f"""  SELECT [Oid],[Equipment],[StartDate],[EndDate],[DowntimeType],
                                        [MalfunctionCause],[MalfunctionDescription],[TakenMeasures],
                                        [Note],[CreateDate],[Creator]
                                    FROM [MES_Iplast].[dbo].[DowntimeFailure]
                                    WHERE [Oid] = '{idleOid[0]}'
                                    ORDER BY [StartDate] DESC """
    downtimeData = SQLManipulator.SQLExecute(sql_GetDowntimeData)
    
    # Получение типа простоев
    sql_GetDowntimeType = f""" SELECT [Oid],[Name],[Status],[SyncId]
                                FROM [MES_Iplast].[dbo].[DowntimeType]
                                WHERE [Status] = '1' 
                                ORDER BY [Name] """
    downtimeType = SQLManipulator.SQLExecute(sql_GetDowntimeType)
    
    # Получение справочника причин неисправности
    sql_GetMalfunctionCause = f""" SELECT [Oid],[Name],[Status]
                                    FROM [MES_Iplast].[dbo].[MalfunctionCause]
                                    ORDER BY [Name] """
    malfunctionCause = SQLManipulator.SQLExecute(sql_GetMalfunctionCause)

    # Получение справочника описаний неисправности
    sql_GetMalfunctionDescription = f""" SELECT [Oid],[Name],[Status]
                                            FROM [MES_Iplast].[dbo].[MalfunctionDescription]
                                            ORDER BY [Name] """
    malfunctionDescription = SQLManipulator.SQLExecute(sql_GetMalfunctionDescription)
                                            
    # Получение справочника предпринятых мер
    sql_GetTakenMeasures = f""" SELECT [Oid],[Name],[Status]
                                FROM [MES_Iplast].[dbo].[TakenMeasures]
                                ORDER BY [Name] """
    takenMeasures = SQLManipulator.SQLExecute(sql_GetTakenMeasures)
    
    # Получаем данные о текущем продукте и производственных данных
    sql_GetCurrentProduct = f"""SELECT DISTINCT ProductionData.Oid, Product.Name 
                                FROM ShiftTask INNER JOIN
                                Shift ON ShiftTask.Shift = Shift.Oid AND Shift.StartDate <= GETDATE() AND Shift.EndDate >= GETDATE() INNER JOIN
                                Product ON ShiftTask.Product = Product.Oid INNER JOIN
                                Equipment ON ShiftTask.Equipment = Equipment.Oid AND Equipment.Oid = '{current_tpa[ip_addr][0]}' INNER JOIN
                                ProductionData ON ShiftTask.Oid = ProductionData.ShiftTask WHERE ProductionData.Status = 1"""
    current_product = SQLManipulator.SQLExecute(sql_GetCurrentProduct)

    # Получаем данные о всех существующих отходах
    sql_GetAllWastes = f"""SELECT Oid, Name  
                            FROM Material WHERE Type = 1
                            ORDER BY [Name] """
    all_wastes = SQLManipulator.SQLExecute(sql_GetAllWastes)
    
    # Получаем уже введенные отходы
    sql_GetExistingWastes = f""" SELECT [ProductWaste].[Oid], [Material].[Name], [ProductWaste].[Weight], [ProductWaste].[CreateDate]
                                        FROM [ShiftTask]
                                        INNER JOIN [Shift] ON [ShiftTask].[Shift] = [Shift].[Oid]
                                            AND [Shift].[StartDate] <= GETDATE()
                                            AND [Shift].[EndDate] >= GETDATE()
                                        INNER JOIN [Equipment] ON [ShiftTask].[Equipment] = [Equipment].[Oid]
                                            AND [Equipment].[Oid] = '{current_tpa[ip_addr][0]}'
                                        INNER JOIN [Product] ON [ShiftTask].[Product] = [Product].[Oid]
                                        INNER JOIN [ProductionData] ON [ShiftTask].[Oid] = [ProductionData].[ShiftTask]
                                        INNER JOIN [ProductWaste] ON [ProductionData].[Oid] = [ProductWaste].[ProductionData]
                                        INNER JOIN [Material] ON [ProductWaste].[Material] = [Material].[Oid]
                                        WHERE [ProductWaste].[Type] = 0
                                        AND [ProductWaste].[Downtime] IS NULL"""
    existing_wastes = SQLManipulator.SQLExecute(sql_GetExistingWastes)
    
    # Получаем уже введенный брак
    sql_GetExistingDefect = f""" SELECT [ProductWaste].[Oid], [Product].[Name], [ProductWaste].[Weight], [ProductWaste].[Count], [ProductWaste].[CreateDate]
                                        FROM [ShiftTask]
                                        INNER JOIN [Shift] ON [ShiftTask].[Shift] = [Shift].[Oid]
                                            AND [Shift].[StartDate] <= GETDATE()
                                            AND [Shift].[EndDate] >= GETDATE()
                                        INNER JOIN [Equipment] ON [ShiftTask].[Equipment] = [Equipment].[Oid]
                                            AND [Equipment].[Oid] = '{current_tpa[ip_addr][0]}'
                                        INNER JOIN [Product] ON [ShiftTask].[Product] = [Product].[Oid]
                                        INNER JOIN [ProductionData] ON [ShiftTask].[Oid] = [ProductionData].[ShiftTask]
                                        INNER JOIN [ProductWaste] ON [ProductionData].[Oid] = [ProductWaste].[ProductionData]
                                        WHERE [ProductWaste].[Type] = 1
                                        AND [ProductWaste].[Downtime] IS NULL """
    existing_defect = SQLManipulator.SQLExecute(sql_GetExistingDefect)
    
    return CheckRolesForInterface('Наладчик', 'adjuster/idles/idleEnter.html', [downtimeData, downtimeType, malfunctionCause, malfunctionDescription, takenMeasures, all_wastes, existing_wastes, current_product, existing_defect])


# Ввод данных о фиксации простоя в БД
@socketio.on('idleEnterFixing')
def idleEnterFixing(data):
    ip_addr = request.remote_addr
    # Добавление новой записи в DowntimeFailure (зафиксированный простой)
    SQLManipulator.SQLExecute(f""" UPDATE [MES_Iplast].[dbo].[DowntimeFailure]
                                    SET [DowntimeType] = '{data['idleType']}',
                                        [MalfunctionCause] = '{data['idleCause']}',
                                        [MalfunctionDescription] = '{data['idleDescription']}',
                                        [TakenMeasures] = '{data['idleTakenMeasures']}',
                                        [Note] = '{data['idleNote']}',
                                        [CreateDate] = GETDATE(),
                                        [Creator] = '{data['creatorOid']}'
                                    WHERE [Oid] = '{data['idleOid']}' """)
    
    # Добавление нового отхода и привязки к простою
    idle_key_list = list(data.keys())
    if 'newWaste' in idle_key_list:
        if len(data['newWaste']) != 0:  
            for i in range(len(data['newWaste'])):
                newWaste = data['newWaste'][i][0].split(',')
                print(newWaste)
                SQLManipulator.SQLExecute(f""" INSERT INTO [MES_Iplast].[dbo].[ProductWaste]
                                                    ([ProductionData],[Material],[Type],[Weight],
                                                    [Downtime],[CreateDate],[Creator])
                                                VALUES 
                                                    ('{newWaste[0]}', '{newWaste[1]}', 0, '{newWaste[2]}',
                                                    '{data['idleOid']}', GETDATE(), '{data['creatorOid']}') """)
    
    # Добавление нового брака и привязки к простою
    if 'newDefect' in idle_key_list:        
        if len(data['newDefect']) != 0:  
            for i in range(len(data['newDefect'])):
                newDefect = data['newDefect'][i].split(',')
                print(newDefect)
                SQLManipulator.SQLExecute(f""" INSERT INTO [MES_Iplast].[dbo].[ProductWaste]
                                                    ([ProductionData],[Type],[Weight],[Count],
                                                    [Downtime],[CreateDate],[Creator])
                                                VALUES 
                                                    ('{newDefect[0]}', 1, '{newDefect[1]}', '{newDefect[2]}',
                                                    '{data['idleOid']}', GETDATE(), '{data['creatorOid']}') """)

    # Привязку существующего отхода к простою
    if 'existingWaste' in idle_key_list:
        if len(data['existingWaste']) != 0:
            for i in range(len(data['existingWaste'])):
                print(data['existingWaste'][i])
                print(data['idleOid'])
                SQLManipulator.SQLExecute(f""" UPDATE [MES_Iplast].[dbo].[ProductWaste]   
                                                SET [Downtime] = '{data['idleOid']}'
                                                WHERE [Oid] = '{data['existingWaste'][i]}' """)
        
    # Привязку существующего брака к простою
    if 'existingDefect' in idle_key_list:
        if len(data['existingDefect']) != 0:
            for i in range(len(data['existingDefect'])):
                print(data['existingDefect'][i])
                print(data['idleOid'])
                SQLManipulator.SQLExecute(f""" UPDATE [MES_Iplast].[dbo].[ProductWaste]
                                                SET [Downtime] = '{data['idleOid']}'
                                                WHERE [Oid] = '{data['existingDefect'][i]}' """)
    
    socketio.emit("IdleEntered", data=json.dumps({ip_addr: ''}),ensure_ascii=False, indent=4)

@app.route('/adjuster/journal/idleView')
@login_required
def adjusterIdleView():
    idleOid = request.args.getlist('oid')
    
    sql_GetIdleData = f""" SELECT   [DF].[Oid],[DF].[StartDate], [DF].[EndDate], [Type].[Name],
                                    [Cause].[Name] AS [Cause], [Desc].[Name] AS [Desc], [TakenMeasures].[Name], [Note],                             
                                    [Employee].[FirstName],[Employee].[LastName],[Employee].[MiddleName]
                            FROM [MES_Iplast].[dbo].[DowntimeFailure] AS [DF]
                            LEFT JOIN [MES_Iplast].[dbo].[DowntimeType] AS [Type] ON [DF].[DowntimeType] = [Type].[Oid]
                            LEFT JOIN [MES_Iplast].[dbo].[MalfunctionCause] AS [Cause] ON [DF].[MalfunctionCause] = [Cause].[Oid]
                            LEFT JOIN [MES_Iplast].[dbo].[MalfunctionDescription] AS [Desc] ON [DF].[MalfunctionDescription] = [Desc].[Oid]
                            LEFT JOIN [MES_Iplast].[dbo].[TakenMeasures] AS [TakenMeasures] ON [DF].[TakenMeasures] = [TakenMeasures].[Oid]
                            LEFT JOIN [MES_Iplast].[dbo].[User] AS [User] ON [DF].[Creator] = [User].[Oid]
                            LEFT JOIN [MES_Iplast].[dbo].[Employee] AS [Employee] ON [User].[Employee] = [Employee].[Oid]
                            WHERE [DF].[Oid] = '{idleOid[0]}' """
    idleData = SQLManipulator.SQLExecute(sql_GetIdleData)
    
    return CheckRolesForInterface('Наладчик', 'adjuster/idles/idleView.html', idleData)

# Сырье до конца выпуска
@app.route('/adjuster/RawMaterials')
@login_required
def adjusterRawMaterials():
    ip_addr = request.remote_addr

    with open('st.json', 'r', encoding='utf-8-sig') as f:
        text = json.load(f)
    
    product_residues = 0

    # Находим разницу по плану и факту выпуска
    for i in range(len(current_tpa[ip_addr][2].specifications)):
        product_residues += current_tpa[ip_addr][2].production_plan[i] - current_tpa[ip_addr][2].product_fact[i]

    raw_materials = []
    total_weight = 0
    product_names = []

    # Находим сумму всех масс компонент
    for product in text[0]['Spec']:
        extra_characteristic = []

        if product['SpecCode'] in current_tpa[ip_addr][2].specifications:
            for product_component in product['ExtraCharacteristic']:
                mass_quantity = (float(product_component['Count'].replace(',', '.')) * product_residues) / int(product['UseFactor'].replace("\xa0", ""))
                total_weight += mass_quantity
                
                extra_characteristic.append({'ProductName': product_component['Name'], 'ProductMass': round(mass_quantity, 2)})
                
            raw_materials.append(extra_characteristic)

    # Высчитываем процент массы каждого компонента продукта
    for product in raw_materials:
        for product_component in product:
            mass_percent = (product_component['ProductMass'] * 100) / total_weight
            product_component['ProductPercent'] = round(mass_percent, 2)
    

    return CheckRolesForInterface('Наладчик', 'adjuster/rawMaterials.html', [product_residues, raw_materials])


# Фиксация отхода и брака
@app.route('/adjuster/WasteDefectFix')
@login_required
def adjusterWasteDefectFix():
    ip_addr = request.remote_addr

    # Получаем данные о текущих отходах и браке
    sql_GetCurrentProductWaste = f"""SELECT ProductWaste.Material, Product.Name, ProductWaste.Type, ProductWaste.Count, ProductWaste.Weight,
                                        ProductWaste.Note, ProductWaste.CreateDate, Employee.LastName, Employee.FirstName, Employee.MiddleName, ProductWaste.Oid
                                        FROM ShiftTask INNER JOIN
                                        Shift ON ShiftTask.Shift = Shift.Oid AND Shift.StartDate <= GETDATE() AND Shift.EndDate >= GETDATE() INNER JOIN
                                        Equipment ON ShiftTask.Equipment = Equipment.Oid AND Equipment.Oid = '{current_tpa[ip_addr][0]}' INNER JOIN
                                        Product ON ShiftTask.Product = Product.Oid INNER JOIN
                                        ProductionData ON ShiftTask.Oid = ProductionData.ShiftTask INNER JOIN
                                        ProductWaste ON ProductionData.Oid = ProductWaste.ProductionData INNER JOIN
                                        [User] ON ProductWaste.Creator = [User].Oid INNER JOIN
                                        Employee ON [User].Employee = Employee.Oid"""
    current_product_waste = SQLManipulator.SQLExecute(sql_GetCurrentProductWaste)

    # Проверяем были ли введены отходы и/или брак в текущую смену
    # Если был, то записываем данные в кортежи в нужном формате для отображения на странице
    if current_product_waste:
        waste_defect_info = list()

        for product_waste_quantity in range(len(current_product_waste)):

            if current_product_waste[product_waste_quantity][0] != None or current_product_waste[product_waste_quantity][2] == 0:
                sql_GetCurrentMaterial  = f"""SELECT Name FROM Material WHERE Material.Oid = '{current_product_waste[product_waste_quantity][0]}'"""
                current_material = SQLManipulator.SQLExecute(sql_GetCurrentMaterial)
                
            else:
                current_material = [['']]


            waste_defect_info.append([current_product_waste[product_waste_quantity][1], 
                                        current_product_waste[product_waste_quantity][2],
                                        current_material[0][0], 
                                        f'{current_product_waste[product_waste_quantity][3]:.0f}' if current_product_waste[product_waste_quantity][3] else '', 
                                        f'{current_product_waste[product_waste_quantity][4]:.3f}', 
                                        str(current_product_waste[product_waste_quantity][6].strftime('%d.%m.%Y %H:%M:%S')), 
                                        f'{current_product_waste[product_waste_quantity][7]} {current_product_waste[product_waste_quantity][8]} {current_product_waste[product_waste_quantity][9]}',
                                        current_product_waste[product_waste_quantity][5] if current_product_waste[product_waste_quantity][5] else '', 
                                        current_product_waste[product_waste_quantity][10]])
    # Если за смену вес никто не вводил, то формируем пустой массив
    else:
        waste_defect_info = list()

    return CheckRolesForInterface('Наладчик', 'adjuster/wasteDefectFix.html', [waste_defect_info])


# Кнопка "Указать причину" на странице "Зафиксировать брак и отход" была нажата
@socketio.on('waste_note_change')
def handle_waste_note_change(data):
    selected_waste_oid = str(data[0])
    entered_waste_note = str(data[1])

    # Обновляем запись отхода или брака в таблице ProductWaste
    SQLManipulator.SQLExecute(f"""UPDATE ProductWaste
                                    SET Note = '{entered_waste_note}'
                                    WHERE Oid = '{selected_waste_oid}'""")


# Сменное задание
@app.route('/adjuster/shiftTask')
@login_required
def adjusterShiftTask():
    return CheckRolesForInterface('Наладчик', 'adjuster/ShiftTask.html')

# Фиксация изменений в тех. системе


@app.route('/adjuster/techSystem')
@login_required
def adjusterTechSystem():
    return CheckRolesForInterface('Наладчик', 'adjuster/techSystem.html')

# Ввод изменений в тех. системе


@app.route('/adjuster/techSystemEnter')
@login_required
def adjusterTechSystemEnter():
    return CheckRolesForInterface('Наладчик', 'adjuster/techSystemEnter.html')
