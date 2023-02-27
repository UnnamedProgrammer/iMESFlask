import json
from datetime import datetime, timedelta

from iMES import ProductDataMonitoring, app
from iMES.Controller.TpaController import TpaController
from iMES.Model.SQLManipulator import SQLManipulator


def get_graph_data_by_ctpa(current_tpa: TpaController, ip_addr=None):
    plan = []
    trend = []
    # Начало и конец смены
    if ((current_tpa.shift_oid != '') and
            (current_tpa.production_plan != (0,)) and
            (current_tpa.production_plan != 0) and
            (current_tpa.tpa != '') and
            (current_tpa.shift_oid != '')):
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
                        Shift.Oid = ShiftTask.Shift and 
                        ShiftTask.Equipment = '{current_tpa.tpa}' and 
                        ShiftTask.Shift = '{current_tpa.shift_oid}'
                """
        ShiftInfo = SQLManipulator.SQLExecute(sql_GetShiftInfo)
        try:
            if len(ShiftInfo) > 0:
                StartShift = ShiftInfo[0][1]
                EndShift = ShiftInfo[0][2]

                # Вытягиваем возможные сменные задания
                shift_tasks = SQLManipulator.SQLExecute(
                    f"""
                        SELECT [ProductCount]
                                ,[Cycle]
                                ,[Product]
                                ,[Specification]
                                ,[SocketCount]
                        FROM [MES_Iplast].[dbo].[ShiftTask]
                        WHERE Equipment = '{current_tpa.tpa}' AND
                                [Shift] = '{current_tpa.shift_oid}'      
                    """
                )
                # Определяем очередь сменных заданий
                task_queue = []
                pressform = ProductDataMonitoring.GetTpaPressFrom(
                    current_tpa.tpa)
                equipment_performance = ProductDataMonitoring.GetEquipmentPerformance(
                    current_tpa.tpa, pressform)
                if equipment_performance is None:
                    total_socket_count = shift_tasks[0][4]
                else:
                    total_socket_count = equipment_performance[4]

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
                                    if shift_tasks[i][4] <= empty_slots:
                                        empty_slots -= int(shift_tasks[i][4])
                                        task.append(shift_tasks[i])
                                        insert_flag = True
                                    break
                        if insert_flag is False:
                            if shift_tasks[i][4] <= total_socket_count:
                                task_queue.append([shift_tasks[i]])

                # <<<!!!! ЗАДЕЙСТВОВАТЬ ПОСЛЕ СОВЕЩАНИЯ ПО ПЕРЕНАЛАДКЕ !!!!>>>>
                # Вычисляем время затрачиваемое на каждое сменное задание
                # for task in task_queue:
                #     task_delta = timedelta(seconds=0)
                #     one_cycle = timedelta(seconds=task[0][1])
                #     for i in range(0, int(task[0][0])):
                #         task_delta += one_cycle
                #     time_to_every_task.append(task_delta)

                # Формирование плана
                FromStartDate = StartShift  # начало смены
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
                    # Формируем точки складывая дельту и дату после каждого смыкания
                    for plan_clouser in range(last_plan,
                                              last_plan + task[0][0]):
                        count += 1
                        FromStartDate += plan_delta
                        plan.append(
                            {"y": plan_clouser, "x": FromStartDate.strftime(
                                "%Y-%m-%d %H:%M:%S.%f")[:-3]})
                        if EndShift <= FromStartDate:
                            cycle_exit_flag = True
                            break
                    if cycle_exit_flag:
                        # Убераем то что вошло в ночную смену
                        if EndShift < FromStartDate:
                            plan = plan[:-1]
                            plan[len(plan) - 1]['x'] = EndShift.strftime(
                                "%Y-%m-%d %H:%M:%S.%f")[:-3]
                            plan[len(plan) - 1]['y'] = count
                        break
                    last_plan = last_plan + task[0][0]

                    # Получаем совершённые смыкания
                sql = f"""
                    SELECT RCD.[Oid]
                        ,[Controller]
                        ,[Label]
                        ,[Date]
                        ,RCD.[Cycle]
                        ,[Status]
                        ,Shift.Note
                    FROM [MES_Iplast].[dbo].[RFIDClosureData] as RCD, ShiftTask, Shift 
                    WHERE 
                    Controller = (SELECT RFIDEquipmentBinding.RFIDEquipment 
                                        FROM RFIDEquipmentBinding, ShiftTask
                                        WHERE ShiftTask.Equipment = RFIDEquipmentBinding.Equipment and 
                                        ShiftTask.Oid = '{current_tpa.shift_task_oid[0]}') AND
                    ShiftTask.Oid = '{current_tpa.shift_task_oid[0]}' AND
                    Shift.Oid = ShiftTask.Shift AND
                    Date between Shift.StartDate AND Shift.EndDate AND
                    Status = 1
                    ORDER BY Date ASC
                """
                clousers = SQLManipulator.SQLExecute(sql)

                # Получаем временные промежутки простоев и годные смыкания
                idles_db = SQLManipulator.SQLExecute(
                    f"""
                        SELECT TOP(50) DF.[Oid]
                                ,DF.[StartDate]
                                ,DF.[EndDate]
                                ,DF.[ValidClosures]
                        FROM [MES_Iplast].[dbo].[DowntimeFailure] AS DF, [Shift] AS SH
                        WHERE Equipment = '{current_tpa.tpa}' AND
                                DF.EndDate IS NOT NULL AND
                                DF.[ValidClosures] != 0 AND
                                SH.Oid = '{current_tpa.shift_oid}' AND
                                DF.StartDate >= SH.StartDate
                    """
                )
                checked_idles = []
                trend.append({"y": '0', "x": StartShift.strftime(
                    "%Y-%m-%d %H:%M:%S.%f")[:-3]})
                if len(clousers) > 0:
                    clousers = tuple(clousers)
                    count = 0
                    # Перебираем простои если есть вхождение смыкания в простой
                    # То после конца простоя указываем годные
                    for close in clousers:
                        idle_catch = False
                        for idle in idles_db:
                            if idle[0] not in checked_idles:
                                if StartShift <= idle[2] <= EndShift:
                                    if close[3] >= idle[2]:
                                        count += int(idle[3]) * \
                                                 current_tpa.socket_count
                                        trend.append(
                                            {"x": str(close[3].strftime(
                                                "%Y-%m-%d %H:%M:%S.%f"))[:-3],
                                             "y": count})
                                        idle_catch = True
                                        checked_idles.append(idle[0])
                        if idle_catch is True:
                            count += 1 * current_tpa.socket_count
                            trend.append({"x": str(close[3].strftime(
                                "%Y-%m-%d %H:%M:%S.%f"))[:-3], "y": count})
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
            app.logger.error(f"[{datetime.now()}] {err}")
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
