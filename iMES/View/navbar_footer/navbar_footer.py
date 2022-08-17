from iMES import app
from flask import request, redirect, render_template
from flask_login import login_required, current_user
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
                /* Находим последнее значение роли пользователя */
                SET @oldrole = (SELECT SavedRole.[Role] FROM SavedRole WHERE SavedRole.Oid = @savedrole)
                /* Находим кто был сохранён под данной ролью */
                SET @olduser = (SELECT SavedRole.[User] FROM SavedRole WHERE SavedRole.Oid = @savedrole)
                /*Если пользователь до этого не был привязан к какой-либо роли на устройстве, т.е @savedrole = NULL*/
                DECLARE @newSavedRoleOid uniqueidentifier
                if @savedrole IS NULL
                    BEGIN
                        /*То сохраняем его в таблицы SavedRole и LastSavedRole */
                        INSERT INTO SavedRole (Oid,[User],[Role],Device) VALUES (NEWID(),@user,@newrole,@device)
                        SET @newSavedRoleOid = (SELECT SavedRole.Oid 
                                                FROM SavedRole 
                                                WHERE SavedRole.Device = @device AND 
                                                    SavedRole.[User] = @user AND 
                                                    SavedRole.[Role] = @newrole)
                        INSERT INTO LastSavedRole (Device,SavedRole) VALUES (@device,@newSavedRoleOid)
                    END
                /*Если найдена закрепленная роль на устройстве*/
                if @savedrole IS NOT NULL
                BEGIN
                    /* Если это тот же пользователь что и был сохранён, но роль у него другая*/
                    IF @olduser = @user and @newrole != @oldrole
                    BEGIN
                        /* Удаляем записи пользователя и создаём новые записи с новой ролью */
                        DELETE FROM LastSavedRole WHERE LastSavedRole.SavedRole = @savedrole
                        DELETE FROM SavedRole WHERE SavedRole.Oid = @savedrole
                        INSERT INTO SavedRole (Oid,[User],[Role],Device) VALUES (NEWID(),@user,@newrole,@device)
                        SET @newSavedRoleOid = (SELECT SavedRole.Oid 
                                        FROM SavedRole 
                                        WHERE SavedRole.Device = @device AND 
                                                SavedRole.[User] = @user AND 
                                                SavedRole.[Role] = @newrole)
                        INSERT INTO LastSavedRole (Device,SavedRole) VALUES (@device,@newSavedRoleOid)
                        RETURN
                    END
                    /* Если пользователь другой и роль у него другая*/
                    IF @olduser != @user and @newrole != @oldrole
                    BEGIN
                        DELETE FROM LastSavedRole WHERE LastSavedRole.SavedRole = @savedrole
                        /*Меняем в записи пользователя и роль*/
                        UPDATE SavedRole SET SavedRole.[User] = @user, SavedRole.[Role] = @newrole WHERE SavedRole.Oid = @savedrole
                        RETURN
                    END
                    /* Если пользователь другой но роль у него та же что была у другого ранее сохранённого пользователя*/
                    IF @olduser != @user and @newrole = @oldrole
                    BEGIN
                        DELETE FROM LastSavedRole WHERE LastSavedRole.SavedRole = @savedrole
                        /*Меняем пользователя*/
                        UPDATE SavedRole SET SavedRole.[User] = @user WHERE SavedRole.Oid = @savedrole
                        RETURN
                    END
                    /* Если пользователь пытается сохраниться под одной и той же ролью снова */
                    IF @olduser = @user AND @newrole = @oldrole
                    BEGIN
                        /* То ничего не делаем ибо он уже привязан */
                        RETURN
                    END
                    INSERT INTO LastSavedRole (Device,SavedRole) VALUES (@device,@savedrole)
                END
            """
        SQLManipulator.SQLExecute(sql)
    else:
        return render_template('Show_error.html',error="Недостаточно прав для данного интерфейса",ret='/menu')
    return redirect('/')

