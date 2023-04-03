from iMES import app, db
from iMES import socketio
from flask import redirect, render_template, request
from iMES import current_tpa,TpaList
from iMES.Model.DataBaseModels.EquipmentModel import Equipment
from iMES.Model.DataBaseModels.EquipmentTypeModel import EquipmentType
from iMES.Model.DataBaseModels.ProductionDataModel import ProductionData
from iMES.Model.DataBaseModels.RFIDClosureDataModel import RFIDClosureData
from iMES.Model.DataBaseModels.RFIDEquipmentBindingModel import RFIDEquipmentBinding
from iMES.Model.DataBaseModels.RFIDEquipmentModel import RFIDEquipment
from flask_login import login_required
import datetime, json
from iMES.daemons import ProductDataMonitoring
from iMES.functions.device_tpa import device_tpa


@app.route("/bindPressForms")
@login_required
def bindPressForms():
    ip_addr = request.remote_addr
    device_tpas = device_tpa(ip_addr)
    # Вытаскиваем Oid и названия существующих пресс-форм
    press_forms = (db.session.query(Equipment.Oid, Equipment.Name)
                         .select_from(Equipment)
                         .join(EquipmentType).filter(EquipmentType.Oid == Equipment.EquipmentType)
                         .where(EquipmentType.Name == 'Пресс-форма')
                         .order_by(Equipment.Name).all())
    current_tpa[ip_addr][2].pressform = current_tpa[ip_addr][2].update_pressform()
    if ip_addr in current_tpa.keys():
        return render_template("/bind_press_form/bind_press_form.html", device_tpa=device_tpas, current_tpa=current_tpa[ip_addr], press_forms=press_forms)
    else:
        return redirect("/menu")


@socketio.on('press_form_binding')
def handle_selected_press_forms(data):
    ip_addr = request.remote_addr
    selected_press_form = str(data)

    if current_tpa[ip_addr][2].controller != 'Empty':
        # Вытаскиваем Oid метки из последнего смыкания контроллера
        label = (db.session.query(RFIDClosureData.Label)
                 .select_from(RFIDClosureData)
                 .where(RFIDClosureData.Controller == current_tpa[ip_addr][2].controller)
                 .order_by(RFIDClosureData.Date.desc())
                 .first())

        # Проверяем создана ли привязка метки к прессофрме
        control_label_binding = (db.session.query(RFIDEquipmentBinding.Oid)
                                 .select_from(RFIDEquipmentBinding)
                                 .where(RFIDEquipmentBinding.RFIDEquipment == label[0])
                                 .all())
        if len(control_label_binding) > 0:
            # Ищем старую запись по Oid метки из последнего смыкания и перезаписываем значение на Oid новой метки
            old_label_REB = db.session.query(RFIDEquipmentBinding).where(RFIDEquipmentBinding.RFIDEquipment == label[0]).one_or_none()
            if old_label_REB is not None:
                old_label_REB.Equipment = selected_press_form
                db.session.commit()
        else:
            # Создаём новую привязку метки и прессформы
            new_REB = RFIDEquipmentBinding()
            new_REB.RFIDEquipment = label[0]
            new_REB.Equipment = selected_press_form
            new_REB.InstallDate = datetime.datetime.now()
            new_REB.RemoveDate = None
            new_REB.State = 1
            db.session.add(new_REB)
            db.session.commit()
    
    else:
        app.logger.critical(f"[{datetime.datetime.now()}] Нет привязки контроллера к ТПА ({current_tpa[ip_addr][2].tpa})")
    for i in range(0, len(ProductDataMonitoring.tpalist)):
        if ProductDataMonitoring.tpalist[i][0] == current_tpa[ip_addr][2].tpaoid:
            copy_shift_task = ProductDataMonitoring.tpalist[i][3]['ShiftTask'] 
            ProductDataMonitoring.tpalist[i][3]['ShiftTask'] = []
            for shift_task in copy_shift_task:
                try:
                    db.session.query(ProductionData).where(ProductionData.ShiftTask == shift_task[0]).delete()
                    db.session.commit()
                except:
                    pass
            break
    ProductDataMonitoring.GetShiftTaskByEquipmentPerformance(current_tpa[ip_addr][2].tpaoid)
    ProductDataMonitoring.OnceMonitoring()
    current_tpa[ip_addr][2].update_pressform()
    current_tpa[ip_addr][2].Check_pressform()
    socketio.emit('ChangePF',
                    data=json.dumps({ip_addr:{'status':'OK'}},
                    ensure_ascii=False, indent=4))