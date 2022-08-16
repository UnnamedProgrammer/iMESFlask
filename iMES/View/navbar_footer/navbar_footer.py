from iMES import app
from flask import request, redirect, render_template
from flask_login import login_required, current_user
from iMES.Model.SQLManipulator import SQLManipulator
from iMES import OperatorAdjusterAtTerminals

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

            SET @newrole = (SELECT Role.Oid FROM Role WHERE Role.Name = '{current_user.role}')
            SET @user = (SELECT [User].Oid FROM [User] WHERE [User].UserName = '{current_user.username}')
            SET @device = (SELECT [Device].Oid FROM [Device] WHERE DeviceId = '{terminal}')
            SET @savedrole = (
                SELECT SavedRole.Oid
                FROM SavedRole 
                WHERE SavedRole.Device = @device AND 
                SavedRole.[Role] = @newrole
            )
            SET @olduser = (SELECT SavedRole.[User] FROM SavedRole WHERE SavedRole.Oid = @savedrole)
            SET @oldrole = (SELECT SavedRole.[Role] FROM SavedRole WHERE SavedRole.Oid = @savedrole)
            if @savedrole IS NULL
                INSERT INTO SavedRole (Oid,[User],[Role],Device) VALUES (NEWID(),@user,@newrole,@device)
            if @savedrole IS NOT NULL
                select @savedrole,@olduser,@user
                if @olduser = @user and @newrole != @oldrole
                    UPDATE SavedRole SET SavedRole.[Role] = @newrole WHERE SavedRole.Oid = @savedrole
                if @olduser != @user and @newrole != @oldrole
                    UPDATE SavedRole SET SavedRole.[User] = @user, SavedRole.[Role] = @newrole WHERE SavedRole.Oid = @savedrole
                if @olduser != @user and @newrole = @oldrole
                    UPDATE SavedRole SET SavedRole.[User] = @user WHERE SavedRole.Oid = @savedrole
            """
        SQLManipulator.SQLExecute(sql)
        terminal = request.remote_addr
        if (current_user.role == "Оператор"):
            if (OperatorAdjusterAtTerminals[terminal]['Наладчик'] == current_user.name):
                OperatorAdjusterAtTerminals[terminal]['Наладчик'] = ''
            OperatorAdjusterAtTerminals[terminal]['Оператор'] = current_user.name
        if (current_user.role == "Наладчик"):
            if (OperatorAdjusterAtTerminals[terminal]['Оператор'] == current_user.name):
                OperatorAdjusterAtTerminals[terminal]['Оператор'] = ''
            OperatorAdjusterAtTerminals[terminal]['Наладчик'] = current_user.name
    else:
        return render_template('Show_error.html',error="Недостаточно прав для данного интерфейса",ret='/menu')
    return redirect('/')

