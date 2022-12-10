from iMES import app
from flask import request
from iMES import current_tpa
from iMES import socketio
from flask_login import login_required, current_user
from iMES.functions.CheckRolesForInterface import CheckRolesForInterface
from iMES.Model.SQLManipulator import SQLManipulator
from iMES import user_dict

# Метод возвращает окно наладчика


@app.route('/adjuster')
@login_required
def adjuster():
    user_dict[str(current_user.id)].interface = "Наладчик"
    return CheckRolesForInterface('Наладчик', 'adjuster/adjuster.html')

# Простои, неполадки и чеклисты


@app.route('/adjuster/journal')
@login_required
def adjusterJournal():
    ip_addr = request.remote_addr
    
    # Получение журнала простоев (не зафиксированных/системных)
    sql_GetDowntimeJournal = f""" SELECT [Oid],[Equipment],[StartDate],[EndDate],[Status]
                                    FROM [MES_Iplast].[dbo].[DowntimeJournal]
                                    WHERE [Equipment] = '{current_tpa[ip_addr][0]}'
                                    AND [Status] = 0
                                    ORDER BY [StartDate] DESC """
    downtimeJournal = SQLManipulator.SQLExecute(sql_GetDowntimeJournal)
    
    # Получение журнала зафиксированных простоев
    sql_GetFixedDowntimeJournal = f""" SELECT [Oid],[Equipment],[StartDate],[EndDate],[DowntimeType],[MalfunctionCause],
                                                [MalfunctionDescription],[TakenMeasures],[Note],[CreateDate],[Creator]
                                                FROM [MES_Iplast].[dbo].[DowntimeFailure]
                                                WHERE [Equipment] = '{current_tpa[ip_addr][0]}'
                                                ORDER BY [StartDate] DESC"""
    fixedDowntimeJournal = SQLManipulator.SQLExecute(sql_GetFixedDowntimeJournal)
    
    return CheckRolesForInterface('Наладчик', 'adjuster/journal.html', [ downtimeJournal, fixedDowntimeJournal ])

# Фиксация простоя


@app.route('/adjuster/journal/idleEnter')
@login_required
def adjusterIdleEnter():
    idleOid = request.args.getlist('oid')
    ip_addr = request.remote_addr
        
    # Получение данных о простое
    sql_GetDowntimeData = f""" SELECT [Oid],[Equipment],[StartDate],[EndDate],[Status]
                                    FROM [MES_Iplast].[dbo].[DowntimeJournal]
                                    WHERE [Oid] = '{idleOid[0]}'
                                    AND [Status] = 0 """
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
                                        WHERE [ProductWaste].[Type] = 0 """
    existing_wastes = SQLManipulator.SQLExecute(sql_GetExistingWastes)
    
    return CheckRolesForInterface('Наладчик', 'adjuster/idles/idleEnter.html', [downtimeData, downtimeType, malfunctionCause, malfunctionDescription, takenMeasures, all_wastes, existing_wastes, current_product])


# Сырье до конца выпуска
@app.route('/adjuster/RawMaterials')
@login_required
def adjusterRawMaterials():
    return CheckRolesForInterface('Наладчик', 'adjuster/rawMaterials.html')


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


            waste_defect_info.append([current_product_waste[product_waste_quantity][1], current_product_waste[product_waste_quantity][2],
                                current_material[0][0], f'{current_product_waste[product_waste_quantity][3]:.0f}' if current_product_waste[product_waste_quantity][3] else '', 
                                f'{current_product_waste[product_waste_quantity][4]:.3f}', str(current_product_waste[product_waste_quantity][6].strftime('%d.%m.%Y %H:%M:%S')), 
                                f'{current_product_waste[product_waste_quantity][7]} {current_product_waste[product_waste_quantity][8]} {current_product_waste[product_waste_quantity][9]}',
                                current_product_waste[product_waste_quantity][5] if current_product_waste[product_waste_quantity][5] else '', current_product_waste[product_waste_quantity][10]])
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
