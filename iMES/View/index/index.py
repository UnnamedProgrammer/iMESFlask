from iMES import app, login_manager, socketio, TpaList, current_tpa, db
from flask import redirect, render_template, request
from flask_login import login_required, login_user, logout_user, current_user
from iMES.daemons import ProductDataMonitoring
from iMES.Model.DataBaseModels.DowntimeFailureModel import DowntimeFailure
from iMES.Model.DataBaseModels.EmployeeModel import Employee
from iMES.Model.DataBaseModels.EquipmentModel import Equipment
from iMES.Model.DataBaseModels.ProductModel import Product
from iMES.Model.DataBaseModels.ProductionDataModel import ProductionData
from iMES.Model.DataBaseModels.RFIDClosureDataModel import RFIDClosureData
from iMES.Model.DataBaseModels.RFIDEquipmentBindingModel import RFIDEquipmentBinding
from iMES.Model.DataBaseModels.RoleModel import Role
from iMES.Model.DataBaseModels.ShiftModel import Shift
from iMES.Model.DataBaseModels.ShiftTaskModel import ShiftTask
from iMES.Model.DataBaseModels.StickerInfoModel import StickerInfo
from iMES.functions.redirect_by_role import redirect_by_role
from iMES.functions.device_tpa import device_tpa
import json
from datetime import datetime, timedelta
import urllib3
# Модули БД
from iMES.Model.DataBaseModels.DeviceTypeModel import DeviceType
from iMES.Model.DataBaseModels.DeviceModel import Device
from iMES.Model.DataBaseModels.UserModel import User
from iMES.Model.DataBaseModels.SavedRoleModel import SavedRole
from iMES.Model.DataBaseModels.LastSavedRoleModel import LastSavedRole
# Метод возвращающий главную страницу

urllib3.disable_warnings()

@app.route("/")
def index():
    ip_addr = request.remote_addr  # Получение IP-адресса пользователя
    # Проверяем нахожиться ли клиент в списке с привязанными к нему ТПА
    device_tpas = None
    # Выгружаем список привязанных ТПА к клиенту
    device_tpas = device_tpa(ip_addr)

    # Запрос определяющий тип устройства клиента из бд, веб или терминал
    device_type = db.session.query(DeviceType).where(
        Device.DeviceId == ip_addr).where(
            DeviceType.Oid == Device.DeviceType).one_or_none()

    # Если устройство является веб то находим пользователя привязаннаго за устройством
    # И автоматически авторизуем его по наименованию устройства
    if device_type is not None:
        if device_type.Name == 'Веб':
            if not current_user.is_authenticated:        
                usr = db.session.query(User).where(
                    Device.DeviceId == ip_addr).where(
                        User.UserName == Device.Name).one_or_none()
                usr.get_roles(ip_addr)
                if usr is not None:
                    login_user(usr)
                else:
                    pass
    else:
        return "Undefinded device, access denied."
    if current_tpa == None or current_tpa == {}:
        current_tpa[ip_addr] = device_tpas[0]
    # Рендерим страницу
    return render_template("index.html",
                           device_tpa=device_tpas,
                           current_tpa=current_tpa[ip_addr])


# Метод возвращающий текущий ТПА в навбаре
@app.route("/changeTpa", methods=["GET"])
def ChangeTPA():
    ip_addr = request.remote_addr
    need_tpa = request.args.getlist('oid')[0]
    for tpa in TpaList:
        current = str(tpa[0])
        if current == need_tpa:
            current_tpa[ip_addr] = tpa
            break
    return {}


# Метод возвращающий данные о плане и факте выпускаемой продукции на графике
# по запросу с сокета в файле Graph.js
@socketio.on(message = "getTrendPlanData")
def GetGraphData(data):
    ip_addr = request.remote_addr
    plan =[]
    trend = []
    # Начало и конец смены
    if ip_addr in current_tpa.keys():
        if ((current_tpa[ip_addr][2].shift_oid != '') and 
            (current_tpa[ip_addr][2].tpa != '') and
            (current_tpa[ip_addr][2].shift_oid != '')):
            ShiftInfo = (db.session.query(ShiftTask.Oid,
                                        Shift.StartDate,
                                        Shift.EndDate,
                                        ShiftTask.ProductCount,
                                        ShiftTask.Cycle,
                                        ShiftTask.Shift,
                                        ShiftTask.Product)
                                        .select_from(ShiftTask, Shift)
                                        .where(ShiftTask.Equipment == current_tpa[ip_addr][2].tpa)
                                        .where(ShiftTask.Shift == current_tpa[ip_addr][2].shift_oid)
                                        .where(Shift.Oid == ShiftTask.Shift)
                                        .all()
                                        )
            try:
                if (len(ShiftInfo) > 0):
                    StartShift = ShiftInfo[0][1]
                    EndShift = ShiftInfo[0][2]

                    # Вытягиваем возможные сменные задания
                    shift_tasks = (db.session.query(ShiftTask.ProductCount,
                                                    ShiftTask.Cycle,
                                                    ShiftTask.Product,
                                                    ShiftTask.Specification,
                                                    ShiftTask.SocketCount)
                                                    .select_from(ShiftTask)
                                                    .where(ShiftTask.Equipment == current_tpa[ip_addr][0])
                                                    .where(ShiftTask.Shift == current_tpa[ip_addr][2].shift_oid)
                                                    .all())
                    # Определяем очередь сменных заданий
                    task_queue = []
                    pressform = ProductDataMonitoring.GetTpaPressFrom(
                        current_tpa[ip_addr][0])
                    equipment_performance = ProductDataMonitoring.GetEquipmentPerformance(
                        current_tpa[ip_addr][0], pressform)
                    if equipment_performance == None:
                        total_socket_count = shift_tasks[0][4]
                    else:
                        total_socket_count = equipment_performance[4]

                    insert_flag = False
                    for i in range(0, len(shift_tasks)):
                        insert_flag = False
                        empty_slots = total_socket_count
                        if len(task_queue) == 0:
                            if shift_tasks[i][4] <= total_socket_count:
                                task_queue.append([shift_tasks[i]])
                            continue
                        else:
                            for task in task_queue:
                                if len(task) == 1:
                                    if ((shift_tasks[i][0] == task[0][0]) and
                                        (shift_tasks[i][1] == task[0][1]) and
                                        (shift_tasks[i][2] == task[0][2]) and
                                        (shift_tasks[i][4] == task[0][4]) and
                                        (empty_slots != 0) and 
                                        (task[0][4] != total_socket_count)):
                                        if (shift_tasks[i][4] <= empty_slots):
                                            empty_slots -= int(shift_tasks[i][4])
                                            task.append(shift_tasks[i])
                                            insert_flag = True
                                        break
                            if insert_flag == False:
                                if shift_tasks[i][4] <= total_socket_count:
                                    task_queue.append([shift_tasks[i]])

                    # Масив занимаемого времени выполнения сменных заданий           
                    time_to_every_task = []

                    # Время окончания сменного задания
                    task_start = (db.session.query(Shift.StartDate)
                                    .order_by(Shift.StartDate.desc()).first())
                    if len(task_start) > 0:
                        task_start = task_start[0]

                    #Вычисляем время затрачиваемое на каждое сменное задание
                    start = task_start
                    for task in task_queue:
                        one_cycle = timedelta(seconds=task[0][1])
                        end = None
                        for i in range(0, int(task[0][0])):
                            task_start += one_cycle
                            end = task_start
                        time_to_every_task.append([start, end, task[0][4]])
                        start = end
                        
                    # Формирование плана
                    FromStartDate = StartShift # начало смены
                    # Начальная точка графика
                    plan.append({"y": '0', "x": FromStartDate.strftime(
                        "%Y-%m-%d %H:%M:%S.%f")[:-3]})
                    
                    # Флаг выхода из цикла когда сумма даты и дельты превышает конец
                    cycle_exit_flag = False
                    # План последнего сменного задания
                    last_plan = 0
                    # Счетчик смыканий
                    count = 0
                    for task in task_queue:
                        # Цикл на одно смыкание
                        plan_delta = timedelta(seconds=task[0][1])
                        sockets = 0
                        if len(task) > 0:
                            for tk in task:
                                sockets += tk[4]
                        else:
                            sockets = task[4]
                        # Формируем точки складывая дельту и дату после каждого смыкания
                        for plan_clouser in range(last_plan, last_plan + task[0][0]):
                            count += 1
                            FromStartDate += plan_delta
                            plan.append({"y": plan_clouser, "x": FromStartDate.strftime(
                                "%Y-%m-%d %H:%M:%S.%f")[:-3]})
                            if EndShift <= FromStartDate: 
                                cycle_exit_flag = True                  
                                break
                        if cycle_exit_flag:
                            # Убераем то что вошло в ночную смену
                            if (EndShift < FromStartDate):
                                plan = plan[:-1]
                                plan[len(plan)-1]['x'] = EndShift.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                                plan[len(plan)-1]['y'] = count
                            break 
                        last_plan = last_plan + task[0][0] 
                    
                    # Получаем совершённые смыкания
                    clousers = (db.session.query(RFIDClosureData.Oid,
                                                RFIDClosureData.Controller,
                                                RFIDClosureData.Label,
                                                RFIDClosureData.Date,
                                                RFIDClosureData.Cycle,
                                                RFIDClosureData.Status,
                                                Shift.Note)
                                                .select_from(RFIDClosureData, Shift)
                                                .where(RFIDClosureData.Controller == \
                                                    db.session.query(RFIDEquipmentBinding.RFIDEquipment)
                                                                        .select_from(RFIDEquipmentBinding)
                                                                        .where(RFIDEquipmentBinding.Equipment == current_tpa[ip_addr][2].tpa).one_or_none()[0])
                                                .where(Shift.Oid == db.session.query(Shift.Oid).order_by(Shift.StartDate.desc()).first()[0])
                                                .where(RFIDClosureData.Date >= Shift.StartDate)
                                                .where(RFIDClosureData.Date <= Shift.EndDate)
                                                .where(RFIDClosureData.Status == 1)
                                                .order_by(RFIDClosureData.Date.asc())
                                                .all())
                    # Получаем временные промежутки простоев и годные смыкания
                    idles_db = (db.session.query(DowntimeFailure.Oid,
                                                DowntimeFailure.StartDate,
                                                DowntimeFailure.EndDate,
                                                DowntimeFailure.ValidClosures)
                                                .select_from(DowntimeFailure, Shift)
                                                .where(DowntimeFailure.Equipment == current_tpa[ip_addr][2].tpa)
                                                .where(DowntimeFailure.EndDate is not None)
                                                .where(Shift.Oid == \
                                                    db.session.query(Shift.Oid).select_from(Shift).order_by(Shift.StartDate.desc()).first()[0])
                                                .where(DowntimeFailure.StartDate >= Shift.StartDate)
                                                .all())
                    idle_catch = False
                    checked_idles = []
                    trend.append({"y": '0', "x": StartShift.strftime(
                        "%Y-%m-%d %H:%M:%S.%f")[:-3]})
                    if len(clousers) > 0:
                        clousers = tuple(clousers)
                        count = 0
                        # Перебираем простои если есть вхождение смыкания в простой
                        # То после конца простоя указываем годные
                        if len(idles_db) > 0:
                            for close in clousers:
                                idle_catch = False
                                for idle in idles_db:
                                    if idle[0] not in checked_idles:
                                        if StartShift <= idle[1] and idle[1] <= EndShift:
                                            if close[3] >= idle[1]:
                                                if idle[3] != None:                                      
                                                    count += int(idle[3])*current_tpa[
                                                        ip_addr][2].socket_count
                                                    trend.append({"x":str(close[3].strftime(
                                                        "%Y-%m-%d %H:%M:%S.%f"))[:-3],
                                                        "y":count})
                                                    idle_catch = True
                                                    checked_idles.append(idle[0])
                                                else:
                                                    count += 0
                                                    trend.append({"x":str(close[3].strftime(
                                                        "%Y-%m-%d %H:%M:%S.%f"))[:-3],
                                                        "y":count})
                                                    idle_catch = True
                                                    checked_idles.append(idle[0]) 
                                if idle_catch != True:
                                    count += 1*current_tpa[ip_addr][2].socket_count
                                    trend.append({"x":str(close[3].strftime(
                                        "%Y-%m-%d %H:%M:%S.%f"))[:-3], "y":count})
                        else:
                            for close in clousers:
                                for task_time in time_to_every_task:
                                    if task_time[0] <= close[3] <= task_time[1]:
                                        count += 1 * task_time[2]
                                        trend.append({"x": str(close[3].strftime(
                                            "%Y-%m-%d %H:%M:%S.%f"))[:-3], "y": count})
                                        continue
                socketio.emit('receiveTrendPlanData',
                                data=json.dumps({ip_addr:
                                                {'plan':plan,
                                                'trend':trend}},
                                                ensure_ascii=False,
                                                indent=4))
            except Exception as err:
                app.logger.error(f"[{datetime.now()}] <GetGraphData> {err}")

# Метод создания пользователя для сессии при прикладываении пропуска.
# Отправляет устройству на котором прикладывается пропуск команду
# на переход по роутингу авторизации '/Auth'
@app.route("/Auth/PassNumber=<string:cardnumber>")
def Authorization(cardnumber):
    ip_addr = request.remote_addr
    socketio.emit('Auth', json.dumps({f'{ip_addr}':cardnumber}, ensure_ascii=False, indent=4))
    return 'Authorization start'

# Метод загружающий пользователя по его Oid в сессии при запросе login_manager'a
@login_manager.user_loader
def load_user(Oid):
    ip_addr = request.remote_addr
    usr = db.session.query(User).where(User.Oid == Oid).one_or_none()
    usr.get_roles(ip_addr)
    return usr

# Метод аутентификации пользователя и редирект на страницы в зависимости от роли
@app.route('/Auth/GetPass/PassNumber=<string:cardnumber>')
def Auth(cardnumber):
    ip_addr = request.remote_addr
    if not current_user.is_authenticated:
        usr = db.session.query(User).where(User.CardNumber == cardnumber).one_or_none()
        usr.get_roles(ip_addr)
        if usr != None:
            login_user(usr)
            return redirect_by_role(current_user.Roles, current_tpa[ip_addr])
        else:
            return redirect("/")
    else:
        return redirect_by_role(current_user.Roles, current_tpa[ip_addr])
    


# Метод вызываемый при переходе на роутинг требующий авторизации будучи не авторизованным
@app.route('/login')
def login():
    return render_template('Show_error.html', error="Нет доступа, авторизируйтесь с помощью пропуска", ret='/', current_tpa=current_tpa[request.remote_addr])

# Метод выхода из аккаунта с откреплением от терминала
@app.route('/logout')
@login_required
def logout():
    ip_addr = request.remote_addr
    saved_role = db.session.query(LastSavedRole).where(
        LastSavedRole.Device == db.session.query(Device.Oid).where(
            Device.DeviceId == ip_addr
            ).one_or_none()[0]
    ).where(
        LastSavedRole.SavedRole == db.session.query(SavedRole.Oid).where(
            SavedRole.User == current_user.Oid
        ).where(
            SavedRole.Device == db.session.query(Device.Oid).where(
                Device.DeviceId == ip_addr
            ).one_or_none()[0] 
        ).one_or_none()[0]
    ).one_or_none()
    if saved_role != None:
        db.session.delete(saved_role)
        db.session.commit()
    logout_user()
    return redirect('/')

# Метод выхода из аккаунта без открепления от терминала
@app.route('/logoutWithoutDeleteRoles')
@login_required
def logoutWithoutDeleteRoles():
    logout_user()
    return redirect('/')

# Метод возвращающий текущего оператора и наладчика на устройстве
# Запрос на этот роутинг выполняется из кода JS в index_template.html
@app.route('/getOperatorAndAdjuster')
def ReturnOperatorAndAdjuster():
    ip = request.remote_addr
    OperatorAdjusterAtTerminals = {'Оператор': '', 'Наладчик': ''}
    roles_emp_at_device = (db.session.query(Employee.LastName,
                                           Employee.FirstName,
                                           Employee.MiddleName,
                                           Role.Name)
                                           .select_from(LastSavedRole, SavedRole, Employee, Role, User)
                                           .where(LastSavedRole.Device == \
                                                db.session.query(Device.Oid).where(Device.DeviceId == ip).one_or_none()[0])
                                           .where(SavedRole.Oid == LastSavedRole.SavedRole)
                                           .where(Role.Oid == SavedRole.Role)
                                           .where(User.Oid == SavedRole.User)
                                           .where(Employee.Oid == User.Employee)
                                           .all())
    if roles_emp_at_device is not None:
        operator = ''
        adjuster = ''
        for employee in roles_emp_at_device:
            if employee[3] == 'Наладчик':
                adjuster = f'{roles_emp_at_device[0][0]} {roles_emp_at_device[0][1]} {roles_emp_at_device[0][2]}'
            if employee[3] == 'Оператор':
                operator = f'{roles_emp_at_device[0][0]} {roles_emp_at_device[0][1]} {roles_emp_at_device[0][2]}'
        OperatorAdjusterAtTerminals['Оператор'] = operator
        OperatorAdjusterAtTerminals['Наладчик'] = adjuster
    return json.dumps(OperatorAdjusterAtTerminals, ensure_ascii=False, indent=4)

# Метод сокета срабатывающий при соединении
@socketio.on(message='GetDeviceType')
def socket_connected(data):
    ip_addr = request.remote_addr
    device_type = (db.session.query(DeviceType.Name)
                    .select_from(DeviceType, Device)
                    .where(Device.DeviceId == ip_addr)
                    .where(DeviceType.Oid == Device.DeviceType)
                    .one_or_none())
    if(device_type[0] == 'Веб'):
        data = 'Веб'
    else:
        data = 'Терминал'
    socketio.emit("DeviceType", json.dumps(
        {ip_addr: data}, ensure_ascii=False, indent=4))


@socketio.on(message="NeedUpdateMainWindowData")
def UpdateMainWindowData(data):
    ip_addr = request.remote_addr
    errors = []
    if ip_addr in current_tpa.keys():
        if current_tpa[ip_addr][2].shift != '':
            shift = current_tpa[ip_addr][2].shift.split('(')[0][:-1]
        else:
            shift = ''
        if len(current_tpa[ip_addr][2].errors) > 0:
            errors = current_tpa[ip_addr][2].errors
        try:
            for tpa in TpaList:
                if str(tpa[0]) == current_tpa[ip_addr][0]:
                    current_tpa[ip_addr] = tpa
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
            app.logger.error(f"[{datetime.now()}] <UpdateMainWindowData> {error}")
            pass


@socketio.on(message="GetExecutePlan")
def GetExecutePlan(data):
    try:
        ip_addr = request.remote_addr
        get_last_closure = (db.session.query(ProductionData.StartDate,
                                            ProductionData.CountFact,
                                            ProductionData.CycleFact,
                                            ProductionData.EndDate)
                                            .where(ProductionData.ShiftTask == current_tpa[ip_addr][2].shift_task_oid[0])
                                            .first())
        remaining_quantity = current_tpa[ip_addr][2].production_plan[0] - \
            get_last_closure[1]
        production_time = (get_last_closure[2] / 60)
        minutes_to_plan_end = remaining_quantity * production_time
        old_diff_time = datetime.now() - get_last_closure[3]
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
    if ip_addr in current_tpa.keys():
        current_machine = current_tpa[ip_addr][0]
        tub_dict = {"Active":active_tpa,"CurrentTpa":str(current_machine)}
        for tpa in TpaList:
            tpa[3] = tpa[2].Check_Downtime(tpa[0])
            if tpa[3] == True:
                active_tpa.append(str(tpa[0]))
        socketio.emit("TubsStatus", data=json.dumps({ip_addr: tub_dict}),ensure_ascii=False, indent=4)
    
@socketio.on(message='GetStickerInfo')
def GetStickerInfo(data):
    ip_addr = request.remote_addr
    stickerData = (db.session.query(Product.Name, 
                                    StickerInfo.StickerCount)
                                    .join(Product).filter(Product.Oid == StickerInfo.Product)
                                    .where(StickerInfo.Equipment == current_tpa[ip_addr][0])
                                    .all())
    if len(stickerData) != 0:
        data = {'Product': stickerData[0][0], 'Count': stickerData[0][1]}
    else:
        data = 'Empty'
   
    socketio.emit("SendStickerInfo", json.dumps(
        {ip_addr: data}, ensure_ascii=False, indent=4))

@socketio.on(message='GetNotify')
def SendNotify(data):
    try:
        ip_addr = request.remote_addr
        if (current_user.Oid != None):
            if ((current_user.ReadingAllDocs == False) and
                (current_user.Showed_notify == False)):
                socketio.emit("ShowNotify", json.dumps(
                    {ip_addr: ''}, ensure_ascii=False, indent=4))
                current_user.Showed_notify = True
    except:
        pass
       
