from iMES import db, TpaList
from iMES.Model.DataBaseModels.DeviceModel import Device
from iMES.Model.DataBaseModels.EquipmentModel import Equipment
from iMES.Model.DataBaseModels.Relation_DeviceEquipmentModel import Relation_DeviceEquipment

def device_tpa(ip_addr):
    device = db.session.query(Device).where(Device.DeviceId == ip_addr).one_or_none()
    if device is None:
        return
    available_tpa = Equipment.query.where(
                Relation_DeviceEquipment.Device == device.Oid).where(
                    Equipment.Oid == Relation_DeviceEquipment.Equipment).all()
    user_tpa_list = []
    for tpa in TpaList:
        for a_tpa in available_tpa:
            if str(a_tpa.Oid) == tpa[0]:
                user_tpa_list.append(tpa)
    
    return user_tpa_list