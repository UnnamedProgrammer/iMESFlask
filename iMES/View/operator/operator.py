from iMES import app, db, socketio, current_tpa
from flask_login import login_required, current_user
from iMES.Model.DataBaseModels.EmployeeModel import Employee
from iMES.Model.DataBaseModels.EquipmentModel import Equipment
from iMES.Model.DataBaseModels.StickerInfoModel import StickerInfo
from iMES.functions.CheckRolesForInterface import CheckRolesForInterface
from flask import request
import json
from iMES.functions.rewrite_role import rewrite_role
from datetime import datetime

from iMES.Model.DataBaseModels.ProductWeightModel import ProductWeight
from iMES.Model.DataBaseModels.ProductModel import Product
from iMES.Model.DataBaseModels.ProductionDataModel import ProductionData
from iMES.Model.DataBaseModels.ShiftModel import Shift
from iMES.Model.DataBaseModels.ShiftTaskModel import ShiftTask
from iMES.Model.DataBaseModels.UserModel import User
from iMES.Model.DataBaseModels.ProductWasteModel import ProductWaste
from iMES.Model.DataBaseModels.MaterialModel import Material
from iMES.Model.DataBaseModels.DowntimeFailureModel import DowntimeFailure


# Отображение окна оператора
@app.route('/operator')
@login_required
def operator():
    rewrite_role('Оператор')
    return CheckRolesForInterface('Оператор', 'operator/operator.html')


# Окно ввода веса изделия
@app.route('/operator/tableWeight')
@login_required
def tableWeight():
    ip_addr = request.remote_addr
    weight_list = []
    productions_data = []
    # Определяем текущую смену
    shift = db.session.query(Shift).order_by(Shift.StartDate.desc()).first()
    # Находим все сменные задания по ТПА
    all_st_of_shift = (
                        db.session.query(ShiftTask)
                        .where(ShiftTask.Shift == shift.Oid)
                        .where(ShiftTask.Equipment == current_tpa[ip_addr][2].tpa)
                        .all()
                       )
    # Находим данные по производству продукции на данный момент
    for st in all_st_of_shift:
        pd = db.session.query(ProductionData).where(ProductionData.ShiftTask == st.Oid).one_or_none()
        if pd is not None:
            productions_data.append(pd)
    
    if len(productions_data) > 0:
        # Ищем записи введённого веса закреплённые по данным по производству
        for pd in productions_data:
            product_weight = \
                (db.session.query(
                    Product.Oid, 
                    Product.Name, 
                    ProductWeight.Weight,
                    ProductWeight.CreateDate,
                    Employee.LastName,
                    Employee.FirstName,
                    Employee.MiddleName)
                    .select_from(ProductWeight)
                    .join(User)
                    .join(Employee)
                    .join(ProductionData)
                    .join(ShiftTask)
                    .join(Product)
                    .where(ProductWeight.ProductionData == pd.Oid)
                    .all()
                )
            for pw in product_weight:
                weight_list.append(pw)

    # Формируем массив записей с нужным форматированием значений
    if weight_list:
        table_info = list()
        for i in range(len(weight_list)):
            table_info.append([weight_list[i][0],
                               weight_list[i][1], 
                               f'{weight_list[i][2]:.3f}', 
                               str(weight_list[i][3].strftime('%d.%m.%Y %H:%M:%S')), 
                               f'{weight_list[i][4]} {weight_list[i][5]} {weight_list[i][6]}'])
    # Если за смену вес никто не вводил, то формируем пустой массив
    else:
        table_info = list()

    # Получаем данные о текущем продукте и производственных данных
    products = []
    for st in all_st_of_shift:
        product = (db.session.query(Product.Name, ProductionData.Oid)
                    .where(ProductionData.ShiftTask == st.Oid)
                    .where(Product.Oid == st.Product)
                    .one_or_none()
                  )
        if product is not None:
            if product[0] not in products:
                products.append(product)

    return CheckRolesForInterface('Оператор', 'operator/tableWeight.html', [table_info, current_tpa[ip_addr], products])

# Кнопка ввода веса изделия во всплывающей клавиатуре была нажата
@socketio.on('product_weight_entering')
def handle_entered_product_weight(data):
    entered_weight = float(data[0])
    production_data = str(data[1])

    # Создаем запись введенного изделия в таблице ProductWeight
    prod_w = ProductWeight()
    prod_w.ProductionData = production_data
    prod_w.Weight = entered_weight
    prod_w.CreateDate = datetime.now()
    prod_w.Creator = current_user.Oid
    db.session.add(prod_w)
    db.session.commit()

# Получение данных о введенном весе для печати
@socketio.on(message='GetWeightSticker')
def GetWeightSticker(data):
    ip_addr = request.remote_addr
    weight_list = []
    productions_data = []
    # Определяем текущую смену
    shift = db.session.query(Shift).order_by(Shift.StartDate.desc()).first()
    all_st_of_shift = (
                    db.session.query(ShiftTask)
                    .where(ShiftTask.Shift == shift.Oid)
                    .where(ShiftTask.Equipment == current_tpa[ip_addr][2].tpa)
                    .all()
                    )
    # Находим данные по производству продукции на данный момент
    for st in all_st_of_shift:
        pd = db.session.query(ProductionData).where(ProductionData.ShiftTask == st.Oid).one_or_none()
        if pd is not None:
            productions_data.append(pd)

    if len(productions_data) > 0:
        # Ищем записи введённого веса закреплённые по данным по производству
        for pd in productions_data:
            product_weight = \
                (db.session.query(
                    Product.Name, 
                    ProductWeight.Weight,
                    ProductWeight.CreateDate)
                    .select_from(ProductWeight)
                    .join(User)
                    .join(Employee)
                    .join(ProductionData)
                    .join(ShiftTask)
                    .join(Product)
                    .where(ProductWeight.ProductionData == pd.Oid)
                    .all()
                )
            for pw in product_weight:
                weight_list.append(pw)

    data = {}
    keys = []
    for weight in weight_list:
        if not weight[0] in keys:
            keys.append(weight[0])
            data[weight[0]] = []
               
    for key in keys:
        for weight in weight_list:
            if weight[0] == key:
                data[key].append([float(weight[1]),weight[2].strftime('%H:%M:%S')])
    
    socketio.emit("SendWeightSticker", json.dumps(
        {ip_addr: data}, ensure_ascii=False, indent=4))

# Окно отходов и брака
@login_required
@app.route('/operator/tableWasteDefect')
def tableWasteDefect():
    ip_addr = request.remote_addr
    waste_list = []
    productions_data = []
    # Определяем текущую смену
    shift = db.session.query(Shift).order_by(Shift.StartDate.desc()).first()
    # Находим все сменные задания по ТПА
    all_st_of_shift = (
                        db.session.query(ShiftTask)
                        .where(ShiftTask.Shift == shift.Oid)
                        .where(ShiftTask.Equipment == current_tpa[ip_addr][2].tpa)
                        .all()
                       )
    # Находим данные по производству продукции на данный момент
    for st in all_st_of_shift:
        pd = db.session.query(ProductionData).where(
            ProductionData.ShiftTask == st.Oid).where(
                ProductionData.StartDate != None).one_or_none()
        if pd is not None:
            productions_data.append(pd)
    
    if len(productions_data) > 0:
        # Ищем записи введённого брака или отхода закреплённые по данным по производству
        for pd in productions_data:
            product_waste = \
                (db.session.query(
                    ProductWaste.Material, 
                    Product.Name, 
                    ProductWaste.Type,
                    ProductWaste.Count,
                    ProductWaste.Weight,
                    ProductWaste.Note,
                    ProductWaste.CreateDate,
                    Employee.LastName,
                    Employee.FirstName,
                    Employee.MiddleName)
                    .select_from(ProductWaste)
                    .join(User)
                    .join(Employee)
                    .join(ProductionData)
                    .join(ShiftTask)
                    .join(Product)
                    .where(ProductWaste.ProductionData == pd.Oid)
                    .all()
                )
            for pw in product_waste:
                waste_list.append(pw)



    # Проверяем были ли введены отходы и/или брак в текущую смену
    # Если был, то записываем данные в кортежи в нужном формате для отображения на странице
    current_material = [['']]
    if waste_list:
        waste_defect_info = list()

        for i in range(len(waste_list)):

            if waste_list[i][0] != None or waste_list[i][2] == 0:
                current_material = db.session.query(Material.Name).where(Material.Oid == waste_list[i][0]).one_or_none()
                if current_material is None:
                    current_material = [['']]

            waste_defect_info.append([waste_list[i][1], 
                                      waste_list[i][2],
                                      current_material[0],
                                      f'{waste_list[i][3]:.0f}' if waste_list[i][3] else '',
                                      f'{waste_list[i][4]:.3f}', waste_list[i][5] if waste_list[i][5] else '',
                                      str(waste_list[i][6].strftime('%d.%m.%Y %H:%M:%S')),
                                      f'{waste_list[i][7]} {waste_list[i][8]} {waste_list[i][9]}'
                                    ])
    # Если за смену вес никто не вводил, то формируем пустой массив
    else:
        waste_defect_info = list()

    products = []
    for st in all_st_of_shift:
        product = (db.session.query(ProductionData.Oid, Product.Name)
                    .where(ProductionData.ShiftTask == st.Oid)
                    .where(Product.Oid == st.Product)
                    .where(ProductionData.StartDate != None)
                    .one_or_none()
                  )
        if product is not None:
            if product[0] not in products:
                products.append(product)
    
    # Получаем данные о всех существующих отходах
    all_wastes = db.session.query(Material.Oid, Material.Name).where(Material.Type == 1).order_by(Material.Name).all()

    return CheckRolesForInterface('Оператор', 'operator/tableWasteDefect/tableWasteDefect.html', [waste_defect_info, products, all_wastes])


# Кнопка ввода веса отходов во всплывающей клавиатуре была нажата
@socketio.on('product_wastes')
def handle_entered_product_wastes(data):
    # Получили данные по отходу из сокета
    production_data = str(data[0])
    material_oid = str(data[1])
    entered_waste_weight = float(data[2])
    # Создаем запись введенного отхода в таблице ProductWaste
    new_pd_waste = ProductWaste()
    new_pd_waste.ProductionData = production_data
    new_pd_waste.Material = material_oid
    new_pd_waste.Type = 0
    new_pd_waste.Weight = entered_waste_weight
    new_pd_waste.CreateDate = datetime.now()
    new_pd_waste.Creator = current_user.Oid
    db.session.add(new_pd_waste)
    db.session.commit()


# Кнопка ввода брака во всплывающей клавиатуре была нажата
@socketio.on('product_defect')
def handle_entered_product_wastes(data):
    # Получили данные по браку из сокета
    production_data = str(data[0])
    entered_defect_weight = float(data[1])
    entered_defect_count = float(data[2])

    # Создаем запись введенного брака в таблице ProductWaste
    new_pd_waste = ProductWaste()
    new_pd_waste.ProductionData = production_data
    new_pd_waste.Count = entered_defect_count
    new_pd_waste.Type = 1
    new_pd_waste.Weight = entered_defect_weight
    new_pd_waste.CreateDate = datetime.now()
    new_pd_waste.Creator = current_user.Oid
    db.session.add(new_pd_waste)
    db.session.commit()

# Получение данных о введенных отходах для печати
@socketio.on(message='GetWasteSticker')
def GetWasteSticker(data):
    ip_addr = request.remote_addr
    waste_list = []
    productions_data = []
    # Определяем текущую смену
    shift = db.session.query(Shift).order_by(Shift.StartDate.desc()).first()
    all_st_of_shift = (
                    db.session.query(ShiftTask)
                    .where(ShiftTask.Shift == shift.Oid)
                    .where(ShiftTask.Equipment == current_tpa[ip_addr][2].tpa)
                    .all()
                    )
    # Находим данные по производству продукции на данный момент
    for st in all_st_of_shift:
        pd = db.session.query(ProductionData).where(ProductionData.ShiftTask == st.Oid).one_or_none()
        if pd is not None:
            productions_data.append(pd)

    if len(productions_data) > 0:
        # Ищем записи введённых отходов закреплённые по данным по производству
        for pd in productions_data:
            product_weight = \
                (db.session.query(
                    Product.Name, 
                    ProductWaste.Weight)
                    .select_from(ProductWaste)
                    .join(User)
                    .join(Employee)
                    .join(ProductionData)
                    .join(ShiftTask)
                    .join(Product)
                    .where(ProductWaste.ProductionData == pd.Oid)
                    .where(ProductWaste.Type == 0)
                    .all()
                )
            for pw in product_weight:
                waste_list.append(pw)

    data = {}
    keys = []
    total = 0
    for waste in waste_list:
        if not waste[0] in keys:
            keys.append(waste[0])
            data[waste[0]] = []
               
    for key in keys:
        for waste in waste_list:
            if waste[0] == key:
                total += float(waste[1])
                data[key] = [total]
        total = 0
    
    socketio.emit("SendWasteSticker", json.dumps(
        {ip_addr: data}, ensure_ascii=False, indent=4))
    
# Получение данных о введенном браке для печати
@socketio.on(message='GetDefectSticker')
def GetDefectSticker(data):
    ip_addr = request.remote_addr
    waste_list = []
    productions_data = []
    # Определяем текущую смену
    shift = db.session.query(Shift).order_by(Shift.StartDate.desc()).first()
    all_st_of_shift = (
                    db.session.query(ShiftTask)
                    .where(ShiftTask.Shift == shift.Oid)
                    .where(ShiftTask.Equipment == current_tpa[ip_addr][2].tpa)
                    .all()
                    )
    # Находим данные по производству продукции на данный момент
    for st in all_st_of_shift:
        pd = db.session.query(ProductionData).where(ProductionData.ShiftTask == st.Oid).one_or_none()
        if pd is not None:
            productions_data.append(pd)

    if len(productions_data) > 0:
        # Ищем записи введённого брака закреплённые по данным по производству
        for pd in productions_data:
            product_weight = \
                (db.session.query(
                    Product.Name, 
                    ProductWaste.Weight,
                    ProductWaste.Count)
                    .select_from(ProductWaste)
                    .join(User)
                    .join(Employee)
                    .join(ProductionData)
                    .join(ShiftTask)
                    .join(Product)
                    .where(ProductWaste.ProductionData == pd.Oid)
                    .where(ProductWaste.Type == 1)
                    .all()
                )
            for pw in product_weight:
                waste_list.append(pw)

    data = {}
    keys = []
    totalWeight = 0
    totalCount = 0
    for defect in waste_list:
        if not defect[0] in keys:
            keys.append(defect[0])
            data[defect[0]] = []
               
    for key in keys:
        for defect in waste_list:
            if defect[0] == key:
                totalWeight += float(defect[1])
                totalCount += float(defect[2])
                data[key] = [totalWeight, totalCount]
        totalWeight = 0
        totalCount = 0

    socketio.emit("SendDefectSticker", json.dumps(
        {ip_addr: data}, ensure_ascii=False, indent=4))

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
    
    current_product_name = [(db.session.query(Product.Name, 
                                            Product.Oid, 
                                            StickerInfo.StickerCount
                                            ).where(Product.Oid == StickerInfo.Product)
                                             .where(StickerInfo.Equipment == current_tpa[ip_addr][2].tpa)).one_or_none()]
    current_product = []
    if current_product_name is not None:
        pass
    else:
        current_product_name = [(' ', ' ', ' ')]
    with open('st.json', 'r', encoding='utf-8-sig') as file_json:
        json_file = json.load(file_json)[0]
        for task in json_file['Order']:
            if (((task['WorkCenter'] == current_tpa[ip_addr][2].WorkCenter) or
                (task['oid'] == current_tpa[ip_addr][2].TpaNomenclatureCode)) and
                (current_tpa[ip_addr][2].TpaNomenclatureCode != "")):
                current_tpa[ip_addr][2].WorkCenter = task['WorkCenter']
                break
        for task in json_file['Order']:
            if ((task['WorkCenter'] == current_tpa[ip_addr][2].WorkCenter) or
                (task['oid'] == current_tpa[ip_addr][2].TpaNomenclatureCode)):
                product = (db.session.query(
                    Product.Oid, Product.Name).select_from(Product)
                                              .where(Product.Code == task["ProductCode"])
                                              .one_or_none())
                if product is not None:
                    current_product.append(list(product))
        file_json.close()
    current_product_duplicate = [] 
    for i in range(0, len(current_product)):
        if current_product[i] not in current_product_duplicate:
            current_product_duplicate.append(current_product[i])
    current_product = current_product_duplicate
    return CheckRolesForInterface('Оператор', 'operator/changeLabel.html', [current_product, current_product_name])


# Кнопка сохранить на странице изменение этикетки была нажата
@socketio.on('sticker_info_change')
def handle_sticker_info_change(data):
    ip_addr = request.remote_addr  

    entered_product = str(data[0])
    entered_sticker_count = int(data[1])
    stinfo_is_instance = False
    # Проверяем, существует ли запись текущей ТПА в таблице StickerInfo
    sticker_info = db.session.query(StickerInfo).where(StickerInfo.Equipment == current_tpa[ip_addr][0]).one_or_none()
    if sticker_info != None:
        stinfo_is_instance = current_tpa[ip_addr][0] == str(sticker_info.Equipment).upper()
    if stinfo_is_instance:
        # Обновляем запись этикетки в таблице StickerInfo
        sticker_info.Product = entered_product
        sticker_info.StickerCount = entered_sticker_count
        sticker_info.Equipment = current_tpa[ip_addr][0]
        db.session.commit()
    else:
        # Создаем запись введенной этикетки в таблице StickerInfo
        new_sticker_info = StickerInfo()
        new_sticker_info.Equipment = current_tpa[ip_addr][0]
        new_sticker_info.Product = entered_product
        new_sticker_info.StickerCount = entered_sticker_count
        new_sticker_info.CreateDate = datetime.now()
        new_sticker_info.Creator = current_user.Oid
        db.session.add(new_sticker_info)
        db.session.commit()


# Схема упаковки
@app.route('/operator/PackingScheme')
@login_required
def OperatorPackingScheme():
    return CheckRolesForInterface('Оператор', 'operator/packingScheme.html')
