from iMES import app
from iMES import socketio
from flask import render_template, request, redirect
from iMES import current_tpa,TpaList
from iMES.Model.SQLManipulator import SQLManipulator
from flask_login import login_required
import datetime, json
from iMES import ProductDataMonitoring


@app.route("/bindPressForms")
@login_required
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
    current_tpa[ip_addr][2].pressform = current_tpa[ip_addr][2].update_pressform()
    current_tpa[ip_addr][2].Check_pressform()
    return render_template("/bind_press_form/bind_press_form.html", device_tpa=device_tpa, current_tpa=current_tpa[ip_addr], press_forms=press_forms)


@socketio.on('press_form_binding')
def handle_selected_press_forms(data):
    ip_addr = request.remote_addr
    selected_press_form = str(data)

    if current_tpa[ip_addr][2].controller != 'Empty':
        # Вытаскиваем Oid метки из последнего смыкания контроллера
        sql_GetLabelOid = f"""SELECT TOP (1) [Label]
                                            FROM [MES_Iplast].[dbo].[RFIDClosureData] 
                                            WHERE Controller='{current_tpa[ip_addr][2].controller}' 
                                            ORDER BY Date DESC"""
        label = SQLManipulator.SQLExecute(sql_GetLabelOid)

        # Проверяем создана ли привязка метки к прессофрме
        control_label_binding = SQLManipulator.SQLExecute(f"""
            SELECT [Oid]
            FROM [MES_Iplast].[dbo].[RFIDEquipmentBinding] 
            WHERE RFIDEquipment = '{label[0][0]}'
        """)
        if len(control_label_binding) > 0:
            # Ищем старую запись по Oid метки из последнего смыкания и перезаписываем значение на Oid новой метки
            SQLManipulator.SQLExecute(f"""UPDATE RFIDEquipmentBinding
                                            SET Equipment = '{selected_press_form}'
                                            WHERE RFIDEquipment = '{label[0][0]}'""")
        else:
            # Создаём новую привязку метки и прессформы
            SQLManipulator.SQLExecute(f"""
                INSERT INTO [RFIDEquipmentBinding] (Oid,RFIDEquipment,Equipment,InstallDate,RemoveDate,State)
                VALUES (NEWID(),'{label[0][0]}','{selected_press_form}',GETDATE(),NULL,1)
            """)
    
    else:
        app.logger.critical(f"[{datetime.datetime.now()}] Нет привязки контроллера к ТПА ({current_tpa[ip_addr][2].tpa})")
    for i in range(0, len(ProductDataMonitoring.tpalist)):
        if ProductDataMonitoring.tpalist[i][0] == current_tpa[ip_addr][2].tpaoid:
            copy_shift_task = ProductDataMonitoring.tpalist[i][3]['ShiftTask'] 
            ProductDataMonitoring.tpalist[i][3]['ShiftTask'] = []
            for shift_task in copy_shift_task:
                try:
                    ProductDataMonitoring.SQLExecute(f"""
                        DELETE FROM ProductionData WHERE ShiftTask = '{shift_task[0]}'
                    """)
                except:
                    pass
            break
    ProductDataMonitoring.GetShiftTaskByEquipmentPerformance(current_tpa[ip_addr][2].tpaoid)
    ProductDataMonitoring.OnceMonitoring()
    socketio.emit('ChangePF',
                    data=json.dumps({ip_addr:{'status':'OK'}},
                    ensure_ascii=False, indent=4))