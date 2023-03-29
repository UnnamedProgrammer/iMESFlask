from iMES.Model.DataBaseModels.LastSavedRoleModel import LastSavedRole
from iMES.Model.DataBaseModels.SavedRoleModel import SavedRole
from iMES.Model.DataBaseModels.DeviceModel import Device
from iMES.Model.DataBaseModels.RoleModel import Role
from iMES import db
from flask_login import current_user
from flask import request

def rewrite_role(role_name: str):
    '''Перезаписывает текущую роль пользователя при переходе по вкладкам 
       оператор, наладчик и т.д
    '''
    ip_addr = request.remote_addr
    last_save_role = None
    old_saved_role = None
    old_saved_role = db.session.query(SavedRole).where(
        SavedRole.User == current_user.Oid
    ).where(
        SavedRole.Device == db.session.query(Device.Oid).where(
            Device.DeviceId == ip_addr
        ).one_or_none()[0]
    ).one_or_none()

    if old_saved_role != None:
        last_save_role = db.session.query(LastSavedRole).where(
            LastSavedRole.Device == db.session.query(Device.Oid).where(
                Device.DeviceId == ip_addr
            ).one_or_none()[0]
        ).where(
            LastSavedRole.SavedRole == old_saved_role.Oid
        ).one_or_none()

    if old_saved_role != None and last_save_role == None:
        # Удаляем старую роль
        db.session.delete(old_saved_role)
        # Записываем новую текущую роль
        saved_role = SavedRole()
        saved_role.Device = db.session.query(Device.Oid).where(
            Device.DeviceId == ip_addr).one_or_none()[0]
        saved_role.User = current_user.Oid
        saved_role.Role = db.session.query(Role.Oid).where(
            Role.Name == role_name
        ).one_or_none()[0]
        db.session.add(saved_role)
        db.session.commit()
    else:
        # Записываем новую текущую роль
        if last_save_role == None:
            saved_role = SavedRole()
            saved_role.Device = db.session.query(Device.Oid).where(
                Device.DeviceId == ip_addr).one_or_none()[0]
            saved_role.User = current_user.Oid
            saved_role.Role = db.session.query(Role.Oid).where(
                Role.Name == role_name
            ).one_or_none()[0]
            db.session.add(saved_role)
            db.session.commit()
        else:
            return