from iMES import app
from flask_login import login_required
from iMES.functions.CheckRolesForInterface import CheckRolesForInterface
from iMES.Model.SQLManipulator import SQLManipulator
from iMES import current_tpa
from flask import request

# Отображение окна оператора
@app.route('/operator')
@login_required
def operator():
    return CheckRolesForInterface('Оператор', 'operator/operator.html')

# Окно отходов и брака
@login_required
@app.route('/operator/tableWasteDefect')
def tableWasteDefect():
    ip_addr = request.remote_addr

    # Получаем данные о текущем продукте и производственных данных
    # sql_GetCurrentProductionData = f"""SELECT Product.Name, ProductionData.Oid
    #                                     FROM ShiftTask INNER JOIN 
    #                                     Product ON ShiftTask.Product = Product.Oid INNER JOIN
    #                                     Equipment ON ShiftTask.Equipment = Equipment.Oid AND Equipment.Oid = '{current_tpa[ip_addr][0]}' INNER JOIN 
    #                                     ProductionData ON ProductionData.ShiftTask = ShiftTask.Oid WHERE ProductionData.StartDate <= GETDATE() AND ProductionData.EndDate >= GETDATE()"""

    # sql_GetCurrentProductionData = f"""SELECT Product.Name, ProductionData.Oid
    #                                     FROM ShiftTask INNER JOIN 
    #                                     Shift ON ShiftTask.Shift = Shift.Oid AND Shift.StartDate <= GETDATE() AND Shift.EndDate >= GETDATE() INNER JOIN
    #                                     Product ON ShiftTask.Product = Product.Oid INNER JOIN
    #                                     Equipment ON ShiftTask.Equipment = Equipment.Oid AND Equipment.Oid = '{current_tpa[ip_addr][0]}' INNER JOIN 
    #                                     ProductionData ON ProductionData.ShiftTask = ShiftTask.Oid"""

    sql_GetCurrentProductionData = f"""SELECT Product.Name, ProductionData.Oid
                                        FROM ShiftTask INNER JOIN 
                                        Shift ON ShiftTask.Shift = Shift.Oid AND Shift.StartDate <= GETDATE() AND Shift.EndDate >= GETDATE() INNER JOIN
                                        Product ON ShiftTask.Product = Product.Oid INNER JOIN
                                        Equipment ON ShiftTask.Equipment = Equipment.Oid AND Equipment.Oid = '3F790841-C76A-4F9A-B4C7-7EBAA3674BAE' INNER JOIN 
                                        ProductionData ON ProductionData.ShiftTask = ShiftTask.Oid"""
    current_production_data = SQLManipulator.SQLExecute(sql_GetCurrentProductionData)

    print(current_production_data)

    # # Получаем данные о текущих отходах и браке
    # sql_GetCurrentProductWaste = f"""SELECT ProductWaste.Type, ProductWaste.Count, ProductWaste.Weight, 
 	# 	                                    ProductWaste.Note, ProductWaste.CreateDate, ProductWaste.Creator
    #                                 FROM ProductWaste INNER JOIN 
    #                                 ProductionData ON ProductWaste.ProductionData = ProductionData.Oid
    #                                 WHERE ProductionData.Oid = '{current_production_data[0][1]}'"""
    # current_product_waste = SQLManipulator.SQLExecute(sql_GetCurrentProductWaste)

    # return CheckRolesForInterface('Оператор', 'operator/tableWasteDefect/tableWasteDefect.html', {"Product name": current_production_data[0][0], 
    #                                 "Defect type": current_product_waste[0][0], "Defect count": current_product_waste[0][1], "Defect weight": current_product_waste[0][2], 
    #                                 "Defect note": current_product_waste[0][3], "Defect create date": current_product_waste[0][4], "Creator": current_product_waste[0][5]})
    
    # return CheckRolesForInterface('Оператор', 'operator/tableWasteDefect/tableWasteDefect.html', [current_production_data[0][0], 
    #                                 current_product_waste[0][0], current_product_waste[0][1], current_product_waste[0][2], 
    #                                 current_product_waste[0][3], current_product_waste[0][4], current_product_waste[0][5]])
    return CheckRolesForInterface('Оператор', 'operator/tableWasteDefect/tableWasteDefect.html')

# Окно ввода отходов
@login_required
@app.route('/operator/tableWasteDefect/wastes')
def wastes():
    ip_addr = request.remote_addr

    # # Получаем данные о предопределенных отходах
    # sql_GetPredefinedWaste = f"""SELECT Product.Name, Material.Oid, Material.Name 
    #                             FROM ShiftTask INNER JOIN 
    #                             Equipment ON Equipment.Oid = ShiftTask.Equipment AND Equipment.Oid = '{current_tpa[ip_addr][0]}' INNER JOIN
    #                             Product ON Product.Oid = ShiftTask.Product INNER JOIN
    #                             Shift ON ShiftTask.Shift = Shift.Oid AND Shift.StartDate <= GETDATE() AND Shift.EndDate >= GETDATE() INNER JOIN
    #                             SpecificationMaterial ON ShiftTask.Specification = SpecificationMaterial.Specification INNER JOIN
    #                             Material ON SpecificationMaterial.Material = Material.Oid AND Material.Type = 1"""
    
    # sql_GetPredefinedWaste = f"""SELECT DISTINCT Material.Oid, Product.Name, Material.Name
    #                                 FROM Material INNER JOIN 
    #                                 SpecificationMaterial ON SpecificationMaterial.Material = Material.Oid AND Material.Type = 1 INNER JOIN
    #                                 ProductSpecification ON SpecificationMaterial.Specification = ProductSpecification.Oid INNER JOIN
    #                                 ShiftTask ON ProductSpecification.Product = ShiftTask.Product INNER JOIN
    #                                 Shift ON ShiftTask.Shift = Shift.Oid AND Shift.StartDate <= GETDATE() AND Shift.EndDate >= GETDATE() INNER JOIN
    #                                 Product ON Product.Oid = ShiftTask.Product INNER JOIN
    #                                 Equipment ON Equipment.Oid = ShiftTask.Equipment AND Equipment.Oid = '{current_tpa[ip_addr][0]}'"""

    sql_GetPredefinedWaste = f"""SELECT DISTINCT Material.Oid, Product.Name, Material.Name
                                    FROM Material INNER JOIN 
                                    SpecificationMaterial ON SpecificationMaterial.Material = Material.Oid AND Material.Type = 1 INNER JOIN
                                    ProductSpecification ON SpecificationMaterial.Specification = ProductSpecification.Oid INNER JOIN
                                    ShiftTask ON ProductSpecification.Product = ShiftTask.Product INNER JOIN
                                    Shift ON ShiftTask.Shift = Shift.Oid AND Shift.StartDate <= GETDATE() AND Shift.EndDate >= GETDATE() INNER JOIN
                                    Product ON Product.Oid = ShiftTask.Product INNER JOIN
                                    Equipment ON Equipment.Oid = ShiftTask.Equipment AND Equipment.Oid = '3F790841-C76A-4F9A-B4C7-7EBAA3674BAE'"""
    predefined_waste = SQLManipulator.SQLExecute(sql_GetPredefinedWaste)
    
    # Получаем данные о текущей ProductionData
    # sql_GetProductionData = f"""SELECT ProductionData.Oid
    #                             FROM ShiftTask INNER JOIN 
    #                             Shift ON ShiftTask.Shift = Shift.Oid AND Shift.StartDate <= GETDATE() AND Shift.EndDate >= GETDATE() INNER JOIN
    #                             Equipment ON Equipment.Oid = ShiftTask.Equipment AND Equipment.Oid = '{current_tpa[ip_addr][0]}' INNER JOIN
    #                             ProductionData ON ProductionData.ShiftTask = ShiftTask.Oid"""

    sql_GetProductionData = f"""SELECT ProductionData.Oid
                                FROM ShiftTask INNER JOIN 
                                Shift ON ShiftTask.Shift = Shift.Oid AND Shift.StartDate <= GETDATE() AND Shift.EndDate >= GETDATE() INNER JOIN
                                Equipment ON Equipment.Oid = ShiftTask.Equipment AND Equipment.Oid = '3F790841-C76A-4F9A-B4C7-7EBAA3674BAE' INNER JOIN
                                ProductionData ON ProductionData.ShiftTask = ShiftTask.Oid"""

    production_data = SQLManipulator.SQLExecute(sql_GetProductionData)

    # # current_type = '''Получаем тип отхода: 0 - отход, 1 - брак'''

    # # # Создаем запись введенного отхода в таблице ProductWaste
    # # sql_PostProductWeight = f"""INSERT INTO ProductWaste (Oid, ProductionData, Material, Type, Weight, Count, Downtime, Note, CreateDate, Creator)
    # #                             VALUES (NEWID(), '', '', '', '{current_type}', '', '', '', '', GETDATE(), '{current_user[0][0]}');"""
    # # SQLManipulator.SQLExecute(sql_PostProductWeight)

    # Получаем данные о всех существующих отходах
    sql_GetAllWastes = f"""SELECT Oid, Name  
    FROM Material WHERE Type = 1"""
    all_wastes = SQLManipulator.SQLExecute(sql_GetAllWastes)

    return CheckRolesForInterface('Оператор', 'operator/tableWasteDefect/wastes.html', [predefined_waste, all_wastes])

# Окно ввода других отходов
@login_required
@app.route('/operator/tableWasteDefect/wastes/anotherWastes')
def anotherWastes():
    # # Получаем данные о всех существующих отходах
    # sql_GetAllWastes = f"""SELECT Oid, Name  
    # FROM Material WHERE Type = 1"""
    # all_wastes = SQLManipulator.SQLExecute(sql_GetAllWastes)
    return CheckRolesForInterface('Оператор', 'operator/tableWasteDefect/anotherWastes.html')


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
