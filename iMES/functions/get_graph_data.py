import json
from datetime import datetime, timedelta
from iMES import app, db
from iMES.daemons import ProductDataMonitoring
from iMES.Controller.TpaController import TpaController
from iMES.Model.DataBaseModels.ShiftTaskModel import ShiftTask
from iMES.Model.DataBaseModels.ShiftModel import Shift
from iMES.Model.DataBaseModels.RFIDClosureDataModel import RFIDClosureData
from iMES.Model.DataBaseModels.RFIDEquipmentBindingModel import RFIDEquipmentBinding
from iMES.Model.DataBaseModels.DowntimeFailureModel import DowntimeFailure




def get_graph_data_by_ctpa(current_tpa: TpaController, ip_addr=None):
    plan = []
    trend = []
    plan =[]
    trend = []
    # Начало и конец смены
    if ((current_tpa.shift_oid != '') and 
        (current_tpa.tpa != '') and
        (current_tpa.shift_oid != '')):
        ShiftInfo = (db.session.query(ShiftTask.Oid,
                                    Shift.StartDate,
                                    Shift.EndDate,
                                    ShiftTask.ProductCount,
                                    ShiftTask.Cycle,
                                    ShiftTask.Shift,
                                    ShiftTask.Product)
                                    .select_from(ShiftTask, Shift)
                                    .where(ShiftTask.Equipment == current_tpa.tpa)
                                    .where(ShiftTask.Shift == current_tpa.shift_oid)
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
                                                .where(ShiftTask.Equipment == current_tpa.tpa)
                                                .where(ShiftTask.Shift == current_tpa.shift_oid)
                                                .all())
                # Определяем очередь сменных заданий
                task_queue = []
                pressform = ProductDataMonitoring.GetTpaPressFrom(
                    current_tpa.tpa)
                equipment_performance = ProductDataMonitoring.GetEquipmentPerformance(
                    current_tpa.tpa, pressform)
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
                                                                    .where(RFIDEquipmentBinding.Equipment == current_tpa.tpa).one_or_none()[0])
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
                                            .where(DowntimeFailure.Equipment == current_tpa.tpa)
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
                                count += 1*current_tpa.socket_count
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
                if ip_addr is None:
                    data = json.dumps({
                        'plan': plan,
                        'trend': trend
                    },
                        ensure_ascii=False,
                        indent=4)
                else:
                    data = json.dumps({
                        ip_addr: {
                            'plan': plan,
                            'trend': trend
                        }
                    },
                        ensure_ascii=False,
                        indent=4)

                return data
        except Exception as err:
            app.logger.error(f"[{datetime.now()}] <get_graph_data_by_ctpa> {err}")
            if ip_addr is None:
                data = json.dumps({
                    'plan': [],
                    'trend': []
                },
                    ensure_ascii=False,
                    indent=4)
            else:
                data = json.dumps({
                    ip_addr: {
                        'plan': [],
                        'trend': []
                    }
                },
                    ensure_ascii=False,
                    indent=4)
            return data
    else:
        return {'error':"Отсутствует сменное задание"}
