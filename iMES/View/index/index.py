from asyncio.log import logger
from iMES import socketio
from iMES import app
from iMES import UserController
from flask import redirect, render_template, request
from flask_login import login_required, login_user, logout_user, current_user
from iMES import login_manager
from iMES.Model.SQLManipulator import SQLManipulator
import json
from iMES import TpaList, current_tpa, user_dict
import requests
from datetime import datetime, timedelta
from requests.adapters import HTTPAdapter,Retry
import requests, urllib3

from iMES.Model.UserModel import UserModel
# Метод возвращающий главную страницу

urllib3.disable_warnings()

@app.route("/")
def index():
    ip_addr = request.remote_addr  # Получение IP-адресса пользователя
    current_tpa[ip_addr][2].data_from_shifttask()
    current_tpa[ip_addr][2].pressform = current_tpa[ip_addr][2].update_pressform()
    current_tpa[ip_addr][2].Check_pressform()
    show_notify = False
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
        device_type = SQLManipulator.SQLExecute(sql_GetDeviceType)[0][0]
        if len(device_type) > 0:
            # Если устройство является веб то находим пользователя привязаннаго за устройством
            # И автоматически авторизуем его по его номеру карты
            if device_type == "Веб":
                sql_GetCardNumber = f"""
                            SELECT [User].CardNumber
                            FROM [User],Device WHERE 
                            Device.DeviceId = '{ip_addr}' AND
                            Device.[Name] = [User].UserName
                        """
                CardNumber = SQLManipulator.SQLExecute(sql_GetCardNumber)[0][0]
                is_authorized = False
                for key in user_dict.keys():
                    if user_dict[key].CardNumber == CardNumber:
                        is_authorized = True
                if not is_authorized:
                    from iMES import host, port
                    session = requests.Session()
                    retry = Retry(connect=3,backoff_factor=0.5)
                    adapter = HTTPAdapter(max_retries=retry)
                    session.mount('http://', adapter)
                    session.mount('https://', adapter)
                    headers={
                    'Referer': f'http://{host}:{str(port)}/Auth/PassNumber={CardNumber}/IP={request.remote_addr}',
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36'
                    }
                    r = session.get(
                        f"http://{host}:{str(port)}/Auth/PassNumber={CardNumber}/IP={request.remote_addr}",headers=headers,verify=False)
                    if r.status_code == 200:
                        for key in list(user_dict.keys()):
                            if user_dict[key].CardNumber == CardNumber:
                                login_user(user_dict[key])            
        else:
            return "Undefinded user, access denied"
    # Рендерим страницу
    return render_template("index.html",
                           device_tpa=device_tpa,
                           current_tpa=current_tpa[ip_addr])


# Метод возвращающий текущий ТПА в навбаре
@app.route("/changeTpa", methods=["GET"])
def ChangeTPA():
    ip_addr = request.remote_addr
    for tpa in TpaList[ip_addr]:
        if tpa['Oid'] == request.args.getlist('oid')[0]:
            current_tpa[ip_addr] = [request.args.getlist('oid')[0], request.args.getlist('name')[0], tpa['Controller']]
            break
    return {}


# Метод возвращающий данные о плане и факте выпускаемой продукции на графике
# по запросу с сокета в файле Graph.js


@socketio.on(message = "getTrendPlanData")
def GetPlan(data):
    ip_addr = request.remote_addr
    # Проверяем есть ли сменное задание на ТП
    if len(current_tpa[ip_addr][2].shift_task_oid) == 0:
        pass
    else:
        # Получаем Oid смены 
        sql_GetShiftOid = f"""
                                SELECT TOP(1) ShiftTask.Shift
                                FROM Shift, ShiftTask
                                WHERE ShiftTask.Oid = '{current_tpa[ip_addr][2].shift_task_oid[0]}'
                            """
        ShiftOid = SQLManipulator.SQLExecute(sql_GetShiftOid)[0][0]
        
        #-------------TREND
        # Массив и начальная точка, получаю начало и конец текущей смены
        sql_GetShiftInfo = f"""
                                SELECT 
                                    ShiftTask.Oid,
                                    Shift.StartDate,
                                    Shift.EndDate,
                                    ShiftTask.ProductCount,
                                    ShiftTask.Cycle,
                                    ShiftTask.Shift,
                                    ShiftTask.Product
                                FROM
                                    Shift, ShiftTask
                                WHERE
                                    Shift.Oid = ShiftTask.Shift and ShiftTask.Equipment = '{current_tpa[ip_addr][2].tpa}' and ShiftTask.Shift = '{ShiftOid}'
                            """
        ShiftInfo = SQLManipulator.SQLExecute(sql_GetShiftInfo)
        for shift_task in ShiftInfo:
            # Начальная точка назначается из БД (StartDate)
            trend = [{"y": "0", "x": (shift_task[1].strftime("%Y-%m-%d %H:%M:%S.%f"))[:-3]}]
            break
        # Подсчет выпущенных изделий (СОМНИТЕЛЬНО)
        y = 0
        # Запрос на время и статус смыкания
        if (len(current_tpa[ip_addr][2].shift_task_oid) > 0):
            sql_GetСlosures = f"""
                                    SELECT [Date]
                                        ,[Status]
                                    FROM [MES_Iplast].[dbo].[RFIDClosureData] as RCD, ShiftTask, Shift 
                                    WHERE 
                                    Controller = (SELECT RFIDEquipmentBinding.RFIDEquipment 
                                                        FROM RFIDEquipmentBinding, ShiftTask
                                                        WHERE ShiftTask.Equipment = RFIDEquipmentBinding.Equipment and 
                                                        ShiftTask.Oid = '{current_tpa[ip_addr][2].shift_task_oid[0]}') AND
                                    ShiftTask.Oid = '{current_tpa[ip_addr][2].shift_task_oid[0]}' AND
                                    Shift.Oid = ShiftTask.Shift AND
                                    Date between Shift.StartDate AND Shift.EndDate

                                    ORDER BY Date ASC
                                """
            Closures = SQLManipulator.SQLExecute(sql_GetСlosures)
            # Заполнение точками массива trend
            for i in Closures:
                # Если смыкание завершилось (status == 0), добавляется точка в массив
                if i[1] == True:
                    closure_time = i[0].strftime("%Y-%m-%d %H:%M:%S.%f")
                    y += 1
                    trend.append({"y": str(current_tpa[ip_addr][2].socket_count * y), "x": closure_time[:-3]})

        #-------------PLAN
        # Если сменное задание одно
        if len(ShiftInfo) == 1:
            # Записываем начало и конец смены
            time = ShiftInfo[0][1]
            end_shift = ShiftInfo[0][2]
            # Массив и начальное значение
            plan = [{"y": "0", "x": time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]}]
            for closure in range(ShiftInfo[0][3]):
                time += timedelta(seconds=int(ShiftInfo[0][4]))
                if time < end_shift:
                    plan.append({"y": str(current_tpa[ip_addr][2].socket_count * closure), "x": time.strftime(
                        "%Y-%m-%d %H:%M:%S.%f")[:-3]})
                # Если время равно времени окончания смены, прибавить цикл и выйти из for
                elif time == end_shift:
                    plan.append({"y": str(current_tpa[ip_addr][2].socket_count * closure), "x": time.strftime(
                        "%Y-%m-%d %H:%M:%S.%f")[:-3]})
                    break
                # Если время превышает время окончания смены, не прибавлять данный цикл
                else:
                    # Пустая точка на конце смены, чтобы график был отрисован до ее конца
                    plan.append({"y": None, "x": end_shift.strftime(
                        "%Y-%m-%d %H:%M:%S.%f")[:-3]})
                    break
        # Если сменных заданий несколько
        elif len(ShiftInfo) > 1:
            # Записываем начало и конец смены
            time = ShiftInfo[0][1]
            end_shift = ShiftInfo[0][2]
            # Переменная для подсчета суммы общего времени на производство
            shift_times = 0
            # Переменная для подсчета кол-ва сменных заданий с разными продуктами
            product_count = 0
            # Подсчет времени на все сменные задания и кол-ва сменных заданий с разными продуктами
            for shift_task in range(0, len(ShiftInfo)-1):
                shift_times += int(ShiftInfo[shift_task][3])*int(ShiftInfo[shift_task][4])
                if ShiftInfo[shift_task][6] == ShiftInfo[shift_task][6]:
                    product_count += 1
            # Расчитываем оставшееся время на простои
            if shift_times >= 43200:
                downtime = 0
            else:
                downtime = 43200 - shift_times
            # Массив и начальное значение
            plan = [{"y": "0", "x": time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]}]
            closure_summ = 0
            # Перебираем сменное задание
            for shift_task in range(0, len(ShiftInfo)):
                for closure in range(1, ShiftInfo[shift_task][3]+1):
                    closure_summ += 1
                    time += timedelta(seconds=int(ShiftInfo[shift_task][4]))
                    if time < end_shift:
                        plan.append({"y": closure_summ, "x": time.strftime(
                            "%Y-%m-%d %H:%M:%S.%f")[:-3]})
                    elif time == end_shift:
                        plan.append({"y": closure_summ, "x": time.strftime(
                            "%Y-%m-%d %H:%M:%S.%f")[:-3]})
                        break
                    else:  
                        # Если время превышает время окончания смены, не прибавлять данный цикл
                        break
                if ShiftInfo[shift_task][6] != ShiftInfo[shift_task][6]:
                    closure_summ -= 1
                    time += timedelta(seconds=(product_count-1))
            plan.append({"y": None, "x": end_shift.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]})
        socketio.emit('receiveTrendPlanData',data=json.dumps({ip_addr:{'plan':plan,'trend':trend}},ensure_ascii=False, indent=4))


# Метод создания пользователя для сессии при прикладываении пропуска.
# Отправляет устройству на котором прикладывается пропуск команду
# на переход по роутингу авторизации '/Auth'


@app.route("/Auth/PassNumber=<string:passnumber>")
def Authorization(passnumber):
    try:
        user = UserModel()
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
            ,USR.[Oid]
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
                    SELECT [Role].[Name],[Role.Oid]
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
            if SavedRole != '' or len(SavedRole) > 0:
                user.role = SavedRole
                user.savedrole = True
            else:
                user.savedrole = False
            # Добавляем данные в экземпляр пользователя
            user.id = userdata[8]
            user.name = f"{userdata[1]} {userdata[2]} {userdata[3]}"
            user.username = userdata[4]
            user.CardNumber = userdata[5]
            user.interfaces = userdata[7]
            packet = {terminal: f'{user.CardNumber}'}
            for key in list(user_dict.keys()):
                if user_dict[key].CardNumber == user.CardNumber:
                    user_dict.pop(key)
            user_dict[str(user.id)] = user

            # Проверка на непрочитанные документы нормативной документации
            Docs = []
            for role in roles:               
                NewDocs = SQLManipulator.SQLExecute(
                    f"""
                        SELECT Documentation.Oid FROM Documentation, Relation_DocumentationRole
                        WHERE [Role] = '{role[1]}' AND
                        NOT EXISTS
                        (
                            SELECT DocumentReadStatus.Document FROM DocumentReadStatus
                            WHERE [User] = '{user.id}'
                        )
                    """
                )
                if len(NewDocs) > 0:               
                    Docs.append(NewDocs[0][0])  

            Docs = list(set(Docs))
            for doc in Docs:
                SQLManipulator.SQLExecute(
                    f"""
                        INSERT INTO DocumentReadStatus 
                            (Oid, [User], Document, [Status], ReadDate)
                        VALUES (NEWID(), '{user.id}', '{doc}', 0, NULL)   
                    """
                )
            
            NoReadDocs = SQLManipulator.SQLExecute(
                f"""
                    SELECT [Oid]
                    FROM [MES_Iplast].[dbo].[DocumentReadStatus]
                    WHERE [User]='{user.id}' AND Status = 0
                """
            )
            if len(NoReadDocs) > 0:
                user.ReadingAllDocs = False
            else:
                user.ReadingAllDocs = True

            for key in list(user_dict.keys()):
                if user_dict[key].CardNumber == user.CardNumber:
                    user_dict.pop(key)
            user_dict[str(user.id)] = user  

            # Отправляем в сокет сообщение о успешной авторизации
            socketio.emit('Auth', json.dumps(packet, ensure_ascii=False, indent=4))
        return 'Authorization successful'
    except:
        logger.exception()

# Метод предназначенный для авторизации без пропуска по запросу
# Большинство операций аналогичны методу авторизации с пропуском


@app.route("/Auth/PassNumber=<string:passnumber>/IP=<string:ipaddress>")
def AuthorizationWhithoutPass(passnumber, ipaddress):
    user = UserModel()
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
        ,USR.Oid
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
                SELECT [Role].[Name], [Role].Oid
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
        if SavedRole != '' or len(SavedRole) > 0:
            user.role = SavedRole
            user.savedrole = True
        else:
            user.savedrole = False
        user.id = userdata[8]
        user.name = f"{userdata[1]} {userdata[2]} {userdata[3]}"
        user.username = userdata[4]
        user.CardNumber = userdata[5]
        user.interfaces = userdata[7]
        packet = {terminal: f'{user.CardNumber}'}  

        # Проверка на новые документы нормативной документации
        Docs = []
        for role in roles:               
            NewDocs = SQLManipulator.SQLExecute(
                f"""
                    SELECT Documentation.Oid FROM Documentation, Relation_DocumentationRole
                    WHERE [Role] = '{role[1]}' AND
                    NOT EXISTS
                    (
                        SELECT DocumentReadStatus.Document FROM DocumentReadStatus
                        WHERE [User] = '{user.id}'
                    )
                """
            )
            if len(NewDocs) > 0:               
                Docs.append(NewDocs[0][0])  

        Docs = list(set(Docs))
        for doc in Docs:
            SQLManipulator.SQLExecute(
                f"""
                    INSERT INTO DocumentReadStatus 
                        (Oid, [User], Document, [Status], ReadDate)
                    VALUES (NEWID(), '{user.id}', '{doc}', 0, NULL)   
                """
            )
        
        NoReadDocs = SQLManipulator.SQLExecute(
            f"""
                SELECT [Oid]
                FROM [MES_Iplast].[dbo].[DocumentReadStatus]
                WHERE [User]='{user.id}' AND Status = 0
            """
        )
        if len(NoReadDocs) > 0:
            user.ReadingAllDocs = False
        else:
            user.ReadingAllDocs = True

        for key in list(user_dict.keys()):
            if user_dict[key].CardNumber == user.CardNumber:
                user_dict.pop(key)
        user_dict[str(user.id)] = user  

        socketio.emit('Auth', json.dumps(packet, ensure_ascii=False, indent=4))
    return 'Authorization successful'

# Метод загружающий пользователя по его ID в сессии при запросе login_manager'a


@login_manager.user_loader
def load_user(_id):
    if str(_id) in user_dict:
        return user_dict[str(_id)]

# Метод аутентификации пользователя и редирект на страницы в зависимости от роли


@app.route('/Auth/GetPass/PassNumber=<string:passnumber>')
def Auth(passnumber):
    try:
        ip_addr = request.remote_addr  # Получение IP-адресса пользователя
        sql_GetDeviceType = f"""SELECT DeviceType.[Name]
                        FROM Device, DeviceType
                        WHERE Device.DeviceId = '{ip_addr}' AND
                                Device.DeviceType = DeviceType.Oid
                        """
        device_type = SQLManipulator.SQLExecute(sql_GetDeviceType)[0][0]
        if device_type == "Терминал":
            for key in list(user_dict.keys()):
                if user_dict[key].CardNumber == passnumber:
                    login_user(user_dict[key])  
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
        else:
            return redirect('/')
    except:
        logger.exception()

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
    if current_user.id != None:
        user_dict.pop(str(current_user.id))
        logout_user()
        return redirect('/')
    else:
        error = """Попытка выхода из сесии пользователя из другой вкладки что запрещено."""
        return render_template('Show_error.html', error=error, ret='/menu',current_tpa=current_tpa[terminal])

# Метод выхода из аккаунта без открепления от терминала


@app.route('/logoutWithoutDeleteRoles')
@login_required
def logoutWithoutDeleteRoles():
    if current_user.id != None:
        user_dict.pop(str(current_user.id))  
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
    errors = []
    current_tpa[ip_addr][2].pressform = current_tpa[ip_addr][2].update_pressform()
    current_tpa[ip_addr][2].Check_Downtime(current_tpa[ip_addr][2].tpa)
    current_tpa[ip_addr][2].Check_pressform()
    current_tpa[ip_addr][2].data_from_shifttask()
    if current_tpa[ip_addr][2].shift != '':
        shift = current_tpa[ip_addr][2].shift.split('(')[0][:-1]
    else:
        shift = ''
    if len(current_tpa[ip_addr][2].errors) > 0:
        errors = current_tpa[ip_addr][2].errors
    try:
        MWData = {
            ip_addr: {
                "PF": str(current_tpa[ip_addr][2].pressform),
                "Product": current_tpa[ip_addr][2].product,
                "Plan": current_tpa[ip_addr][2].production_plan,
                "Fact": current_tpa[ip_addr][2].product_fact,
                "PlanCycle": str(current_tpa[ip_addr][2].cycle),
                "FactCycle": str(current_tpa[ip_addr][2].cycle_fact),
                "PlanWeight": current_tpa[ip_addr][2].plan_weight,
                "AverageWeight": current_tpa[ip_addr][2].average_weight,
                "Shift": str(shift),
                "Wastes": current_tpa[ip_addr][2].wastes,
                "Defectives": current_tpa[ip_addr][2].defectives,
                "Errors": errors
            },
            'Reason': ""
        }
        if data['data'] == "AfterSwitchPF":
            MWData['Reason'] = "AfterSwitchPF"
            socketio.emit("GetMainWindowData", data=json.dumps(
                MWData, ensure_ascii=False, indent=4))
        else:
            socketio.emit("GetMainWindowData", data=json.dumps(
                MWData, ensure_ascii=False, indent=4))
    except Exception as error:
        app.logger.error(f"[{datetime.now()}] {error}")
        pass


@socketio.on(message="GetExecutePlan")
def GetExecutePlan(data):
    try:
        ip_addr = request.remote_addr
        get_last_closure_sql = f"""
            SELECT TOP (1)
                [StartDate]
                ,[CountFact]
                ,[CycleFact]
                ,[EndDate]
            FROM [MES_Iplast].[dbo].[ProductionData] WHERE ShiftTask = '{current_tpa[ip_addr][2].shift_task_oid[0]}'
        """
        get_last_closure = SQLManipulator.SQLExecute(get_last_closure_sql)
        remaining_quantity = current_tpa[ip_addr][2].production_plan[0] - \
            get_last_closure[0][1]
        production_time = (get_last_closure[0][2] / 60)
        minutes_to_plan_end = remaining_quantity * production_time
        old_diff_time = datetime.now() - get_last_closure[0][3]
        end_date = (
            datetime.now() + timedelta(minutes=float(minutes_to_plan_end))) - old_diff_time
        socketio.emit("GetExecutePlan", data=json.dumps(
            {ip_addr: str(end_date)}), ensure_ascii=False, indent=4)
    except Exception as error:
        pass

@socketio.on(message="GetUpTubsStatus")
def UpTubsStatus(data):
    ip_addr = request.remote_addr
    active_tpa = []
    current_machine = current_tpa[ip_addr][0]
    tub_dict = {"Active":active_tpa,"CurrentTpa":current_machine}
    for tpa in TpaList[ip_addr]:
        tpa['WorkStatus'] = tpa['Controller'].Check_Downtime(tpa['Oid'])
        if tpa['WorkStatus'] == True:
            active_tpa.append(tpa['Oid'])
    socketio.emit("TubsStatus", data=json.dumps({ip_addr: tub_dict}),ensure_ascii=False, indent=4)

def Get_Tpa_Status(tpaoid):
    if tpaoid == None or tpaoid == '':
        return False
    sql = f"""
        SELECT TOP(1) [Date],Controller,[RFIDEquipmentBinding].RFIDEquipment
        FROM [MES_Iplast].[dbo].[RFIDClosureData], Equipment, [RFIDEquipmentBinding]
        WHERE 
            Equipment.Oid = '{tpaoid}' AND
            [RFIDEquipmentBinding].Equipment = Equipment.Oid AND
            [RFIDClosureData].Controller = [RFIDEquipmentBinding].RFIDEquipment
        ORDER BY Date DESC
    """
    last_closure_date = SQLManipulator.SQLExecute(sql)
    if len(last_closure_date) > 0:
        last_closure_date = last_closure_date[0][0]
        current_date = datetime.now()
        last_closure_date = last_closure_date
        seconds = (current_date - last_closure_date).total_seconds()
        if seconds >= 400:
            return False
        else:
            return True
    else:
        return False
    
@socketio.on(message='GetStickerInfo')
def GetStickerInfo(data):
    ip_addr = request.remote_addr

    sql_GetStickerInfo = f""" SELECT [Prod].[Name], [SInfo].[StickerCount]
                                FROM [MES_Iplast].[dbo].[StickerInfo] AS [SInfo]
                                LEFT JOIN [MES_Iplast].[dbo].[Product] AS [Prod] ON [Prod].[Oid] = [SInfo].[Product]
                                WHERE [Equipment] = '{current_tpa[ip_addr][0]}' """
                                
    stickerData = SQLManipulator.SQLExecute(sql_GetStickerInfo)
    
    if len(stickerData) != 0:
        data = {'Product': stickerData[0][0], 'Count': stickerData[0][1]}
    else:
        data = 'Empty'
   
    socketio.emit("SendStickerInfo", json.dumps(
        {ip_addr: data}, ensure_ascii=False, indent=4))

@socketio.on(message='GetNotify')
def SendNotify(data):
    ip_addr = request.remote_addr
    if ((current_user.ReadingAllDocs == False) and
        (current_user.Showed_notify == False)):
        socketio.emit("ShowNotify", json.dumps(
            {ip_addr: ''}, ensure_ascii=False, indent=4))
        current_user.Showed_notify = True
       
