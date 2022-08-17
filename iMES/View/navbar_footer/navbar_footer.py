from iMES import app
from flask import request, redirect, render_template
from flask_login import login_required, current_user, logout_user
from iMES.Model.SQLManipulator import SQLManipulator

# Процедура кнопки "Выход с сохранением"
@app.route('/exitwithsave')
@login_required
def ExitWithSave():
    sql = f"""
    SELECT Interface.[Name]
    FROM [MES_Iplast].[dbo].[Relation_UserRole], [User],[Role],Interface,Relation_RoleInterface
    WHERE [User].CardNumber = '{current_user.CardNumber}' AND 
        [Relation_UserRole].[User] = [User].Oid AND
        [Relation_UserRole].[Role] = [Role].Oid AND
        [Role].Oid = Relation_RoleInterface.[Role] AND
        Relation_RoleInterface.Interface = Interface.Oid
    """
    terminal = request.remote_addr
    sqlUserInterfaces = []
    sqlUserInterfaces = SQLManipulator.SQLExecute(sql)
    Interfaces = []
    for Interface in sqlUserInterfaces:
        Interfaces.append(Interface[0])
    if current_user.role in Interfaces:
        sql = f"""
                DECLARE @newrole uniqueidentifier
                DECLARE @oldrole uniqueidentifier
                DECLARE @user uniqueidentifier
                DECLARE @savedrole uniqueidentifier
                DECLARE @device uniqueidentifier
                DECLARE @olduser uniqueidentifier
                DECLARE @newsavedrole uniqueidentifier
                /* Новая роль пользователя */
                SET @newrole = (SELECT Role.Oid FROM Role WHERE Role.Name = '{current_user.role}')
                /* Сам пользователь */
                SET @user = (SELECT [User].Oid FROM [User] WHERE [User].UserName = '{current_user.username}')
                /* Устройство на котором работает пользователь */
                SET @device = (SELECT [Device].Oid FROM [Device] WHERE DeviceId = '{terminal}')
                /*Ищем последнюю сохранённую роль пользователя*/
                SET @savedrole = (
                    SELECT SavedRole.Oid
                    FROM SavedRole 
                    WHERE SavedRole.Device = @device AND SavedRole.[Role] = @newrole
                )
                IF @savedrole IS NULL
                BEGIN
                    DELETE FROM LastSavedRole WHERE LastSavedRole.Device = @device AND 
                    LastSavedRole.SavedRole = (SELECT SavedRole.Oid 
                                            FROM SavedRole 
                                            WHERE SavedRole.[User] = @user AND 
                                                    SavedRole.Device = @device)
                    DELETE FROM SavedRole WHERE SavedRole.[User] = @user AND SavedRole.Device = @device
                    INSERT INTO SavedRole (Oid,[User],[Role],Device) VALUES (NEWID(),@user,@newrole,@device)
                    SET @newsavedrole = (SELECT SavedRole.Oid 
                                        FROM SavedRole 
                                        WHERE SavedRole.[User] = @user AND 
                                            SavedRole.[Role] = @newrole AND 
                                            SavedRole.Device = @device)
                    INSERT INTO LastSavedRole (Device,SavedRole) VALUES (@device,@newsavedrole)
                    RETURN
                END
                IF @savedrole IS NOT NULL
                BEGIN
                    DELETE FROM LastSavedRole WHERE LastSavedRole.Device = @device AND 
                    LastSavedRole.SavedRole = (SELECT SavedRole.Oid 
                                            FROM SavedRole 
                                            WHERE SavedRole.[User] = @user AND 
                                                    SavedRole.Device = @device)
                    DELETE FROM SavedRole WHERE SavedRole.[User] = @user AND SavedRole.Device = @device
                    DELETE FROM LastSavedRole WHERE LastSavedRole.SavedRole = @savedrole
                    DELETE FROM SavedRole WHERE SavedRole.[Role] = @newrole AND 
                                                SavedRole.Device = @device
                    INSERT INTO SavedRole (Oid,[User],[Role],Device) VALUES (NEWID(),@user,@newrole,@device)
                    SET @newsavedrole = (SELECT SavedRole.Oid 
                                        FROM SavedRole 
                                        WHERE SavedRole.[User] = @user AND 
                                            SavedRole.[Role] = @newrole AND 
                                            SavedRole.Device = @device)
                    INSERT INTO LastSavedRole (Device,SavedRole) VALUES (@device,@newsavedrole)
                    RETURN
                END
            """
        SQLManipulator.SQLExecute(sql)
    else:
        return render_template('Show_error.html',error="Недостаточно прав для данного интерфейса",ret='/menu')
    logout_user()
    return redirect('/')

