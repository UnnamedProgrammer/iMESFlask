from iMES import app
from iMES import socketio
from flask import request
from flask import render_template
from iMES.Model.SQLManipulator import SQLManipulator
from iMES import current_tpa
from flask_login import current_user
from flask_login import login_required
import json

@login_required
@app.route('/operator/tableWeight')
def tableWeight():
    global sql_GetDate

    ip_addr = request.remote_addr
    sql_GetDate = "SELECT CONVERT(VARCHAR(19), GETDATE(), 121)"

    # Получаем данные о введенных за смену весов изделия
    sql_GetProductWeight = f"""SELECT Product.Name, ProductionData.Oid, ProductWeight.Weight, ProductWeight.CreateDate  
    FROM ShiftTask INNER JOIN 
    Product ON ShiftTask.Product = Product.Oid INNER JOIN
    Equipment ON ShiftTask.Equipment = Equipment.Oid AND Equipment.Oid = '{current_tpa[ip_addr][0]}' INNER JOIN 
    ProductionData ON ProductionData.ShiftTask = ShiftTask.Oid AND ProductionData.StartDate <= GETDATE() AND ProductionData.EndDate >= GETDATE() INNER JOIN
    ProductWeight ON ProductWeight.ProductionData = ProductionData.Oid"""
    product_weight = SQLManipulator.SQLExecute(sql_GetProductWeight)

    # Проверяем был ли введен вес изделий в текущую смену
    # Если был, то записываем данные в кортежи в нужном формате для отображения на странице
    if product_weight:
        table_info = [tuple(product_weight[0][0], product_weight[0][2], product_weight[0][3], current_user.name)]
    # Если за смену вес никто не вводил, то формируем пустой массив
    else:
        table_info = list()
        
    return render_template("operator/tableWeight.html", table_info=table_info, current_tpa=current_tpa[ip_addr])

# Кнопка ввода веса изделия во всплывающей клавиатуре была нажата
@socketio.on('product_weight_entering')
def handle_entered_product_weight(data):
    ip_addr = request.remote_addr
    entered_weight = str(data)
    # Получаем время нажатия
    current_date_e = SQLManipulator.SQLExecute(sql_GetDate)

    sql_GetCurrentUser = f"""SELECT [User].Oid FROM [User] WHERE [User].CardNumber = '{current_user.CardNumber}'"""
    current_User = SQLManipulator.SQLExecute(sql_GetCurrentUser)

    # Получаем данные о текущем продукте и производственных данных
    sql_GetCurrentProductionData = f"""SELECT Product.Name, ProductionData.Oid
        FROM ShiftTask INNER JOIN 
        Product ON ShiftTask.Product = Product.Oid INNER JOIN
        Equipment ON ShiftTask.Equipment = Equipment.Oid AND Equipment.Oid = '{current_tpa[ip_addr][0]}' INNER JOIN 
        ProductionData ON ProductionData.ShiftTask = ShiftTask.Oid WHERE ProductionData.StartDate <= GETDATE() AND ProductionData.EndDate >= GETDATE()"""
    current_production_data = SQLManipulator.SQLExecute(sql_GetCurrentProductionData)

    # Формируем json словарь и отправляем данные на сайт
    broadcasted_data = json.dumps({'ip_address': ip_addr, 'data': [current_production_data[0][0], entered_weight, current_date_e[0][0], current_user.name]})
    socketio.emit('table_weight', broadcasted_data)
    
    # Создаем запись введенного изделия в таблице ProductWeight
    sql_PostProductWeight = f"""INSERT INTO ProductWeight (Oid, ProductionData, Weight, CreateDate, Creator)
                                VALUES (NEWID(), '{current_production_data[0][1]}', '{entered_weight}', {current_date_e[0][0]}, '{current_User[0][0]}');"""
    SQLManipulator.SQLExecute(sql_PostProductWeight)

# Кнопка печати введенных весов изделия во всплывающей клавиатуре была нажата
@socketio.on('product_weight_printing')
def handle_printed_product_weight():
    ip_addr = request.remote_addr
    # Получаем время нажатия
    current_date_p = SQLManipulator.SQLExecute(sql_GetDate)
    # Получаем данные о введенных за смену весов изделия
    sql_GetPrintProductWeight = f"""SELECT ProductWeight.Weight, ProductWeight.CreateDate  
    FROM ShiftTask INNER JOIN 
    Equipment ON ShiftTask.Equipment = Equipment.Oid AND Equipment.Oid = '{current_tpa[ip_addr][0]}' INNER JOIN 
    ProductionData ON ProductionData.ShiftTask = ShiftTask.Oid AND ProductionData.StartDate <= GETDATE() AND ProductionData.EndDate >= GETDATE() INNER JOIN
    ProductWeight ON ProductWeight.ProductionData = ProductionData.Oid"""
    print_product_weight = SQLManipulator.SQLExecute(sql_GetPrintProductWeight)
   
   # Формируем список со значениями веса изделия и времени его ввода
    weight_time = list()
    for row in print_product_weight:
        weight_time.append([f"{row[0] if row[0] % 1 != 0 else int(row[0])} кг.", row[1].strftime("%H:%M:%S")])
    
    # Формируем json словарь и отправляем данные на сайт
    printed_data = json.dumps({'ip_address': ip_addr, 'head_data': [current_date_p[0][0], current_tpa[ip_addr][1]], 'body_data': [weight_time]})
    socketio.emit('print_weight', printed_data)
