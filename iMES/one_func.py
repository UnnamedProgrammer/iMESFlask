@socketio.on(message = "getTrendPlanData")
def GetPlan(data):
    ip_addr = request.remote_addr
    print(current_tpa[ip_addr])
    #-------------TREND
    # Массив и начальная точка, получаю начало и конец текущей смены
    sql_GetShiftTime = f"""
                            SELECT 
                                ShiftTask.Oid,
                                Shift.StartDate
                            FROM
                                Shift, ShiftTask
                            WHERE
                                Shift.Oid = ShiftTask.Shift and ShiftTask.Oid = '{current_tpa[ip_addr][2].shift_task_oid}'
                        """
    ShiftTime = SQLManipulator.SQLExecute(sql_GetShiftTime)
    for shift_task in ShiftTime:
        # Начальная точка назначается из БД (StartDate)
        trend = [
            {"y": "0", "x": (shift_task[1].strftime("%Y-%m-%d %H:%M:%S.%f"))[:-3]}]
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

    #-------------PLAN
    sql_GetShiftOid = f"""
                            SELECT TOP(1) ShiftTask.Shift
                            FROM Shift, ShiftTask
                            WHERE ShiftTask.Oid = '{current_tpa[ip_addr][2].shift_task_oid}'
                        """
    ShiftOid = SQLManipulator.SQLExecute(sql_GetShiftOid)[0][0]
    # Массив и начальная точка, получаю начало и конец текущей смены
    sql_GetShiftTime = f"""
                            SELECT 
                                ShiftTask.Oid,
                                Shift.StartDate,
                                Shift.EndDate,
                                ShiftTask.ProductCount,
                                ShiftTask.Cycle,
                                ShiftTask.Shift
                            FROM
                                Shift, ShiftTask
                            WHERE
                                Shift.Oid = ShiftTask.Shift and ShiftTask.Equipment = '{current_tpa[ip_addr][2].tpa}' and ShiftTask.Shift = '{ShiftOid}'
                        """
    ShiftTime = SQLManipulator.SQLExecute(sql_GetShiftTime)
    # Если сменное задание одно
    if len(ShiftTime) == 1:
        # Записываем начало и конец смены
        time = ShiftTime[0][1]
        end_shift = ShiftTime[0][2]
        # Массив и начальное значение
        plan = [{"y": "0", "x": time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]}]
        for closure in range(ShiftTime[0][3]):
            time += timedelta(seconds=int(ShiftTime[0][4]))
            if time < end_shift:
                plan.append({"y": str(closure), "x": time.strftime(
                    "%Y-%m-%d %H:%M:%S.%f")[:-3]})
            # Если время равно времени окончания смены, прибавить цикл и выйти из for
            elif time == end_shift:
                plan.append({"y": str(closure), "x": time.strftime(
                    "%Y-%m-%d %H:%M:%S.%f")[:-3]})
                break
            # Если время превышает время окончания смены, не прибавлять данный цикл
            else:
                # Пустая точка на конце смены, чтобы график был отрисован до ее конца
                plan.append({"y": None, "x": end_shift.strftime(
                    "%Y-%m-%d %H:%M:%S.%f")[:-3]})
                break
    # Если сменных заданий несколько
    elif len(ShiftTime) > 1:
        # Записываем начало и конец смены
        time = ShiftTime[0][1]
        end_shift = ShiftTime[0][2]
        # Переменная для подсчета суммы общего времени на производство
        shift_times = 0
        for shift_task in ShiftTime:
            shift_times += int(shift_task[3])*int(shift_task[4])
            break
        # Расчитываем оставшееся время на простои
        # if shift_times >= 43200:
        #     downtime = 0
        # else:
        #     downtime = 43200 - shift_times
        downtime = 4400
        # Массив и начальное значение
        plan = [{"y": "0", "x": time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]}]
        closure_summ = 0
        # Перебираем сменное задание
        for shift_task in ShiftTime:
            # for closure in range(1, shift_task[3]+1):
            for closure in range(1, 100+1):
                closure_summ += 1
                time += timedelta(seconds=int(shift_task[4]))
                if time < end_shift:
                    plan.append({"y": closure_summ, "x": time.strftime(
                        "%Y-%m-%d %H:%M:%S.%f")[:-3]})
                elif time == end_shift:
                    plan.append({"y": closure_summ, "x": time.strftime(
                        "%Y-%m-%d %H:%M:%S.%f")[:-3]})
                    break
                else:  # Если время превышает время окончания смены, не прибавлять данный цикл
                    break
            closure_summ -= 1
            time += timedelta(seconds=downtime//(len(ShiftTime)-1))
        # Пустая точка на конце смены, чтобы график был отрисован до конца
        plan.append({"y": None, "x": end_shift.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]})
        print(plan)
    socketio.emit('receiveTrendPlanData',data=json.dumps({ip_addr:{'plan':plan,'trend':trend}},ensure_ascii=False, indent=4))