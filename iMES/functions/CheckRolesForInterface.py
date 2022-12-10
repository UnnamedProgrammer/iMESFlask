from iMES.Model.SQLManipulator import SQLManipulator
from flask_login import current_user
from flask import render_template, request
from iMES import TpaList
from iMES import current_tpa


# Метод предназначенный для проверки доступных интерфейсов в зависимости от роли пользователя
def CheckRolesForInterface(RequiredInterface, DirectPageTemplate, somedata=""):
    ip_addr = request.remote_addr
    sql = f"""
    SELECT Interface.[Name]
    FROM [MES_Iplast].[dbo].[Relation_UserRole], [User],[Role],Interface,Relation_RoleInterface
    WHERE [User].CardNumber = '{current_user.CardNumber}' AND 
        [Relation_UserRole].[User] = [User].Oid AND
        [Relation_UserRole].[Role] = [Role].Oid AND
        [Role].Oid = Relation_RoleInterface.[Role] AND
        Relation_RoleInterface.Interface = Interface.Oid
    """
    sqlUserInterfaces = []
    sqlUserInterfaces = SQLManipulator.SQLExecute(sql)
    Interfaces = []
    for Interface in sqlUserInterfaces:
        Interfaces.append(Interface[0])
    if RequiredInterface in Interfaces:
        if (RequiredInterface == "Оператор"):
            current_user.role = "Оператор"
        if (RequiredInterface == "Наладчик"):
            current_user.role = "Наладчик"
        return render_template(f"{DirectPageTemplate}", device_tpa=TpaList[request.remote_addr], current_tpa=current_tpa[ip_addr], somedata=somedata)
    else:
        return render_template('Show_error.html', error="Недостаточно прав для данного интерфейса", ret='/', current_tpa=current_tpa[ip_addr])
