import sqlalchemy
from iMES import app, db
from flask import request, redirect
from iMES import current_tpa
from iMES import socketio
from flask_login import login_required, current_user
from iMES.Model.DataBaseModels.MaterialModel import Material
from iMES.Model.DataBaseModels.ProductModel import Product
from iMES.Model.DataBaseModels.ProductWasteModel import ProductWaste
from iMES.Model.DataBaseModels.ProductionDataModel import ProductionData
from iMES.Model.DataBaseModels.ShiftTaskModel import ShiftTask
from iMES.functions.CheckRolesForInterface import CheckRolesForInterface
from iMES.functions.rewrite_role import rewrite_role
import json
from datetime import datetime
from iMES.Model.DataBaseModels.DowntimeFailureModel import DowntimeFailure as DF
from iMES.Model.DataBaseModels.TakenMeasuresModel import TakenMeasures as TM
from iMES.Model.DataBaseModels.MalfunctionDescriptionModel import MalfunctionDescription as MDesc
from iMES.Model.DataBaseModels.MalfunctionCauseModel import MalfunctionCause as MCause
from iMES.Model.DataBaseModels.UserModel import User
from iMES.Model.DataBaseModels.EmployeeModel import Employee
from iMES.Model.DataBaseModels.DowntimeTypeModel import DowntimeType
from iMES.Model.DataBaseModels.ShiftModel import Shift



# Метод возвращает окно наладчика
@app.route('/adjuster')
@login_required
def adjuster():
    rewrite_role('Наладчик')
    return CheckRolesForInterface('Наладчик', 'adjuster/adjuster.html')

# Простои, неполадки и чеклисты
@app.route('/adjuster/journal')
@login_required
def adjusterJournal():
    ip_addr = request.remote_addr
    df = (db.session.query(DF.Oid,
                            DF.Equipment,
                            DF.StartDate,
                            DF.EndDate,
                            MCause.Name,
                            MDesc.Name,
                            TM.Name,
                            DF.Note,
                            DF.CreateDate,
                            Employee.LastName,
                            Employee.FirstName,
                            Employee.MiddleName)
                            .select_from(DF, Employee, User)
                            .outerjoin(MCause)
                            .outerjoin(MDesc)
                            .outerjoin(TM)
                            .outerjoin(Employee)
                            .where(User.Oid == DF.Creator)
                            .where(DF.Equipment == current_tpa[ip_addr][0])
                            .order_by(DF.StartDate.desc()))


    return CheckRolesForInterface('Наладчик', 'adjuster/journal.html', df)

# Фиксация простоя
@app.route('/adjuster/journal/idleEnter')
@login_required
def adjusterIdleEnter():
    idles = request.args.getlist('idles')
    idleOid = request.args.getlist('oid')[0]
    start = datetime.strptime(request.args.getlist('start_date')[0], '%Y.%m.%d-%H:%M:%S')
    end = None
    if request.args.getlist('end_date')[0] != '':
        end = datetime.strptime(request.args.getlist('end_date')[0], '%Y.%m.%d-%H:%M:%S')
    ip_addr = request.remote_addr
        
    downtimeData = [idleOid, start, end, idles]
    shift = db.session.query(Shift).order_by(Shift.StartDate.desc()).first()
    # Получение типа простоев
    downtimeType = (db.session.query(DowntimeType.Oid,
                                    DowntimeType.Name,
                                    DowntimeType.Status,
                                    DowntimeType.SyncId)
                                    .select_from(DowntimeType)
                                    .where(DowntimeType.Status == 1)
                                    .order_by(DowntimeType.Name).all())
    
    # Получение справочника причин неисправности
    malfunctionCause = (db.session.query(MCause.Oid,
                                        MCause.Name,
                                        MCause.Status)
                                        .select_from(MCause)
                                        .order_by(MCause.Name)
                                        .all())


    # Получение справочника описаний неисправности
    malfunctionDescription = (db.session.query(MDesc.Oid, 
                                               MDesc.Name, 
                                               MDesc.Status)
                                               .select_from(MDesc)
                                               .order_by(MDesc.Name)
                                               .all())
                                            
    # Получение справочника предпринятых мер
    takenMeasures = (db.session.query(TM.Oid,
                                     TM.Name,
                                     TM.Status)
                                     .select_from(TM)
                                     .order_by(TM.Name)
                                     .all())
    
    # Получаем данные о текущем продукте и производственных данных
    current_product = (db.session.query(ProductionData.Oid, 
                                        Product.Name)
                                        .select_from(ProductionData, Product, ShiftTask)
                                        .where(ShiftTask.Shift == shift.Oid)
                                        .where(ShiftTask.Equipment == current_tpa[ip_addr][0])
                                        .where(Product.Oid == ShiftTask.Product)
                                        .where(ProductionData.ShiftTask == ShiftTask.Oid)
                                        .where(ProductionData.Status == 1)
                                        .all())

    # Получаем данные о всех существующих отходах
    all_wastes = (db.session.query(Material.Oid,
                                   Material.Name)
                                   .select_from(Material)
                                   .order_by(Material.Name)
                                   .all())
    
    # Получаем уже введенные отходы
    existing_wastes = (db.session.query(ProductWaste.Oid, 
                                        Material.Name,
                                        ProductWaste.Weight, 
                                        ProductWaste.CreateDate)
                                        .select_from(ProductWaste,
                                                     Material, 
                                                     ShiftTask, 
                                                     ProductionData)
                                        .where(ShiftTask.Shift == shift.Oid)
                                        .where(ShiftTask.Equipment == current_tpa[ip_addr][0])
                                        .where(ProductionData.ShiftTask == ShiftTask.Oid)
                                        .where(ProductionData.Status == 1)
                                        .where(ProductWaste.ProductionData == ProductionData.Oid)
                                        .where(ProductWaste.Type == 0)
                                        .where(Material.Oid == ProductWaste.Material)
                                        .all()
                                        )
    
    # Получаем уже введенный брак
    existing_defect = (db.session.query(ProductWaste.Oid, 
                                        Product.Name,
                                        ProductWaste.Weight, 
                                        ProductWaste.Count,
                                        ProductWaste.CreateDate)
                                        .select_from(ProductWaste, 
                                                     ShiftTask, 
                                                     ProductionData,
                                                     Product)
                                        .where(ShiftTask.Shift == shift.Oid)
                                        .where(ShiftTask.Equipment == current_tpa[ip_addr][0])
                                        .where(ProductionData.ShiftTask == ShiftTask.Oid)
                                        .where(ProductionData.Status == 1)
                                        .where(ProductWaste.ProductionData == ProductionData.Oid)
                                        .where(ProductWaste.Type == 1)
                                        .where(Product.Oid == ShiftTask.Product)
                                        .all()
                                        )
    
    return CheckRolesForInterface('Наладчик', 
                                  'adjuster/idles/idleEnter.html', [
                                  downtimeData, 
                                  downtimeType, 
                                  malfunctionCause, 
                                  malfunctionDescription, 
                                  takenMeasures, 
                                  all_wastes, 
                                  existing_wastes, 
                                  current_product, 
                                  existing_defect
                                  ])


# Ввод данных о фиксации простоя в БД
@socketio.on('idleEnterFixing')
def idleEnterFixing(data):
    ip_addr = request.remote_addr
    idles_data = data['idles'][2:-2]
    idles = json.loads(idles_data)
    validClosures = data['validClousers']
    if validClosures == '':
        validClosures = '0'
    if data['idleEnd'] != '':
        formated_endDate = datetime.strptime(data['idleEnd'], '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%dT%H:%M:%S')
        # Добавление новой записи в DowntimeFailure (зафиксированный простой)
        downtime_failure = db.session.query(DF).where(DF.Oid == data['idleOid']).one_or_none()
        if downtime_failure is not None:
            downtime_failure.DowntimeType = data['idleType']
            downtime_failure.MalfunctionCause = data['idleCause']
            downtime_failure.MalfunctionDescription = data['idleDescription']
            downtime_failure.TakenMeasures = data['idleTakenMeasures']
            downtime_failure.Note = data['idleNote']
            downtime_failure.CreateDate = datetime.now()
            downtime_failure.Creator = current_user.Oid
            downtime_failure.EndDate = formated_endDate
            downtime_failure.ValidClosures = validClosures
    else:
        downtime_failure = db.session.query(DF).where(DF.Oid == data['idleOid']).one_or_none()
        if downtime_failure is not None:
            downtime_failure.DowntimeType = data['idleType']
            downtime_failure.MalfunctionCause = data['idleCause']
            downtime_failure.MalfunctionDescription = data['idleDescription']
            downtime_failure.TakenMeasures = data['idleTakenMeasures']
            downtime_failure.Note = data['idleNote']
            downtime_failure.CreateDate = datetime.now()
            downtime_failure.Creator = current_user.Oid
            downtime_failure.EndDate = None
            downtime_failure.ValidClosures = validClosures
    
    # Добавление нового отхода и привязки к простою
    idle_key_list = list(data.keys())
    if 'newWaste' in idle_key_list:
        if len(data['newWaste']) != 0:  
            for i in range(len(data['newWaste'])):
                newWaste = data['newWaste'][i][0].split(',')
                product_waste = ProductWaste()
                product_waste.ProductionData = newWaste[0]
                product_waste.Material = newWaste[1]
                product_waste.Type = 0
                product_waste.Weight = newWaste[2]
                product_waste.Downtime = data['idleOid']
                product_waste.CreateDate = datetime.now()
                product_waste.Creator = data['creatorOid']
                db.session.add(product_waste)

    # Добавление нового брака и привязки к простою
    if 'newDefect' in idle_key_list:        
        if len(data['newDefect']) != 0:  
            for i in range(len(data['newDefect'])):
                newDefect = data['newDefect'][i].split(',')
                defect = ProductWaste()
                defect.ProductionData = newDefect[0]
                defect.Type = 1
                defect.Weight = newDefect[1]
                defect.Count = newDefect[2]
                defect.Downtime = data['idleOid']
                defect.CreateDate = datetime.now()
                defect.Creator = data['creatorOid']
                db.session.add(defect)

    # Привязку существующего отхода к простою
    if 'existingWaste' in idle_key_list:
        if len(data['existingWaste']) != 0:
            for i in range(len(data['existingWaste'])):
                exists_waste = db.session.query(ProductWaste).where(
                    ProductWaste.Oid == data['existingWaste'][i]).one_or_none()
                if exists_waste is not None:
                    exists_waste.Downtime = data['idleOid']
        
    # Привязку существующего брака к простою
    if 'existingDefect' in idle_key_list:
        if len(data['existingDefect']) != 0:
            for i in range(len(data['existingDefect'])):
                exists_defect = db.session.query(ProductWaste).where(
                    ProductWaste.Oid == data['existingDefect'][i]).one_or_none()
                if exists_defect is not None:
                    exists_defect.Downtime = data['idleOid']

    for idle in idles:
        if idle['Oid'] != data['idleOid']:
            bad_idle = db.session.query(DF).where(
                DF.Oid == idle['Oid']).one_or_none()
            if bad_idle is not None:
                db.session.delete(bad_idle)
    db.session.commit()
    socketio.emit("IdleEntered", data=json.dumps({ip_addr: ''}),ensure_ascii=False, indent=4)

@app.route('/adjuster/journal/idleView')
@login_required
def adjusterIdleView():
    idleOid = request.args.getlist('oid')
    shift = db.session.query(Shift).order_by(Shift.StartDate.desc()).first()
    idle_data = (db.session.query(DF.Oid, 
                                  DF.StartDate, 
                                  DF.EndDate,
                                  DowntimeType.Name,
                                  MCause.Name,
                                  MDesc.Name,
                                  TM.Name,
                                  DF.Note,
                                  Employee.FirstName,
                                  Employee.LastName,
                                  Employee.MiddleName,
                                  DF.ValidClosures)
                                  .select_from(DF)
                                  .where(DF.Oid == idleOid[0])
                                  .join(DowntimeType)
                                  .join(MCause)
                                  .join(MDesc)
                                  .join(TM)
                                  .join(User).filter(User.Oid == DF.Creator)
                                  .join(Employee).filter(User.Employee == Employee.Oid)
                                  .one_or_none())
    if idle_data is not None:
        idle_wastes = (db.session.query(Material.Name, 
                                        Product.Name,
                                        ProductWaste.Weight, 
                                        ProductWaste.Count,
                                        ProductWaste.CreateDate)
                                        .select_from(ProductWaste, 
                                                     ShiftTask, 
                                                     ProductionData,
                                                     Product,
                                                     Material)
                                        .where(ShiftTask.Shift == shift.Oid)
                                        .where(ProductionData.ShiftTask == ShiftTask.Oid)
                                        .where(ProductWaste.ProductionData == ProductionData.Oid)
                                        .where(Product.Oid == ShiftTask.Product)
                                        .outerjoin(Material)
                                        .where(ProductWaste.Downtime == idleOid[0])
                                        .all()
                                        )
        if idle_wastes is None:
            idle_wastes = []
    else:
        return redirect("/adjuster/journal")
    
    return CheckRolesForInterface('Наладчик', 'adjuster/idles/idleView.html', [idle_data, idle_wastes])

@app.route('/adjuster/journal/save_idle')
@login_required
def save_idle_comment():
    idleOid = request.args.getlist('oid')[0]
    comment = request.args.getlist('comment')[0]
    idle = db.session.query(DF).where(DF.Oid == idleOid).one_or_none()
    if idle is not None:
        idle.Note = comment
        db.session.commit()
    return redirect('/adjuster/journal')

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
    shift = db.session.query(Shift).order_by(Shift.StartDate.desc()).first()
    # Получаем данные о текущих отходах и браке                       
    current_product_waste = (db.session.query(
                                            Material.Name,
                                            Product.Name,
                                            ProductWaste.Type,
                                            ProductWaste.Count,
                                            ProductWaste.Weight,
                                            ProductWaste.Note,
                                            ProductWaste.Downtime,
                                            ProductWaste.CreateDate,
                                            Employee.LastName,
                                            Employee.FirstName,
                                            Employee.MiddleName,
                                            ProductWaste.Oid)
                                            .select_from(ProductWaste, 
                                                         Material, 
                                                         ShiftTask, 
                                                         ProductionData, 
                                                         User, 
                                                         Employee, 
                                                         Product)
                                            .outerjoin(Material)
                                            .where(ShiftTask.Equipment == current_tpa[ip_addr][0])
                                            .where(ShiftTask.Shift == shift.Oid)
                                            .where(ProductionData.ShiftTask == ShiftTask.Oid)
                                            .where(ProductWaste.ProductionData == ProductionData.Oid)
                                            .where(Product.Oid == ShiftTask.Product)
                                            .where(User.Oid == ProductWaste.Creator)
                                            .where(Employee.Oid == User.Employee)
                                            .all())

    return CheckRolesForInterface('Наладчик', 'adjuster/wasteDefectFix.html', [current_product_waste])


# Кнопка "Указать причину" на странице "Зафиксировать брак и отход" была нажата
@socketio.on('waste_note_change')
def handle_waste_note_change(data):
    selected_waste_oid = str(data[0])
    entered_waste_note = str(data[1])

    # Обновляем запись отхода или брака в таблице ProductWaste
    waste = db.session.query(ProductWaste).where(ProductWaste.Oid == selected_waste_oid)
    waste.Note = entered_waste_note
    db.session.commit()


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
