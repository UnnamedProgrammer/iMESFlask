from iMES import app, db
from flask import request, redirect
from flask_login import login_required, current_user
from iMES.Model.DataBaseModels.LastSavedRoleModel import LastSavedRole
from iMES.Model.DataBaseModels.SavedRoleModel import SavedRole
from iMES.Model.DataBaseModels.DeviceModel import Device



# Процедура кнопки "Выход с сохранением"
# Закрепляет пользователя за выбранной ролью
@app.route('/exitwithsave')
@login_required
def ExitWithSave():
    ip_addr = request.remote_addr
    old_last_save_role = db.session.query(LastSavedRole).where(
            LastSavedRole.Device == db.session.query(Device.Oid).where(
                Device.DeviceId == ip_addr
        ).one_or_none()[0]
    ).one_or_none()
    if old_last_save_role == None:
        last_saved_role = LastSavedRole()
        last_saved_role.Device = db.session.query(Device.Oid).where(
            Device.DeviceId == ip_addr
        ).one_or_none()[0]
        last_saved_role.SavedRole = db.session.query(SavedRole.Oid).where(
            SavedRole.User == current_user.Oid
        ).where(
            SavedRole.Device == db.session.query(Device.Oid).where(
                Device.DeviceId == ip_addr
            ).one_or_none()[0]
        ).one_or_none()[0]
        db.session.add(last_saved_role)
        db.session.commit()
    return redirect("/")
