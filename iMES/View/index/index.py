import socketio
from iMES import socketio
from iMES import app
from iMES import UserController
from flask import redirect, render_template, request
from flask_socketio import SocketIO, emit
from iMES.Model.UserModel import UserModel
from flask_login import login_required, login_user, logout_user,current_user
from iMES import login_manager
from iMES.Model.SQLManipulator import SQLManipulator
import json

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
        UserModel.id = userdata[0]
        UserModel.name = f"{userdata[1]} {userdata[2]} {userdata[3]}"
        UserModel.username = userdata[4]
        UserModel.CardNumber = userdata[5]
        UserModel.role = userdata[6]
        UserModel.interfaces = userdata[7]
        user = UserModel()
        login_user(user=user)
        socketio.emit('AnswerAfterConnection',current_user.role)
    return 'Logged'

@login_manager.user_loader
def load_user(id):
    return UserModel

@app.route('/login')
def login():
    return render_template('Show_error.html',error="Доступ запрещен, приложите ключ карту",ret='/')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    UserController.CountUsers -= 1
    return redirect('/')

@app.route('/getOperatorAndAdjuster')
def ReturnOperatorAndAdjuster():    
    TerminalSavedRoles = {}
    devices = SQLManipulator.SQLExecute('select * from [MES_Iplast].[dbo].[Device]')
    print(devices)
    for device in devices:
        operator = ''
        Adjuster = '' 
        users = SQLManipulator.SQLExecute(f'''
                                SELECT Employee.LastName,
                                    Employee.FirstName,
                                    Employee.MiddleName,
                                    [Role].Name
                                FROM [MES_Iplast].[dbo].[SavedRole],
                                    [MES_Iplast].[dbo].Device,
                                    [MES_Iplast].[dbo].[User],
                                    [MES_Iplast].[dbo].[Role],
                                    [MES_Iplast].[dbo].[Employee]
                                WHERE Device.DeviceId = '{device[3]}' AND
                                    SavedRole.Device = Device AND
                                    SavedRole.[Role] = [Role].Oid AND
                                    SavedRole.[User] = [User].Oid AND
                                    Employee.Oid = [User].Employee
                                ''')                   
        for user in users:
            if(user[3] == 'Оператор'):
                operator = f'{user[0]} {user[1]} {user[2]}'
            if(user[3] == 'Наладчик'):
                Adjuster = f'{user[0]} {user[1]} {user[2]}'
        ip = request.remote_addr
        print(ip)
        if (operator != '' and Adjuster != ''):                             
            TerminalSavedRoles[device[3]] = {'Оператор':operator,'Наладчик': Adjuster}
        if (operator == '' and Adjuster == ''):                             
            TerminalSavedRoles[device[3]] = {'Оператор':'','Наладчик': ''}
        if (operator != '' and Adjuster == ''):                             
            TerminalSavedRoles[device[3]] = {'Оператор':operator,'Наладчик': ''}
        if (operator == '' and Adjuster != ''):                             
            TerminalSavedRoles[device[3]] = {'Оператор':'','Наладчик': Adjuster}
    return json.dumps(TerminalSavedRoles[ip],ensure_ascii=False,indent=4)


@socketio.on(message='connecting')
def socket_connected(data):
    pass