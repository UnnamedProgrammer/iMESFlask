from iMES import db
from flask_login import current_user
from flask import render_template, request
from iMES import TpaList
from iMES import current_tpa
from iMES.Model.DataBaseModels.Relation_RoleInterfaceModel import Relation_RoleInterface
from iMES.Model.DataBaseModels.InterfaceModel import Interface
from iMES.Model.DataBaseModels.RoleModel import Role

# Метод предназначенный для проверки доступных интерфейсов в зависимости от роли пользователя
def CheckRolesForInterface(RequiredInterface, DirectPageTemplate, somedata=""):
    ip_addr = request.remote_addr
    available_interfaces = []
    for role in current_user.Roles['Roles']:
        interface = db.session.query(Interface.Name).where(
            Interface.Oid == db.session.query(
                Relation_RoleInterface.Interface).where(
                    Relation_RoleInterface.Role == db.session.query(Role.Oid).where(
                        Role.Name == role
                    ).one_or_none()[0]
            ).one_or_none()[0]).one_or_none()
        if interface is not None:
            available_interfaces.append(interface.Name)
    if RequiredInterface in available_interfaces:
        return render_template(f"{DirectPageTemplate}", device_tpa=TpaList[ip_addr], current_tpa=current_tpa[ip_addr], somedata=somedata)
    else:
        return render_template('Show_error.html', error="Недостаточно прав для данного интерфейса", ret='/', current_tpa=current_tpa[ip_addr])
