from iMES import db, app, TpaList
from flask import request

from iMES.Model.DataBaseModels.ProductionDataModel import ProductionData
from iMES.Model.DataBaseModels.ProductWasteModel import ProductWaste
from iMES.Model.DataBaseModels.MaterialModel import Material
from iMES.Model.DataBaseModels.EmployeeModel import Employee
from iMES.Model.DataBaseModels.UserModel import User

@app.route("/api/wastes")
def mes_ns_wastes():
    tpa_oid = request.args.getlist('oid')[0]
    selected_tpa = None
    wastes_json = {}
    for tpa in TpaList:
        if str(tpa[0]) == tpa_oid.lower():
            selected_tpa = tpa
            break
    if (selected_tpa is not None):
        if selected_tpa[2].shift_task_oid != '':
            production_data = db.session.query(ProductionData).where(
                ProductionData.ShiftTask == selected_tpa[2].shift_task_oid[0]).first()
            wastes_list = db.session.query(ProductWaste).where(
                ProductWaste.ProductionData == production_data.Oid
            ).all()
            for waste in wastes_list:
                material = None
                waste_type = 'Брак'
                if waste.Material is not None:
                    material = db.session.query(Material).where(Material.Oid == waste.Material).first()
                if waste.Type == 0:
                    waste_type = 'Отход'
                usr = db.session.query(User).where(User.Oid == waste.Creator).one_or_none()
                creator_name = ""
                if creator_name is not None:
                    creator_name = usr.get_name()
                wastes_json[str(waste.Oid)] = {
                    'type': str(waste_type),
                    'material': material.Name if material is not None else '',
                    'weight': str(waste.Weight),
                    'count': str(waste.Count),
                    'create_date': str(waste.CreateDate),
                    'creator': creator_name
                }
    return wastes_json
