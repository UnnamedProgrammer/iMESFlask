from string import ascii_letters
import socketio
from iMES import socketio
from iMES import app
from iMES import UserController
from flask import redirect, render_template, request
from iMES.Model.UserModel import UserModel
from flask_login import login_required, login_user, logout_user,current_user
from iMES import login_manager
from iMES.Model.SQLManipulator import SQLManipulator
import json
from iMES import TpaList

user = UserModel()

@app.route("/")
def index():
    # Код закоментирован до тех пор пока не появится авторизация
    # for filename in os.listdir("iMES/templates/Directum"):
    #     shutil.rmtree('iMES/templates/Directum/'+filename)
    # for filename in os.listdir("iMES/static/Directum"):
    #     shutil.rmtree('iMES/static/Directum/'+filename)
    # try:
    #     shutil.rmtree('iMES/static/Directum/images')
    # except:
    #     pass
    return render_template("index.html")

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
        print(LastRole)
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
        print(user.role)
        user.id = userdata[0]
        user.name = f"{userdata[1]} {userdata[2]} {userdata[3]}"
        user.username = userdata[4]
        user.CardNumber = userdata[5]
        user.interfaces = userdata[7]
        login_user(user)
        socketio.emit('AnswerAfterConnection',json.dumps(current_user.role,ensure_ascii=False,indent=4))
    return 'Authorization successful'

@login_manager.user_loader
def load_user(id):
    return user

@app.route('/login')
def login():
    return render_template('Show_error.html',error="Нет доступа, авторизируйтесь с помощью пропуска",ret='/')

@app.route('/logout')
@login_required
def logout():
    terminal = request.remote_addr
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

@socketio.on(message='getTpaList')
def socket_connected(data):
    socketio.emit('TpaList',json.dumps(TpaList[data['ipaddress']], ensure_ascii=False,indent=4))