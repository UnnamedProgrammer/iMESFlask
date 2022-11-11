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
            print(1)
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
    sql_GetCurrentProductWaste = f"""SELECT Product.Name, ProductWaste.Type, Material.Name, ProductWaste.Count, ProductWaste.Weight,
                                        ProductWaste.Note, ProductWaste.CreateDate, ProductWaste.Creator
                                        FROM ShiftTask INNER JOIN
                                        Shift ON ShiftTask.Shift = Shift.Oid AND Shift.StartDate <= GETDATE() AND Shift.EndDate >= GETDATE() INNER JOIN
                                        Equipment ON ShiftTask.Equipment = Equipment.Oid AND Equipment.Oid = '{current_tpa[ip_addr][0]}' INNER JOIN
                                        Product ON ShiftTask.Product = Product.Oid INNER JOIN
                                        ProductionData ON ShiftTask.Oid = ProductionData.ShiftTask INNER JOIN
                                        ProductWaste ON ProductionData.Oid = ProductWaste.ProductionData INNER JOIN
                                        Material ON ProductWaste.Material = Material.Oid"""
    current_product_waste = SQLManipulator.SQLExecute(sql_GetCurrentProductWaste)

    # Получаем данные о текущем продукте и производственных данных
    sql_GetCurrentProduct = f"""SELECT DISTINCT Product.Oid, Product.Name, ProductionData.Oid
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

    return CheckRolesForInterface('Оператор', 'operator/tableWasteDefect/tableWasteDefect.html', [current_product_waste, current_product, all_wastes])


# # Кнопка ввода веса изделия во всплывающей клавиатуре была нажата
# @socketio.on('product_wastes')
# def handle_entered_product_wastes(data):
#     entered_weight = float(data[0])
#     production_data = str(data[1])

#     sql_GetCurrentUser = f"""SELECT [User].Oid FROM [User] WHERE [User].CardNumber = '{current_user.CardNumber}'"""
#     current_User = SQLManipulator.SQLExecute(sql_GetCurrentUser)

#     # Создаем запись введенного изделия в таблице ProductWeight
#     sql_PostProductWeight = f"""INSERT INTO ProductWeight (Oid, ProductionData, Weight, CreateDate, Creator)
#                                 VALUES (NEWID(), '{production_data}', {entered_weight}, GETDATE(), '{current_User[0][0]}');"""
#     SQLManipulator.SQLExecute(sql_PostProductWeight)


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
    return CheckRolesForInterface('Оператор', 'operator/changeLabel.html')

# Схема упаковки


@app.route('/operator/PackingScheme')
@login_required
def OperatorPackingScheme():
    return CheckRolesForInterface('Оператор', 'operator/packingScheme.html')
