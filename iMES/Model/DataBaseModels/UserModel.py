from iMES import db
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER, BIT, DATETIME
from sqlalchemy import ForeignKey, text
from sqlalchemy.orm import mapped_column
from flask_login import UserMixin
from iMES.Model.DataBaseModels.LastSavedRoleModel import LastSavedRole
from iMES.Model.DataBaseModels.SavedRoleModel import SavedRole
from iMES.Model.DataBaseModels.Relation_UserRoleModel import Relation_UserRole
from iMES.Model.DataBaseModels.RoleModel import Role
from iMES.Model.DataBaseModels.DeviceModel import Device
from iMES.Model.DataBaseModels.EmployeeModel import Employee

class User(db.Model, UserMixin):
    __tablename__ = "User"
    Oid = db.Column(UNIQUEIDENTIFIER, primary_key=True, server_default=text("newid()"), nullable=False)
    Employee = mapped_column(ForeignKey('Employee.Oid'), nullable=True)
    UserName = db.Column(db.String, nullable=False)
    Password = db.Column(db.String, nullable=True)
    CardNumber = db.Column(db.String, nullable=True)
    isActive = db.Column(BIT, nullable=False)
    Creator = mapped_column(ForeignKey('User.Oid'), nullable=True)
    CreateDate = db.Column(DATETIME, nullable=True)
    ModifyDate = db.Column(DATETIME, nullable=True)
    Roles = []
    CurrentRole = ""
    
    def __init__(self):
        self.name = self.get_name()

    def get_id(self):
        '''Возвращаем Oid пользователя для получения данных о пользователе из БД'''
        return self.Oid
    
    def get_name(self):
        Emp = db.session.query(Employee).where(Employee.Oid == self.Employee).one_or_none()
        if Emp != None:
            return f"{Emp.LastName} {Emp.FirstName} {Emp.MiddleName}"
        else:
            return "Undefinded"
    
    def get_roles(self, device_ip):
        '''Возвращает список сохранённых ролей либо доступных ролей'''
        # Сначала проверяем сохранена ли какая-либо роль у пользователя
        saved_roles_list = {'SavedRoles': None,'Roles': []}
        device = db.session.query(Device.Oid).where(Device.DeviceId == device_ip).one_or_none()[0]
        sv_role = db.session.query(LastSavedRole.SavedRole).where(LastSavedRole.Device == device).one_or_none()
        last_saved_role = None
        if sv_role != None:
            last_saved_role = db.session.query(
                Role).where(
                    Role.Oid ==db.session.query(
                        SavedRole.Role).where(
                            SavedRole.Oid == sv_role[0]).one_or_none()[0]).one_or_none()
        # Если сохранена добавляем её в словарь
        if last_saved_role != None:
            saved_roles_list['SavedRoles'] = last_saved_role.Name

        # Ищем все доступные роли пользователя и так же добавляем в словарь
        roles_oids = db.session.query(Relation_UserRole.Role).where(
            Relation_UserRole.User == self.Oid
        ).all()
        for role_oid in roles_oids:
            role = db.session.query(Role).where(Role.Oid == role_oid[0]).one_or_none()
            if role is not None:
                saved_roles_list['Roles'].append(role.Name)
        self.Roles = saved_roles_list

