from iMES import app
from iMES import socketio
from flask import render_template, request
from iMES import current_tpa,TpaList
from iMES.Model.SQLManipulator import SQLManipulator
from flask_login import login_required


@login_required
@app.route("/bindPressForms")
def bindPressForms():
    ip_addr = request.remote_addr
    device_tpa = TpaList[ip_addr]
    
    # Вытаскиваем Oid и названия существующих пресс-форм
    sql_GetPressForms = """SELECT Equipment.Oid, Equipment.Name
                                                FROM Equipment 
                                                INNER JOIN EquipmentType on Equipment.EquipmentType = EquipmentType.Oid 
                                                WHERE EquipmentType.Name = 'Пресс-форма' 
                                                ORDER BY Equipment.Name"""
    press_forms = SQLManipulator.SQLExecute(sql_GetPressForms)

    return render_template("/bind_press_form/bind_press_form.html", device_tpa=device_tpa, current_tpa=current_tpa[ip_addr], press_forms=press_forms)


@socketio.on('press_form_binding')
def handle_selected_press_forms(json):
    selected_press_form = list(json)

    # Вытаскиваем Oid метки из последнего смыкания контроллера
    sql_GetLabelOid = f"""SELECT TOP (1) [Label]
                                        FROM [MES_Iplast].[dbo].[RFIDClosureData] 
                                        WHERE Controller='{selected_press_form[1]}' 
                                        ORDER BY GETDATE() DESC"""
    label = SQLManipulator.SQLExecute(sql_GetLabelOid)

    # Ищем старую запись по Oid метке из последнего смыкания и перезаписываем значение на Oid новой метки
    SQLManipulator.SQLExecute(f"""UPDATE RFIDEquipmentBinding
                                    SET Equipment = '{selected_press_form[0]}'
                                    WHERE RFIDEquipment = '{label[0][0]}'""")