from iMES import socketio
from iMES import app
from iMES import UserController
from flask import redirect, render_template, request
from flask_login import login_required, login_user, logout_user, current_user
from iMES import login_manager
from iMES.Model.SQLManipulator import SQLManipulator
from iMES.Controller.IndexController import IndexController
import json
from iMES import TpaList, current_tpa, user
import requests
from datetime import datetime, timedelta

# Метод возвращающий главную страницу


@app.route("/")
def index():
    ip_addr = request.remote_addr  # Получение IP-адресса пользователя
    current_tpa[ip_addr][2].data_from_shifttask()
    # Проверяем нахожиться ли клиент в списке с привязанными к нему ТПА
    if ip_addr in TpaList.keys():
        # Выгружаем список привязанных ТПА к клиенту
        device_tpa = TpaList[ip_addr]
        # Запрос определяющий тип устройства клиента из бд, веб или терминал
        sql_GetDeviceType = f"""SELECT DeviceType.[Name]
                            FROM Device, DeviceType
                            WHERE Device.DeviceId = '{ip_addr}' AND
                                    Device.DeviceType = DeviceType.Oid
                            """
        user.device_type = SQLManipulator.SQLExecute(sql_GetDeviceType)[0][0]
        # Если устройство является веб то находим пользователя привязаннаго за устройством
        # И автоматически авторизуем его по его номеру карты
        if(user.device_type == 'Веб' and current_user.is_authenticated == False):
            sql_GetCardNumber = f"""
                                    SELECT [User].CardNumber
                                    FROM [User],Device WHERE 
                                    Device.DeviceId = '{ip_addr}' AND
                                    Device.[Name] = [User].UserName
                                """
            CardNumber = SQLManipulator.SQLExecute(sql_GetCardNumber)[0][0]
            from iMES import host, port
            r = requests.get(
                f"http://{host}:{str(port)}/Auth/PassNumber={CardNumber}/IP={request.remote_addr}")
            if(r.status_code == 200):
                login_user(user)
    # В противном случае уведомляем клиента о том что его нет в списках устройств
    else:
        return "Ваше устройство не находиться в списке допущенных, нет доступа."
    # Рендерим страницу
    return render_template("index.html",
                           device_tpa=device_tpa,
                           current_tpa=current_tpa[ip_addr])


# Метод возвращающий текущий ТПА в навбаре
@app.route("/changeTpa", methods=["GET"])
def ChangeTPA():
    ip_addr = request.remote_addr
    controller = IndexController(request.args.getlist(
        'oid')[0])
    controller.data_from_shifttask()
    current_tpa[ip_addr] = list((request.args.getlist(
        'oid')[0], request.args.getlist('name')[0], controller))
    return current_tpa


# Алия М
# Метод возвращающий данные о текущей выпущенной продукции на графике
# по запросу с главной страницы с помощью JS
# Запрос на этот роутинг выполняется их кода JS в index_template.html


@app.route("/getTrend")
def GetTrend():
    ip_addr = request.remote_addr
    # Массив и начальная точка, получаю начало и конец текущей смены
    sql_GetShiftTime = f"""
                            SELECT 
                                ShiftTask.Oid,
                                Shift.StartDate
                            FROM
                                Shift, ShiftTask
                            WHERE
                                Shift.Oid = ShiftTask.Shift
                        """
    ShiftTime = SQLManipulator.SQLExecute(sql_GetShiftTime)
    for shift_task in ShiftTime:
        # Если Oid смены в сменном задании совпадает с Oid смены в current_tpa
        if shift_task[0] == current_tpa[ip_addr][2].shift_task_oid:
            # Начальная точка назначается из БД (StartDate)
            trend = [{ "y": "0", "x": (shift_task[1].strftime("%Y-%m-%d %H:%M:%S.%f"))[:-3] }]
        elif current_tpa[ip_addr][2].shift_task_oid == '':
            trend = [{ "y": "0", "x": "0"},{ "y": "0", "x": "0"}]
            break
    # Подсчет выпущенных изделий (СОМНИТЕЛЬНО)
    y = 0 
    # Запрос на время и статус смыкания
    if (current_tpa[ip_addr][2].shift_task_oid != ''):
        sql_GetСlosures = f"""
                                SELECT [Date]
                                    ,[Status]
                                FROM [MES_Iplast].[dbo].[RFIDClosureData] as RCD, ShiftTask, Shift 
                                WHERE 
                                Controller = (SELECT RFIDEquipmentBinding.RFIDEquipment 
                                                    FROM RFIDEquipmentBinding, ShiftTask
                                                    WHERE ShiftTask.Equipment = RFIDEquipmentBinding.Equipment and 
                                                    ShiftTask.Oid = '{current_tpa[ip_addr][2].shift_task_oid}') AND
                                ShiftTask.Oid = '{current_tpa[ip_addr][2].shift_task_oid}' AND
                                Shift.Oid = ShiftTask.Shift AND
                                Date between Shift.StartDate AND Shift.EndDate

                                ORDER BY Date ASC
                            """
        Closures = SQLManipulator.SQLExecute(sql_GetСlosures)
        # Заполнение точками массива trend
        for i in Closures:
            # Если смыкание завершилось (status == 0), добавляется точка в массив
            if i[1] == False:
                closure_time = i[0].strftime("%Y-%m-%d %H:%M:%S.%f")
                y += 1
                trend.append({"y": str(y), "x": closure_time[:-3]})
    return json.dumps(trend)


# Метод возвращающий данные о плане выпускаемой продукции на графике
# по запросу с главной страницы с помощью JS
# Запрос на этот роутинг выполняется их кода JS в index_template.html


@app.route("/getPlan")
def GetPlan():
    ip_addr = request.remote_addr
    # План по продукции
    production_plan = current_tpa[ip_addr][2].production_plan
    # Плановый цикл
    cycle = current_tpa[ip_addr][2].cycle
    # Массив и начальная точка, получаю начало и конец текущей смены
    sql_GetShiftTime = f"""
                            SELECT 
                                ShiftTask.Oid,
                                Shift.StartDate,
                                Shift.EndDate
                            FROM
                                Shift, ShiftTask
                            WHERE
                                Shift.Oid = ShiftTask.Shift
                        """
    ShiftTime = SQLManipulator.SQLExecute(sql_GetShiftTime)
    time = datetime.now()
    for shift_task in ShiftTime:
        # Если Oid смены в сменном задании совпадает с Oid смены в current_tpa
        if shift_task[0] == current_tpa[ip_addr][2].shift_task_oid:
            # Записываем начало и конец смены
            time = shift_task[1]
            end_shift = shift_task[2]
            break
    # Массив и начальное значение
    plan = [{ "y": "0", "x": time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] }]
    for product in range(production_plan):
        # Прибавляем 1 цикл
        time += timedelta(seconds=100) #CYCLE !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # Если время превышает время окончания смены, не прибавлять данный цикл
        if time <= end_shift:
            plan.append({ "y": str(product), "x": time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] })
        else:
            break
    return json.dumps(plan)


# Метод создания пользователя для сессии при прикладываении пропуска.
# Отправляет устройству на котором прикладывается пропуск команду
# на переход по роутингу авторизации '/Auth'


@app.route("/Auth/PassNumber=<string:passnumber>")
def Authorization(passnumber):
    # Определяем адресс клиента
    terminal = request.remote_addr
    # Запрос на информацию о клиенте по его номеру карты
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
    # Отправляем запрос
    data = SQLManipulator.SQLExecute(sql)
    # Если записей с таким номером пропуска нет выводим ошибку
    if (len(data) == 0):
        return 'User undefinded'
    else:
        # Прибавляем к счетчику пользователей 1 для задания ID пользователяUserController.CountUsers += 1
        UserController.CountUsers += 1
        # Помещаем данные о клиенте в список для удобства
        userdata = list(data[0])
        # Помещаем в начало спика ID
        userdata.insert(0, UserController.CountUsers)
        # Запрос на сохраненные роли пользователя
        sqlLastRole = f"""
                SELECT [Role].[Name]
                FROM [SavedRole],[User],[Role] 
                WHERE [User].CardNumber = '{userdata[5]}' AND
                    [SavedRole].[User] = [User].Oid AND
                    [SavedRole].[Role] = [Role].Oid
                """
        LastRole = SQLManipulator.SQLExecute(sqlLastRole)
        if(LastRole != []):
            user.role = {0: LastRole[0][0]}
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
            for i in range(0, len(roles)):
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
        # Добавляем данные в экземпляр пользователя
        user.id = userdata[0]
        user.name = f"{userdata[1]} {userdata[2]} {userdata[3]}"
        user.username = userdata[4]
        user.CardNumber = userdata[5]
        user.interfaces = userdata[7]
        packet = {terminal: ''}
        # Отправляем в сокет сообщение о успешной авторизации
        socketio.emit('Auth', json.dumps(packet, ensure_ascii=False, indent=4))
    return 'Authorization successful'

# Метод предназначенный для авторизации без пропуска по запросу
# Большинство операций аналогичны методу авторизации с пропуском


@app.route("/Auth/PassNumber=<string:passnumber>/IP=<string:ipaddress>")
def AuthorizationWhithoutPass(passnumber, ipaddress):
    terminal = ipaddress
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
        userdata.insert(0, UserController.CountUsers)
        sqlLastRole = f"""
                SELECT [Role].[Name]
                FROM [SavedRole],[User],[Role] 
                WHERE [User].CardNumber = '{userdata[5]}' AND
                    [SavedRole].[User] = [User].Oid AND
                    [SavedRole].[Role] = [Role].Oid
                """
        LastRole = SQLManipulator.SQLExecute(sqlLastRole)
        if(LastRole != []):
            user.role = {0: LastRole[0][0]}
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
            for i in range(0, len(roles)):
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
        packet = {terminal: ''}
        socketio.emit('Auth', json.dumps(packet, ensure_ascii=False, indent=4))
    return 'Authorization successful'

# Метод загружающий пользователя по его ID в сессии при запросе login_manager'a


@login_manager.user_loader
def load_user(id):
    return user

# Метод аутентификации пользователя и редирект на страницы в зависимости от роли


@app.route('/Auth')
def Auth():
    ip_addr = request.remote_addr  # Получение IP-адресса пользователя
    device_tpa = TpaList[ip_addr]
    terminal = request.remote_addr
    login_user(user)
    packet = {terminal: current_user.role}

    if (current_user.role == 'Оператор'):
        return redirect('/operator')
    elif (current_user.role == 'Наладчик'):
        return redirect('/adjuster')
    elif (current_user.role == {0: 'Наладчик'}):
        return redirect('/adjuster')
    elif (current_user.role == {0: 'Оператор'}):
        return redirect('/operator')
    else:
        return redirect('/menu')

# Метод вызываемый при переходе на роутинг требующий авторизации будучи не авторизованным


@app.route('/login')
def login():
    return render_template('Show_error.html', error="Нет доступа, авторизируйтесь с помощью пропуска", ret='/', current_tpa=current_tpa[request.remote_addr])

# Метод выхода из аккаунта с откреплением от терминала


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

# Метод выхода из аккаунта без открепления от терминала


@app.route('/logoutWithoutDeleteRoles')
@login_required
def logoutWithoutDeleteRoles():
    logout_user()
    return redirect('/')

# Метод возвращающий текущего оператора и наладчика на устройстве
# Запрос на этот роутинг выполняется их кода JS в index_template.html


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
    OperatorAdjusterAtTerminals = {'Оператор': '', 'Наладчик': ''}
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
    return json.dumps(OperatorAdjusterAtTerminals, ensure_ascii=False, indent=4)

# Метод сокета срабатывающий при соединении


@socketio.on(message='GetDeviceType')
def socket_connected(data):
    ip_addr = request.remote_addr
    sql_GetDeviceType = f"""SELECT DeviceType.[Name]
                           FROM Device, DeviceType
                           WHERE Device.DeviceId = '{ip_addr}' AND
                                 Device.DeviceType = DeviceType.Oid
                        """
    device_type = SQLManipulator.SQLExecute(sql_GetDeviceType)[0][0]
    if(device_type == 'Веб'):
        data = 'Веб'
    else:
        data = 'Терминал'
    socketio.emit("DeviceType", json.dumps(
        {ip_addr: data}, ensure_ascii=False, indent=4))

@socketio.on(message="NeedUpdateMainWindowData")
def UpdateMainWindowData(data):
    ip_addr = request.remote_addr
    try:
        current_tpa[ip_addr][2].data_from_shifttask()
        MWData = {
                    ip_addr:{"PF":str(current_tpa[ip_addr][2].pressform),
                            "Product":str(current_tpa[ip_addr][2].product),
                            "Plan":str(current_tpa[ip_addr][2].production_plan),
                            "Fact":str(current_tpa[ip_addr][2].product_fact),
                            "PlanCycle":str(current_tpa[ip_addr][2].cycle),
                            "FactCycle":str(current_tpa[ip_addr][2].cycle_fact),
                            "PlanWeight":str(current_tpa[ip_addr][2].plan_weight),
                            "AverageWeight":str(current_tpa[ip_addr][2].average_weight),
                            "Shift":str(current_tpa[ip_addr][2].shift),
                            "Defective": 0}
                }
        socketio.emit("GetMainWindowData", data = json.dumps(
            MWData, ensure_ascii=False, indent=4))
    except:
        pass