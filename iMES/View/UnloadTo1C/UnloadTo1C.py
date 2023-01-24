from iMES import app
from iMES.Model.BaseObjectModel import BaseObjectModel
import json
from collections import OrderedDict

@app.route('/1CUnlouding/Date=<string:date>/STNumber=<string:stnum>')
def UnloudingTo1C(date,stnum):
    # Убираем лишние нули так как в базе номер сменки без нулей
    data = []
    ordinal = ''
    slc = 0
    for i in stnum:
        if i == '0':
            slc += 1
        else:
            break
    ordinal = stnum[slc:]
    # Ищем в базе смену в зависимости от даты
    shift = BaseObjectModel.SQLExecute(f"""
        SELECT [Oid], Note
        FROM [MES_Iplast].[dbo].[Shift] WHERE 
            DATENAME(YEAR, [StartDate]) = DATENAME(YEAR, CAST('{date}' AS datetime)) AND
            DATENAME(MONTH, [StartDate]) = DATENAME(MONTH,CAST('{date}' AS datetime)) AND
            DATENAME(DAY, [StartDate]) = DATENAME(DAY, CAST('{date}' AS datetime))
    """)
    # Если нашли смену то ищем сменные задания с заданным номером и сменой
    if len(shift) > 0:
        full_task_list = []
        if len(shift) == 1:
            shift_tasks = BaseObjectModel.SQLExecute(f"""
                SELECT [Oid], 
                    Shift,
                    Equipment, 
                    Product,
                    Specification,
                    [ProductCount],
                    [Cycle],
                    [Weight],
                    [SocketCount],
                    Shift
                FROM [MES_Iplast].[dbo].[ShiftTask]
                WHERE Ordinal = {ordinal} AND
                        Shift = '{shift[0][0]}'
            """)
            full_task_list = shift_tasks
        else:
            shift_tasks1 = BaseObjectModel.SQLExecute(f"""
                SELECT [Oid], 
                    Shift,
                    Equipment, 
                    Product,
                    Specification,
                    [ProductCount],
                    [Cycle],
                    [Weight],
                    [SocketCount],
                    Shift
                FROM [MES_Iplast].[dbo].[ShiftTask]
                WHERE Ordinal = {ordinal} AND
                        Shift = '{shift[0][0]}'
            """)
            shift_tasks2 = BaseObjectModel.SQLExecute(f"""
                SELECT [Oid], 
                    Shift,
                    Equipment, 
                    Product,
                    Specification,
                    [ProductCount],
                    [Cycle],
                    [Weight],
                    [SocketCount],
                    Shift
                FROM [MES_Iplast].[dbo].[ShiftTask]
                WHERE Ordinal = {ordinal} AND
                        Shift = '{shift[1][0]}'
            """)
            full_task_list = shift_tasks1 + shift_tasks2
        # Проходим по каждому сменному заданию и ищем все данные связанные с ним
        pd = []
        count = 0
        for task in full_task_list:
            # Поиск номенклатуры ТПА
            nomenclature_code = BaseObjectModel.SQLExecute(
                f"""
                    SELECT NG.[Name], NG.[Code]
	                FROM NomenclatureGroup AS NG, Equipment
                    WHERE Equipment.Oid = '{task[2]}' AND
                    NG.Oid = Equipment.NomenclatureGroup
                """
            )
            # Поиск продукта сменки
            product = BaseObjectModel.SQLExecute(
                f"""
                    SELECT [Oid]
                        ,[Code]
                        ,[Name]
                        ,[Article]
                    FROM [MES_Iplast].[dbo].[Product]
                    WHERE Oid = '{task[3]}'
                """
            )

            # Поиск данных по произведенному продукту
            production_data = BaseObjectModel.SQLExecute(f"""
                    SELECT [Oid]
                        ,[ShiftTask]
                        ,[RigEquipment]
                        ,[Status]
                        ,[StartDate]
                        ,[EndDate]
                        ,[CountFact]
                        ,[CycleFact]
                        ,[WeightFact]
                        ,[SpecificationFact]
                    FROM [MES_Iplast].[dbo].[ProductionData] WHERE
                        ShiftTask = '{task[0]}'
                """)
            
            if len(product) > 0:
                pass
            else:
                return f'В сменном задании {task[0]} не указан продукт.'
                
            if len(nomenclature_code) > 0:
                spec = BaseObjectModel.SQLExecute(
                    f"""
                        SELECT TOP (1000) [Oid]
                            ,[Code]
                            ,[Name]
                            ,[Product]
                            ,[UseFactor]
                            ,[IsActive]
                        FROM [MES_Iplast].[dbo].[ProductSpecification]
                        WHERE Oid = '{task[4]}'
                    """
                )
                if len(spec) > 0:
                    pass
                else:
                    return f'В сменном задании {task[0]} неизвестная спецификация.'

                # Получаем наименование смены
                get_shift = BaseObjectModel.SQLExecute(
                    f"""
                    SELECT [Oid]
                        ,[StartDate]
                        ,[EndDate]
                        ,[Note]
                    FROM [MES_Iplast].[dbo].[Shift] 
                    WHERE Oid = '{task[9]}'   
                    """
                )

                # Вставляем трафарет данных по сменному задания
                data.append({'oid':nomenclature_code[0][1],
                             'name':nomenclature_code[0][0],
                             'product_code': product[0][1],
                             'product': product[0][2],
                             'specefication': spec[0][2],
                             'specification_code': spec[0][1],
                             'plan': str(task[5]),
                             'weight': str(task[7]),
                             'shift': get_shift[0][3],
                             'cycle': str(task[6]),
                             'production_data': []})

                if len(production_data) > 0:
                    # Ищем все данные привязанные к production data
                    for pd in production_data:
                        # Получаем ПФ
                        rig_equipment = BaseObjectModel.SQLExecute(
                            f"""
                                SELECT TOP (1000) [Oid]
                                    ,[Code]
                                    ,[Name]
                                    ,[EquipmentType]
                                    ,[Area]
                                    ,[NomenclatureGroup]
                                    ,[InventoryNumber]
                                    ,[SyncId]
                                FROM [MES_Iplast].[dbo].[Equipment]
                                WHERE Oid = '{pd[2]}'
                            """
                        )
                        # Получаем фактическую спецификацию
                        spec_fact = BaseObjectModel.SQLExecute(
                            f"""
                                SELECT TOP (1000) [Oid]
                                    ,[Code]
                                    ,[Name]
                                    ,[Product]
                                    ,[UseFactor]
                                    ,[IsActive]
                                FROM [MES_Iplast].[dbo].[ProductSpecification]
                                WHERE Oid = '{pd[9]}' 
                            """
                        )
                        # Заполняем лист отходов брака
                        wastes_list = []
                        prod_wastes = BaseObjectModel.SQLExecute(
                            f"""
                                SELECT [Oid]
                                    ,[ProductionData]
                                    ,[Material]
                                    ,[Type]
                                    ,[Weight]
                                    ,[Count]
                                    ,[Downtime]
                                    ,[Note]
                                    ,[CreateDate]
                                    ,[Creator]
                                FROM [MES_Iplast].[dbo].[ProductWaste]
                                WHERE ProductionData = '{pd[0]}'
                            """
                        )
                        if len(prod_wastes) > 0:
                            for waste in prod_wastes:
                                if waste[2] != None:
                                    material_data = BaseObjectModel.SQLExecute(
                                        f"""
                                            SELECT TOP (1000) [Oid]
                                                ,[Code]
                                                ,[Name]
                                                ,[Article]
                                                ,[Type]
                                            FROM [MES_Iplast].[dbo].[Material]
                                            WHERE Oid = '{waste[2]}'  
                                        """
                                    )
                                    if len(material_data) > 0 or waste[2] == None:
                                        typew = ''
                                        if waste[3] == 0:
                                            typew = 'Отход'
                                        else:
                                            typew = 'Брак'
                                        if typew == 'Отход':
                                            wastes_list.append(
                                                {
                                                    'wastes_name': material_data[0][2],
                                                    'wastes_code': material_data[0][1],
                                                    'type': typew,
                                                    'weight': str(waste[4]),
                                                    'create_date': waste[8].strftime('%Y-%m-%d %H:%M:%S')
                                                }                                     
                                            )
                                        elif typew == 'Брак':
                                            wastes_list.append(
                                                {
                                                    'type': typew,
                                                    'weight': str(waste[4]),
                                                    'count': str(waste[5]),
                                                    'create_date': waste[8].strftime('%Y-%m-%d %H:%M:%S')
                                                }                                     
                                            )
                                    else:
                                        return f'Неизвестная запись в [Material]'
                        # Заполняем данные по введёному весу
                        prod_weight_list = []
                        prod_weight = BaseObjectModel.SQLExecute(
                            f"""
                                SELECT [Oid]
                                    ,[ProductionData]
                                    ,[Weight]
                                    ,[CreateDate]
                                    ,[Creator]
                                FROM [MES_Iplast].[dbo].[ProductWeight]
                                WHERE ProductionData = '{pd[0]}'   
                            """
                        )
                        if len(prod_weight) > 0:
                            for weight in prod_weight:
                                prod_weight_list.append({
                                    'weight': str(weight[2]),
                                    'create_date': weight[3].strftime('%Y-%m-%d %H:%M:%S')
                                })
                        if len(spec_fact) == 0:
                            return f'В productiondata {pd[0]} неизвестная спецификация'
                        else:
                            spec_fact = spec_fact[0]

                        # Вставляем все данные в трафарет
                        if len(rig_equipment) > 0:
                            data[count]['production_data'].append({'press_form': rig_equipment[0][2],
                                                                   'pressform_code': rig_equipment[0][1],
                                                                   'start_date': str(pd[4]),
                                                                   'end_date': str(pd[5]),
                                                                   'count_fact': str(pd[6]),
                                                                   'cycle_fact': str(pd[7]),
                                                                   'weight_fact': str(pd[8]),
                                                                   'spec_fact' : spec_fact[2],
                                                                   'spec_code_fact': spec_fact[1],
                                                                   'wastes': wastes_list,
                                                                   'entered_weight': prod_weight_list
                                                                  })
                        else:
                            return f'В productiondata {pd[0]} неизвестная ПФ'
            else:
                return 'В одном из сменных заданий нет номенклатурной группы.'
            count += 1   
    else:
        return 'Не удалось найти смену, возможно неверно указана дата.'
    # Возвращаем данные в виде json
    # флаг ensire_ascii нужен для отображаения символов отличных от ascii
    return json.dumps({'data': data}, ensure_ascii=False)