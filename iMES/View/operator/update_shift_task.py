from iMES import app, db
from iMES import socketio,current_tpa
from flask import request
from datetime import datetime
from iMES.Model.DataBaseModels.EquipmentModel import Equipment
from iMES.Model.DataBaseModels.NomenclatureGroupModel import NomenclatureGroup
from iMES.Model.DataBaseModels.ProductWasteModel import ProductWaste
from iMES.Model.DataBaseModels.ProductWeightModel import ProductWeight
from iMES.Model.DataBaseModels.ProductionDataModel import ProductionData
from iMES.Model.DataBaseModels.ShiftTaskModel import ShiftTask
from iMES.Model.ShiftTaskModels.ShiftTaskLoad import ShiftTaskLoader
from iMES.daemons import ProductDataMonitoring
import json
from flask_login import login_required


@socketio.on('UpdateShiftTask')
@login_required
def UpdateShiftTask(data):
    ip_addr = request.remote_addr
    date = 0
    socketio.emit("GetProgressStatus",
        data=json.dumps({ip_addr: '0'}),ensure_ascii=False, indent=4)
    old_task_list = (db.session.query(ShiftTask.Oid)
                    .where(ShiftTask.Equipment == current_tpa[ip_addr][0]).all())
    progress_max = 50
    i = 1
    for task in old_task_list:
        prod_data = (db.session.query(ProductionData.Oid)
                    .where(ProductionData.ShiftTask == task[0]).all())
        if len(prod_data) > 0:
            prod_data = prod_data[0][0]
            pw = db.session.query(ProductWaste).where(ProductWaste.ProductionData == prod_data).all()
            for p in pw:
                db.session.delete(p)
            pwt = db.session.query(ProductWeight).where(ProductWeight.ProductionData == prod_data).all()
            for pw in pwt:
                db.session.delete(pw)
            pd = db.session.query(ProductionData).where(ProductionData.ShiftTask == task[0]).all()
            for p in pd:
                db.session.delete(p)
            db.session.commit()
            db.session.query(ShiftTask).where(ShiftTask.Oid == task[0])
            db.session.commit()
        else:
            db.session.query(ShiftTask).where(ShiftTask.Oid == task[0]).delete()
            db.session.commit()
        socketio.emit("GetProgressStatus",
            data=json.dumps({ip_addr: int(0+((progress_max/len(old_task_list))*(i)))}),ensure_ascii=False, indent=4)
        i += 1
    nomenclature_group_oid = (db.session.query(Equipment.NomenclatureGroup)
                              .select_from(Equipment)
                              .where(Equipment.Oid == current_tpa[ip_addr][0]).all())
    if len(nomenclature_group_oid) > 0:
        nomenclature_group_oid = nomenclature_group_oid[0][0]
        nomenclature_group = (db.session.query(NomenclatureGroup.Code)
                              .select_from(NomenclatureGroup)
                              .where(NomenclatureGroup.Oid == nomenclature_group_oid)
                              .all())
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
    LoadShiftTask.ShiftTask_Update()
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
            new_shift_tasks = (db.session.query(ShiftTask.Oid)
                                .select_from(ShiftTask)
                                .where(ShiftTask.Equipment == current_tpa[ip_addr][0])
                                .all())
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