from iMES import app
from iMES import socketio
from flask_login import login_required
from iMES.functions.CheckRolesForInterface import CheckRolesForInterface
from iMES.Model.SQLManipulator import SQLManipulator
from iMES import current_tpa
from flask_login import current_user
from flask import request
import json


# Отображение окна оператора
@app.route('/operator')
@login_required
def operator():
    return CheckRolesForInterface('Оператор', 'operator/operator.html')


# Окно ввода веса изделия
@app.route('/operator/tableWeight')
@login_required
def tableWeight():
    ip_addr = request.remote_addr

    # Получаем данные о введенных за смену весов изделия
    sql_GetProductWeight = f"""SELECT Product.Name, ProductWeight.Weight, ProductWeight.CreateDate, Employee.LastName, Employee.FirstName, Employee.MiddleName
                                FROM ShiftTask INNER JOIN 
                                Shift ON ShiftTask.Shift = Shift.Oid AND Shift.StartDate <= GETDATE() AND Shift.EndDate >= GETDATE() INNER JOIN
                                Equipment ON ShiftTask.Equipment = Equipment.Oid AND Equipment.Oid = '{current_tpa[ip_addr][0]}' INNER JOIN 
                                Product ON ShiftTask.Product = Product.Oid INNER JOIN
                                ProductionData ON ShiftTask.Oid = ProductionData.ShiftTask INNER JOIN
                                ProductWeight ON ProductWeight.ProductionData = ProductionData.Oid INNER JOIN
								[User] ON ProductWeight.Creator = [User].Oid INNER JOIN
								Employee ON [User].Employee = Employee.Oid
                                ORDER BY CreateDate"""
    product_weight = SQLManipulator.SQLExecute(sql_GetProductWeight)

    # Проверяем был ли введен вес изделий в текущую смену
    # Если был, то записываем данные в кортежи в нужном формате для отображения на странице
    if product_weight:
        table_info = list()
        for product_weight_quantity in range(len(product_weight)):
            table_info.append([product_weight[product_weight_quantity][0], f'{product_weight[product_weight_quantity][1]:.3f}', str(
                                product_weight[product_weight_quantity][2].strftime('%d.%m.%Y %H:%M:%S')), 
                                f'{product_weight[product_weight_quantity][3]} {product_weight[product_weight_quantity][4]} {product_weight[product_weight_quantity][5]}'])
    # Если за смену вес никто не вводил, то формируем пустой массив
    else:
        table_info = list()

    # Получаем данные о текущем продукте и производственных данных
    sql_GetCurrentProduct = f"""SELECT Product.Name, ProductionData.Oid
                                        FROM ShiftTask INNER JOIN 
                                        Shift ON ShiftTask.Shift = Shift.Oid AND Shift.StartDate <= GETDATE() AND Shift.EndDate >= GETDATE() INNER JOIN
                                        Equipment ON ShiftTask.Equipment = Equipment.Oid AND Equipment.Oid = '{current_tpa[ip_addr][0]}' INNER JOIN
                                        Product ON ShiftTask.Product = Product.Oid INNER JOIN
                                        ProductionData ON ShiftTask.Oid = ProductionData.ShiftTask WHERE ProductionData.Status = 1"""
    current_product = SQLManipulator.SQLExecute(sql_GetCurrentProduct)

    return CheckRolesForInterface('Оператор', 'operator/tableWeight.html', [table_info, current_tpa[ip_addr], current_product])


# Кнопка ввода веса изделия во всплывающей клавиатуре была нажата
@socketio.on('product_weight_entering')
def handle_entered_product_weight(data):
    entered_weight = float(data[0])
    production_data = str(data[1])

    sql_GetCurrentUser = f"""SELECT [User].Oid FROM [User] WHERE [User].CardNumber = '{current_user.CardNumber}'"""
    current_User = SQLManipulator.SQLExecute(sql_GetCurrentUser)

    # Создаем запись введенного изделия в таблице ProductWeight
    sql_PostProductWeight = f"""INSERT INTO ProductWeight (Oid, ProductionData, Weight, CreateDate, Creator)
                                VALUES (NEWID(), '{production_data}', {entered_weight}, GETDATE(), '{current_User[0][0]}');"""
    SQLManipulator.SQLExecute(sql_PostProductWeight)


# Окно отходов и брака
@login_required
@app.route('/operator/tableWasteDefect')
def tableWasteDefect():
    ip_addr = request.remote_addr

    # Получаем данные о текущих отходах и браке
    sql_GetCurrentProductWaste = f"""SELECT ProductWaste.Material, Product.Name, ProductWaste.Type, ProductWaste.Count, ProductWaste.Weight,
                                        ProductWaste.Note, ProductWaste.CreateDate, Employee.LastName, Employee.FirstName, Employee.MiddleName
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
                                f'{current_product_waste[product_waste_quantity][4]:.3f}', current_product_waste[product_waste_quantity][5] if current_product_waste[product_waste_quantity][5] else '',
                                str(current_product_waste[product_waste_quantity][6].strftime('%d.%m.%Y %H:%M:%S')), 
                                f'{current_product_waste[product_waste_quantity][7]} {current_product_waste[product_waste_quantity][8]} {current_product_waste[product_waste_quantity][9]}'])
    # Если за смену вес никто не вводил, то формируем пустой массив
    else:
        waste_defect_info = list()

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
    ORDER BY Name"""
    all_wastes = SQLManipulator.SQLExecute(sql_GetAllWastes)

    return CheckRolesForInterface('Оператор', 'operator/tableWasteDefect/tableWasteDefect.html', [waste_defect_info, current_product, all_wastes])


# Кнопка ввода веса отходов во всплывающей клавиатуре была нажата
@socketio.on('product_wastes')
def handle_entered_product_wastes(data):
    production_data = str(data[0])
    material_oid = str(data[1])
    entered_waste_weight = float(data[2])

    sql_GetCurrentUser = f"""SELECT [User].Oid FROM [User] WHERE [User].CardNumber = '{current_user.CardNumber}'"""
    current_User = SQLManipulator.SQLExecute(sql_GetCurrentUser)

    # Создаем запись введенного отхода в таблице ProductWaste
    sql_PostProductWaste = f"""INSERT INTO ProductWaste (Oid, ProductionData, Material, Type, Weight, CreateDate, Creator)
                                VALUES (NEWID(), '{production_data}', '{material_oid}', 0, {entered_waste_weight}, GETDATE(), '{current_User[0][0]}');"""
    SQLManipulator.SQLExecute(sql_PostProductWaste)


# Кнопка ввода брака во всплывающей клавиатуре была нажата
@socketio.on('product_defect')
def handle_entered_product_wastes(data):
    production_data = str(data[0])
    entered_defect_weight = float(data[1])
    entered_defect_count = float(data[2])

    sql_GetCurrentUser = f"""SELECT [User].Oid FROM [User] WHERE [User].CardNumber = '{current_user.CardNumber}'"""
    current_User = SQLManipulator.SQLExecute(sql_GetCurrentUser)

    # Создаем запись введенного отхода в таблице ProductWaste
    sql_PostProductWaste = f"""INSERT INTO ProductWaste (Oid, ProductionData, Type, Weight, Count, CreateDate, Creator)
                                VALUES (NEWID(), '{production_data}', 1, {entered_defect_weight}, {entered_defect_count}, GETDATE(), '{current_User[0][0]}');"""
    SQLManipulator.SQLExecute(sql_PostProductWaste)


# Окно ввода отходов
# @login_required
# @app.route('/operator/tableWasteDefect/wastes')
# def wastes():
#     ip_addr = request.remote_addr

#     predefined_waste = ''

#     # Получаем данные о текущей ProductionData
#     sql_GetProductionData = f"""SELECT ProductionData.Oid
#                                 FROM ShiftTask INNER JOIN
#                                 Shift ON ShiftTask.Shift = Shift.Oid AND Shift.StartDate <= GETDATE() AND Shift.EndDate >= GETDATE() INNER JOIN
#                                 Equipment ON Equipment.Oid = ShiftTask.Equipment AND Equipment.Oid = '{current_tpa[ip_addr][0]}' INNER JOIN
#                                 ProductionData ON ProductionData.ShiftTask = ShiftTask.Oid"""

#     production_data = SQLManipulator.SQLExecute(sql_GetProductionData)

#     # current_type = '''Получаем тип отхода: 0 - отход, 1 - брак'''

#     # Создаем запись введенного отхода в таблице ProductWaste
#     sql_PostProductWeight = f"""INSERT INTO ProductWaste (Oid, ProductionData, Material, Type, Weight, Count, Downtime, Note, CreateDate, Creator)
#                                 VALUES (NEWID(), '', '', '', '{current_type}', '', '', '', '', GETDATE(), '{current_user[0][0]}');"""
#     SQLManipulator.SQLExecute(sql_PostProductWeight)

#     # Получаем данные о всех существующих отходах
#     sql_GetAllWastes = f"""SELECT Oid, Name  
#     FROM Material WHERE Type = 1
#     ORDER BY Name"""
#     all_wastes = SQLManipulator.SQLExecute(sql_GetAllWastes)

#     # Получаем данные о текущем продукте
#     sql_GetCurrentProduct = f"""SELECT DISTINCT Product.Oid, Product.Name, ProductionData.Oid
#                                 FROM ShiftTask INNER JOIN
#                                 Shift ON ShiftTask.Shift = Shift.Oid AND Shift.StartDate <= GETDATE() AND Shift.EndDate >= GETDATE() INNER JOIN
#                                 Product ON ShiftTask.Product = Product.Oid INNER JOIN
#                                 Equipment ON ShiftTask.Equipment = Equipment.Oid AND Equipment.Oid = '{current_tpa[ip_addr][0]}' INNER JOIN
#                                 ProductionData ON ShiftTask.Oid = ProductionData.ShiftTask WHERE ProductionData.Status = 1"""
#     current_product = SQLManipulator.SQLExecute(sql_GetCurrentProduct)
#     print(current_product)

#     return CheckRolesForInterface('Оператор', 'operator/tableWasteDefect/wastes.html', [predefined_waste, all_wastes, current_product])


# Отображение окна сменного задания
@app.route('/operator/ShiftTask')
@login_required
def OperatorShiftTask():
    return CheckRolesForInterface('Оператор', 'operator/ShiftTask.html')


# Изменение этикетки
@app.route('/operator/ChangeLabel')
@login_required
def OperatorChangeLabel():
    ip_addr = request.remote_addr
    
    # Получаем данные о текущих продуктах за смену и название смены
    sql_GetCurrentProduct = f"""SELECT DISTINCT Product.Oid, Product.Name
                                FROM ShiftTask INNER JOIN
                                Shift ON ShiftTask.Shift = Shift.Oid AND Shift.StartDate <= GETDATE() AND Shift.EndDate >= GETDATE() INNER JOIN
                                Product ON ShiftTask.Product = Product.Oid INNER JOIN
                                Equipment ON ShiftTask.Equipment = Equipment.Oid AND Equipment.Oid = '{current_tpa[ip_addr][0]}' INNER JOIN
                                ProductionData ON ShiftTask.Oid = ProductionData.ShiftTask"""
    current_product = SQLManipulator.SQLExecute(sql_GetCurrentProduct)

    # Получаем данные о текущей смене
    sql_GetCurrentShift = f"""SELECT Note FROM Shift WHERE Shift.StartDate <= GETDATE() AND Shift.EndDate >= GETDATE()"""
    current_shift = SQLManipulator.SQLExecute(sql_GetCurrentShift)

    return CheckRolesForInterface('Оператор', 'operator/changeLabel.html', [current_product, current_shift[0][0]])


# Кнопка сохранить на странице изменение этикетки была нажата
@socketio.on('sticker_info_change')
def handle_sticker_info_change(data):
    ip_addr = request.remote_addr  

    entered_product = str(data[0])
    entered_sticker_count = int(data[1])

    sql_GetCurrentUser = f"""SELECT [User].Oid FROM [User] WHERE [User].CardNumber = '{current_user.CardNumber}'"""
    current_User = SQLManipulator.SQLExecute(sql_GetCurrentUser)

    # Проверяем, существует ли запись текущей ТПА в таблице StickerInfo
    if SQLManipulator.SQLExecute(f"SELECT Equipment FROM StickerInfo WHERE Equipment = '{current_tpa[ip_addr][0]}'"):
        # Обновляем запись этикетки в таблице StickerInfo
        SQLManipulator.SQLExecute(f"""UPDATE StickerInfo
                                        SET Product = '{entered_product}', StickerCount = '{entered_sticker_count}'
                                        WHERE Equipment = '{current_tpa[ip_addr][0]}'""")
    else:
        # Создаем запись введенной этикетки в таблице StickerInfo
        SQLManipulator.SQLExecute(f"""INSERT INTO StickerInfo (Oid, Equipment, Product, StickerCount, CreateDate, Creator)
                                    VALUES (NEWID(), '{current_tpa[ip_addr][0]}', '{entered_product}', {entered_sticker_count}, GETDATE(), '{current_User[0][0]}');""")


# Схема упаковки
@app.route('/operator/PackingScheme')
@login_required
def OperatorPackingScheme():
    return CheckRolesForInterface('Оператор', 'operator/packingScheme.html')
