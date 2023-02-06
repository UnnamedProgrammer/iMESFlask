from iMES import app
from iMES import socketio,current_tpa
from flask import request
from iMES.Model.BaseObjectModel import BaseObjectModel
from datetime import datetime
from iMES.Model.ShiftTaskModels.ShiftTaskLoad import ShiftTaskLoader
from iMES import ProductDataMonitoring
import json
from flask_login import login_required


@socketio.on('UpdateShiftTask')
@login_required
def UpdateShiftTask(data):
    ip_addr = request.remote_addr
    date = 0
    socketio.emit("GetProgressStatus",
        data=json.dumps({ip_addr: '0'}),ensure_ascii=False, indent=4)
    old_task_list =BaseObjectModel.SQLExecute(f"""
        SELECT [Oid]
            FROM [MES_Iplast].[dbo].[ShiftTask]
                WHERE Equipment = '{current_tpa[ip_addr][0]}'
    """)
    progress_max = 50
    i = 1
    for task in old_task_list:
        prod_data = BaseObjectModel.SQLExecute(f"""
            SELECT Oid FROM ProductionData
                WHERE ShiftTask = '{task[0]}'
        """)
        if len(prod_data) > 0:
            prod_data = prod_data[0][0]
            BaseObjectModel.SQLExecute(f"""
                DELETE FROM [ProductWaste] 
                    WHERE ProductionData = '{prod_data}'
                DELETE FROM [ProductWeight]
                    WHERE ProductionData = '{prod_data}'
                DELETE FROM [ProductionData]
                    WHERE Oid = '{prod_data}'
                DELETE FROM ShiftTask
                    WHERE Oid = '{task[0]}'
            """)
        else:
            BaseObjectModel.SQLExecute(f"""
                DELETE FROM ShiftTask
                    WHERE Oid = '{task[0]}'
            """)
        socketio.emit("GetProgressStatus",
            data=json.dumps({ip_addr: int(0+((progress_max/len(old_task_list))*(i)))}),ensure_ascii=False, indent=4)
        i += 1
    nomenclature_group_oid = BaseObjectModel.SQLExecute(f"""
        SELECT [NomenclatureGroup] 
            FROM [Equipment]
                WHERE Oid = '{current_tpa[ip_addr][0]}'
    """)
    if len(nomenclature_group_oid) > 0:
        nomenclature_group_oid = nomenclature_group_oid[0][0]
        nomenclature_group = BaseObjectModel.SQLExecute(f"""
            SELECT [Code]
                FROM [NomenclatureGroup]
                    WHERE Oid = '{nomenclature_group_oid}'
        """)
        if len(nomenclature_group) > 0:
            nomenclature_group = nomenclature_group[0][0]
            now = datetime.now()
            year = str(now.year)
            month = str(now.month)
            day = str(now.day)
            if now.month < 10:
                month = '0' + month
            if now.day < 10:
                day = '0' + day
            socketio.emit("GetProgressStatus",
                data=json.dumps({ip_addr: "45"}),ensure_ascii=False, indent=4)
            date = int(str(year + month + day))
        else:
            socketio.emit("GetProgressStatus",
                data=json.dumps({ip_addr: "Complete"}),ensure_ascii=False, indent=4) 
            return
    else:
        socketio.emit("GetProgressStatus",
            data=json.dumps({ip_addr: "Complete"}),ensure_ascii=False, indent=4) 
        return
    LoadShiftTask = ShiftTaskLoader(nomenclature_group, date, 3, app)
    LoadShiftTask.Get_ShiftTask()
    LoadShiftTask.InsertToDataBase(to_current_shift=True)
    for i in range(0, len(ProductDataMonitoring.tpalist)):
        if ProductDataMonitoring.tpalist[i][0] == current_tpa[ip_addr][0]:
            ProductDataMonitoring.tpalist[i][3]['ShiftTask'] = []
            socketio.emit("GetProgressStatus",
                data=json.dumps({ip_addr: "50"}),ensure_ascii=False, indent=4)
            counts = 0
            while len(ProductDataMonitoring.tpalist[i][3]['ShiftTask']) == 0:
                if counts == 6: break
                ProductDataMonitoring.OnceMonitoring()
                counts += 1
            new_shift_tasks = BaseObjectModel.SQLExecute(f"""
                SELECT [Oid]
                    FROM [MES_Iplast].[dbo].[ShiftTask]
                        WHERE Equipment = '{current_tpa[ip_addr][0]}'
            """)
            if len(new_shift_tasks) > 0:
                i = 1
                for task in range(0,len(new_shift_tasks)*3):
                    ProductDataMonitoring.OnceMonitoring()
                    socketio.emit("GetProgressStatus",
                        data=json.dumps({ip_addr: int(
                            progress_max+((progress_max/(len(new_shift_tasks)*3))*(i)))}),
                                ensure_ascii=False, indent=4)
                    i += 1
            break
    socketio.emit("GetProgressStatus",
        data=json.dumps({ip_addr: "Complete"}),ensure_ascii=False, indent=4)
    return