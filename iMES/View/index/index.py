from iMES import socketio
from iMES import app
from iMES import UserController
from flask import redirect, render_template, request
from flask_login import login_required, login_user, logout_user,current_user
from iMES import login_manager
from iMES.Model.SQLManipulator import SQLManipulator
import json
from iMES import TpaList,current_tpa,user


@app.route("/")
def index():
    ip_addr = request.remote_addr  # Получение IP-адресса пользователя
    device_tpa = TpaList[ip_addr]
    # Код закоментирован до тех пор пока не появится авторизация
    # for filename in os.listdir("iMES/templates/Directum"):
    #     shutil.rmtree('iMES/templates/Directum/'+filename)
    # for filename in os.listdir("iMES/static/Directum"):
    #     shutil.rmtree('iMES/static/Directum/'+filename)
    # try:
    #     shutil.rmtree('iMES/static/Directum/images')
    # except:
    #     pass
    return render_template("index.html",
                           device_tpa = device_tpa,
                           current_tpa = current_tpa[ip_addr])

@app.route("/changeTpa", methods=["GET"])
def ChangeTPA():
    ip_addr = request.remote_addr
    current_tpa[ip_addr] = request.args.getlist('oid')[0], request.args.getlist('name')[0]
    return current_tpa

@app.route("/getTrend")
def GetTrend():
    trend = '[{ "y": "0", "x": "2022-07-01 07:01:08.637" },{ "y": "15", "x": "2022-07-01 14:00:08.570" }]'
    return trend

@app.route("/getPlan")
def GetPlan():
    plan = '[{ "y": "0", "x": "2022-07-01 07:00:00" },{ "y": "25", "x": "2022-07-01 19:00:00" }]'
    return plan

@app.route("/Auth/PassNumber=<string:passnumber>")
def Authorization(passnumber):
    terminal = request.remote_addr
    sql = f"""
    SELECT
         EMPL.LastName
        ,EMPL.FirstName
        ,EMPL.MiddleName
        ,USR.[UserName]
        ,USR.[CardNumber]
        ,RL.Name
        ,ITF.Name
    FROM [MES_Iplast].[dbo].[User] as USR,
        [MES_Iplast].[dbo].[Relation_UserRole] as RUR,
        [MES_Iplast].[dbo].[Relation_RoleInterface] as RRI,
        [MES_Iplast].[dbo].[Interface] as ITF,
        [MES_Iplast].[dbo].[Role] as RL,
        [MES_Iplast].[dbo].[Employee] as EMPL
    WHERE RUR.[User] = USR.Oid AND 
        RRI.[Role] = RUR.[Role] AND
        ITF.Oid = RRI.Interface AND
        RL.Oid = RUR.Role AND
        EMPL.Oid = USR.[Employee] AND
        USR.[CardNumber] = '{passnumber}'
        """

    data = SQLManipulator.SQLExecute(sql)
    if (len(data) == 0):
        return 'User undefinded'
    else:
        UserController.CountUsers += 1
        userdata = list(data[0])
        userdata.insert(0,UserController.CountUsers)
        sqlLastRole = f"""
                SELECT [Role].[Name]
                FROM [SavedRole],[User],[Role] 
                WHERE [User].CardNumber = '{userdata[5]}' AND
                    [SavedRole].[User] = [User].Oid AND
                    [SavedRole].[Role] = [Role].Oid
                """
        LastRole = SQLManipulator.SQLExecute(sqlLastRole)
        if(LastRole != []):
            user.role = {0:LastRole[0][0]}
        else:
            sqlUserRoles = f"""
                SELECT [Role].[Name]
                FROM [MES_Iplast].[dbo].[Relation_UserRole], [User],[Role]  
                WHERE [User].CardNumber = '{userdata[5]}' AND 
                    [Relation_UserRole].[User] = [User].Oid AND
                    [Relation_UserRole].[Role] = [Role].Oid
            """
            roles = SQLManipulator.SQLExecute(sqlUserRoles)
            user.role = {}
            for i in range(0,len(roles)):
                user.role[i] = roles[i][0]
        sqlCheckSavedRole = f"""
                DECLARE @device uniqueidentifier
                DECLARE @user uniqueidentifier
                SET @device = (SELECT Device.Oid FROM Device WHERE DeviceId = '{terminal}')
                SET @user = (SELECT [User].Oid FROM [User] WHERE [User].UserName = '{userdata[4]}')
                SELECT [Role].[Name] AS Роль
                FROM Employee, [Role], LastSavedRole, SavedRole, [User]

                WHERE LastSavedRole.Device = @device AND
                    SavedRole.Oid = LastSavedRole.SavedRole AND
                    SavedRole.[Role] = [Role].Oid AND
                    [User].Oid = SavedRole.[User] AND
                    Employee.Oid = [User].Employee AND
                    [User].Oid = @user
            """
        try:
            SavedRole = SQLManipulator.SQLExecute(sqlCheckSavedRole)[0][0]
        except:
            SavedRole = ''
            pass
        if SavedRole != '':
            user.role = SavedRole
            user.savedrole = True
        else:
            user.savedrole = False
        user.id = userdata[0]
        user.name = f"{userdata[1]} {userdata[2]} {userdata[3]}"
        user.username = userdata[4]
        user.CardNumber = userdata[5]
        user.interfaces = userdata[7]
        login_user(user)
        packet = {terminal:''}
        socketio.emit('Auth',json.dumps(packet,ensure_ascii=False,indent=4))
    return 'Authorization successful'

@login_manager.user_loader
def load_user(id):
    return user

@app.route('/Auth')
def Auth():
    ip_addr = request.remote_addr  # Получение IP-адресса пользователя
    device_tpa = TpaList[ip_addr]
    terminal = request.remote_addr
    login_user(user)
    packet = {terminal:current_user.role}
    print(current_user.role)
    if (current_user.role == 'Оператор'):
        return redirect('/operator')
    elif (current_user.role == 'Наладчик'):
        return redirect('/adjuster')
    else:
        return redirect('/menu')


@app.route('/login')
def login():
    return render_template('Show_error.html',error="Нет доступа, авторизируйтесь с помощью пропуска",ret='/', current_tpa = current_tpa[request.remote_addr])

@app.route('/logout')
@login_required
def logout():
    terminal = request.remote_addr
    sqlRemoveSaveUser = f"""
            DECLARE @user uniqueidentifier
            DECLARE @device uniqueidentifier
            /* Сам пользователь */
            SET @user = (SELECT [User].Oid FROM [User] WHERE [User].UserName = '{current_user.username}')
            /* Устройство на котором работает пользователь */
            SET @device = (SELECT [Device].Oid FROM [Device] WHERE DeviceId = '{terminal}')
        	DELETE FROM LastSavedRole WHERE LastSavedRole.Device = @device AND 
            LastSavedRole.SavedRole = (SELECT SavedRole.Oid 
                                    FROM SavedRole 
                                    WHERE SavedRole.[User] = @user AND 
                                            SavedRole.Device = @device)
            DELETE FROM SavedRole WHERE SavedRole.[User] = @user AND SavedRole.Device = @device
    """
    SQLManipulator.SQLExecute(sqlRemoveSaveUser)
    logout_user()
    return redirect('/')

@app.route('/logoutWithoutDeleteRoles')
@login_required
def logoutWithoutDeleteRoles():
    logout_user()
    return redirect('/')

@app.route('/getOperatorAndAdjuster')
def ReturnOperatorAndAdjuster():    
    ip = request.remote_addr
    sql = f"""
        DECLARE @device uniqueidentifier
        SET @device = (SELECT Device.Oid FROM Device WHERE DeviceId = '{ip}')
        SELECT (Employee.LastName +' '+ Employee.FirstName + ' ' + Employee.MiddleName) as ФИО
                ,[Role].[Name] AS Роль
        FROM Employee, [Role], LastSavedRole, SavedRole, [User]

        WHERE LastSavedRole.Device = @device AND
            SavedRole.Oid = LastSavedRole.SavedRole AND
            SavedRole.[Role] = [Role].Oid AND
            [User].Oid = SavedRole.[User] AND
            Employee.Oid = [User].Employee
      """
    sqlresult = SQLManipulator.SQLExecute(sql)
    OperatorAdjusterAtTerminals = {'Оператор':'','Наладчик':''}
    operator = ''
    adjuster = ''
    if(len(sqlresult) != 0):
        for employee in sqlresult:
            if employee[1] == 'Наладчик':
                adjuster = employee[0]
            if employee[1] == 'Оператор':
                operator = employee[0]
        OperatorAdjusterAtTerminals['Оператор'] = operator
        OperatorAdjusterAtTerminals['Наладчик'] = adjuster
    return json.dumps(OperatorAdjusterAtTerminals,ensure_ascii=False,indent=4)


@socketio.on(message='connecting')
def socket_connected(data):
    pass