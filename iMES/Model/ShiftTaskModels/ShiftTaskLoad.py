"""Модуль для работы со сменными заданиями."""

from logging import critical
import requests
import json
from iMES.Model.ShiftTaskModels.ShiftTaskModel import ShiftTaskModel
from progress.bar import IncrementalBar
from iMES.Model.SQLManipulator import SQLManipulator
import datetime
from iMES import app
import sys

class ShiftTaskLoader():
    """
        Класс выгрузки сменного задания из 1С
        :param _nomenclature_group - Номенклатурная группа ТПА, для поиска
         по всем ТПА введите в поле кавычки "", для поиска по нескольким ТПА
         передайте объект типа >>> list() c объектами >>> str() содержащими
         номенклатурную группу оборудования
        :param _date - Дата на которую требуется сменное задание
        :param _shift - Смена (0 - День, 1 - Ночь), оставьте в этом поле 3
        для автоматического определения текущей смены
        >>> Load = ShiftTaskLoader("000000043",20220715,0)
        >>> Load.Get_ShiftTask()
        >>> Load.InsertToDataBase() 
        или
        >>> Load = ShiftTaskLoader("",20220715,0)
        >>> Load.Get_ShiftTask()
        >>> Load.InsertToDataBase()
        или
        >>> TpaList = ["000000043","000000042","000000041"]
        >>> Load = ShiftTaskLoader(TpaList,20220715,0)
        >>> Load.Get_ShiftTask()
        >>> Load.InsertToDataBase()
        "Данные о сменном задании получены."
    """

    def __init__(self, _nomenclature_group, _date: int, _shift: int):
        self.nomenclature_group = _nomenclature_group
        self.date = _date
        if _shift == 3:
            self.shift = self.Determine_Shift()
        elif _shift > 3:
            raise Exception("Invalid shift argument")
        else:
            self.shift = _shift
        self.shift_task_list = []
        self.shift_task_parsed = None
        self.data = None

    # Метод парсит сменные задания в зависимости от переданного аргумента
    # _nomenclature_group и добавляет их в список self.shift_task_list
    def Get_ShiftTask(self) -> list:
        self.data = self.ShiftTask_Update()
        if self.data == '':
            app.logger.critical("Ошибка 1С при выгрузке сменного задания.")
            sys.exit()
        if isinstance(self.nomenclature_group, list):
            for NomGroup in self.nomenclature_group:
                self.Find_ShiftTask(NomGroup, self.data)
        elif isinstance(self.nomenclature_group, str):
            self.Find_ShiftTask(NomGroup, self.data)

    # Делает запрос в веб-сервис 1С получая json файл, парсит его
    # и возвращает в виде dict
    def ShiftTask_Update(self):
        json_data = requests.get(
            f"""http://mes:4439/IplMES/hs/MES/GetProductionAssignment2?Date={str(self.date)}000000&Smena={str(self.shift)}""")
        with open('st.json', 'wb') as file_json:
            file_json.write(json_data.content)
            file_json.close()
        try:
            with open('st.json', 'r', encoding='utf-8-sig') as file_json:
                load_file = json.load(file_json)[0]
        except:
            with open('st.json', 'r', encoding='windows-1251',errors='ignore') as file_json:
                load_file = file_json.read()
                app.logger.critical(load_file)
                return ''
        return load_file

    # Определяет какое сейчас время суток, если в shift аргумент класса
    # было передано 3 то метод используется автоматически
    def Determine_Shift(self) -> int:
        # 0 - День, 1 - Ночь
        now = datetime.datetime.now()
        hour = now.hour
        if (hour >= 1 and hour < 7) or (hour >= 19 and hour <= 24):
            return 1
        elif hour >= 7 and hour < 19:
            return 0

    # Метод самопроверки значений класса перед вставкой в базу данных
    # Некоторые поля в таблице являются FK которые ссылаются на другие таблицы
    # В связи с этим нужно проверить есть ли зависимые значения в других таблицах
    # чтобы небыло конфликтов и ошибок
    def CheckingRequiredValuesInTheDataBase(self, ShiftTask) -> bool:
        # Проверка основных полей на None значение
        progressbar = IncrementalBar()
        app.logger.info(
            f"Валидация обязательных значений сменного задания № {ShiftTask.Ordinal}")
        args_cantbe_null = {"Shift": ShiftTask.Shift,
                            "Equipment": ShiftTask.Equipment,
                            "ProductCode": ShiftTask.ProductCode,
                            "Specification": ShiftTask.Specification,
                            "PackingCount": ShiftTask.PackingCount,
                            "SocketCount": ShiftTask.SocketCount,
                            "ProductCount": ShiftTask.ProductCount,
                            "Cycle": ShiftTask.Cycle,
                            "Weight": ShiftTask.Weight}
        keys_list = list(args_cantbe_null.keys())
        progressbar.max = len(keys_list)
        for key in keys_list:
            progressbar.message = f"Валидация self.{key}"
            progressbar.next()
            if (args_cantbe_null[key] != None):
                continue
            else:
                error = f"Значение self.{key} в сменном задании №{ShiftTask.Ordinal} является None, что недопустимо."
                app.logger.critical(f"Ошибка: {error}")
                raise Exception(error)
        progressbar.finish()
        app.logger.info("Валидация полей закончена.")

        # Поиск записей в базе данных от которых зависит сменное задание
        # чтобы предотвратить ошибки вставки записи сменного задания в таблицу
        app.logger.info(
            f"Проверка наличия записей на которые ссылается сменное задание № {ShiftTask.Ordinal}:")
        app.logger.info(f"    Проверка наличия требуемых записей:")
        app.logger.info(f"        Проверка оборудования {ShiftTask.Equipment}")
        equipment_sql = f"""
            SELECT [Equipment].[Oid],
                EquipmentType.[Name]
            FROM [MES_Iplast].[dbo].[Equipment],EquipmentType WHERE 
                [Equipment].NomenclatureGroup = (SELECT [Oid] 
                                                FROM [NomenclatureGroup]
                                                WHERE [NomenclatureGroup].Code = '{ShiftTask.Equipment}') AND
                [Equipment].EquipmentType = 'CC019258-D8D7-4286-B2CD-706FA0A2DC9D' AND
                EquipmentType.Oid = Equipment.EquipmentType
        """
        equipment = SQLManipulator.SQLExecute(equipment_sql)
        if len(equipment) > 0:
            pass
        else:
            app.logger.warning(
                f"Ошибка: Сменное задание № {ShiftTask.Ordinal} - в базе данных отсутствует запись о оборудовании {ShiftTask.Equipment} ")
            return False
        if equipment[0][1] == "Термопластавтомат":
            app.logger.info(
                f"        Термопластавтомат {ShiftTask.Equipment} найден")
            app.logger.info(
                f"        Проверка продукта {ShiftTask.ProductCode}")
            productsql = f"""
                SELECT [Oid]
                FROM [MES_Iplast].[dbo].[Product] WHERE Code = '{ShiftTask.ProductCode}'
            """
            product = SQLManipulator.SQLExecute(productsql)
            if (len(product) > 0):
                app.logger.info(
                    f"        Продукт {ShiftTask.ProductCode} найден")
                app.logger.info(
                    f"        Проверка спецификации {ShiftTask.Specification}")
                get_spec_sql = f"""
                        SELECT [Oid]
                        FROM [MES_Iplast].[dbo].[ProductSpecification] WHERE Code = '{ShiftTask.Specification}'
                      """
                specification = SQLManipulator.SQLExecute(get_spec_sql)
                if len(specification) > 0:
                    app.logger.info(
                        f"        Спецификация {ShiftTask.Specification} найдена")
                    app.logger.info(
                        f"Валидация сменного задания № {ShiftTask.Specification} успешна.")
                    return True
                else:
                    ['SpecCode']
                    app.logger.warning(
                        f"Внимание: Сменное задание № {ShiftTask.Ordinal} - в базе данных отсутствует запись о спецификации {ShiftTask.Specification}")
                    app.logger.info(f"  Поиск спецификации {ShiftTask.Specification} в массиве 1С")
                    for specification_1C in self.data['Spec']:
                        spec1C_code = specification_1C['SpecCode']
                        if len(spec1C_code) < 11:
                            while len(spec1C_code) != 11:
                                spec1C_code = '0' + spec1C_code
                        if spec1C_code == ShiftTask.Specification:
                            app.logger.info(f"  Спецификация {ShiftTask.Specification} найдена")
                            isActive = 0
                            if specification_1C['IsActive'] == "Да":
                                isActive = 1
                            insert_specsql = f"""                            
                                INSERT INTO ProductSpecification 
                                    (Oid, Code, [Name], Product, UseFactor,IsActive) 
                                VALUES (NEWID(),'{spec1C_code}','{specification_1C['Spec']}',
                                    '{product[0][0]}',{float(specification_1C['UseFactor'])},
                                    {isActive})              
                                """
                            app.logger.info(f"  Сохранение спецификации {ShiftTask.Specification} в базе данных")
                            SQLManipulator.SQLExecute(insert_specsql)
                            break
                    app.logger.info(f"  Проверка наличия спецификации {ShiftTask.Specification} в базе данных")
                    specification = SQLManipulator.SQLExecute(get_spec_sql)
                    if len(specification) > 0:
                        app.logger.info(
                            f"        Спецификация {ShiftTask.Specification} найдена")
                        app.logger.info(
                            f"Валидация сменного задания № {ShiftTask.Specification} успешна.")
                        app.logger.info(f"\r\n")
                        return True
                    else:
                        app.logger.warning(
                            f"Ошибка: Сменное задание № {ShiftTask.Ordinal} - в базе данных отсутствует запись о спецификации {ShiftTask.Specification}")
                        return False
            else:
                app.logger.warning(
                    f"Ошибка: Сменное задание № {ShiftTask.Ordinal} - в базе данных отсутствует запись о продукте {ShiftTask.ProductCode} ")
                return False
        else:
            app.logger.warning(
                f"Ошибка: Сменное задание № {ShiftTask.Ordinal} - в базе данных отсутствует запись о оборудовании {ShiftTask.Equipment} ")
            return False

    # Главный метод который создаёт записи сменных заданий
    def InsertToDataBase(self) -> bool:
        # Задаём начальные переменные
        shiftsql = ""
        shift = self.Determine_Shift()
        shift_name = None
        start_date = None
        end_date = None
        # Проверяем длинну списка сменных заданий
        if len(self.shift_task_list) == 0:
            # Если заданий нет
            app.logger.warning(
                "В списке отсутсвуют сменные задания для выгрузки")
            return
        else:
            # Если есть то единожды в название смены
            # указываем смену сменного задания
            shift_name = self.shift_task_list[0].Shift
        # Если день то ищем дневную дату смены
        if shift == 0:
            shiftsql = """
                SELECT [Oid]
                    ,[StartDate]
                    ,[EndDate]
                    ,[Note]
                FROM [MES_Iplast].[dbo].[Shift] WHERE 
                    DATENAME(HOUR, [StartDate]) >= 7 AND 
                    DATENAME(YEAR, [StartDate]) = DATENAME(YEAR, GETDATE()) AND
                    DATENAME(MONTH, [StartDate]) = DATENAME(MONTH, GETDATE()) AND
                    DATENAME(DAY, [StartDate]) = DATENAME(DAY, GETDATE())
                        """
        # Если ночь то ищем ночную дату смены
        elif shift == 1:
            shiftsql = """
                SELECT [Oid]
                    ,[StartDate]
                    ,[EndDate]
                    ,[Note]
                FROM [MES_Iplast].[dbo].[Shift] WHERE 
                    DATENAME(HOUR, [StartDate]) >= 19 AND 
                    DATENAME(YEAR, [StartDate]) = DATENAME(YEAR, GETDATE()) AND
                    DATENAME(MONTH, [StartDate]) = DATENAME(MONTH, GETDATE()) AND
                    DATENAME(DAY, [StartDate]) = DATENAME(DAY, GETDATE())
                        """
        getshift = SQLManipulator.SQLExecute(shiftsql)
        if len(getshift) == 0:
            if shift == 0:
                start_date = datetime.datetime(datetime.datetime.now().year,
                                               datetime.datetime.now().month,
                                               datetime.datetime.now().day,
                                               7, 0, 0).strftime("%Y-%m-%d %H:%M:%S")
                end_date = datetime.datetime(datetime.datetime.now().year,
                                             datetime.datetime.now().month,
                                             datetime.datetime.now().day,
                                             19, 0, 0).strftime("%Y-%m-%d %H:%M:%S")
                insertshiftsql = f"""
                set language english
                INSERT INTO [Shift] (Oid,StartDate,EndDate,Note) 
                VALUES (NEWID(),
                        Cast('{start_date}' AS DATETIME),
                        Cast('{end_date}' AS DATETIME),
                        '{shift_name}')
                """
                SQLManipulator.SQLExecute(insertshiftsql)
            elif shift == 1:
                start_date = datetime.datetime(datetime.datetime.now().year,
                                               datetime.datetime.now().month,
                                               datetime.datetime.now().day,
                                               19, 0, 0).strftime("%Y-%m-%d %H:%M:%S")
                end_date = datetime.datetime(datetime.datetime.now().year,
                                             datetime.datetime.now().month,
                                             datetime.datetime.now().day+1,
                                             7, 0, 0).strftime("%Y-%m-%d %H:%M:%S")
                insertshiftsql = f"""
                set language english
                INSERT INTO [Shift] (Oid,StartDate,EndDate,Note) 
                VALUES (NEWID(),
                        Cast('{start_date}' AS DATETIME),
                        Cast('{end_date}' AS DATETIME),
                        '{shift_name}')
                """
                SQLManipulator.SQLExecute(insertshiftsql)
            getshift = SQLManipulator.SQLExecute(shiftsql)
            self.InsertShiftTask(getshift, self.shift_task_list)
        return

    # Метод ищет сменное задание по номенклатурной группе
    # и json файлу со сменными заданиями далее сменное задание проходит
    # валидацию полей во избежания ошибок до создания самой записи
    # валидация так же пишет в консоль отчёт об ошибке, тобишь какие поля небыли
    # найдены в БД
    def Find_ShiftTask(self, NomenclatureGroup, file_data):
        data = file_data
        self.shift_task_parsed = data
        task_id = 0
        for task in self.shift_task_parsed['Order']:
            SpecificationCodeCorrection = task['SpecCode']
            if len(SpecificationCodeCorrection) < 11:
                while len(SpecificationCodeCorrection) != 11:
                    SpecificationCodeCorrection = '0' + SpecificationCodeCorrection
            if ((task['oid'] == NomenclatureGroup) or
                    (self.nomenclature_group == "")):
                ShiftTask = ShiftTaskModel(task_id,
                                           task['Shift'],
                                           task['oid'],
                                           task['ProductCode'],
                                           SpecificationCodeCorrection,
                                           "",
                                           "",
                                           task['Packing'],
                                           task['PackingCount'],
                                           task['Socket'],
                                           task['ProductPlan'],
                                           task['ProductCycle'],
                                           task['ProductWeight'],
                                           task['nomencURL'],
                                           task['normUpacURL'],
                                           task['ShiftTask']
                                           )
                if (self.CheckingRequiredValuesInTheDataBase(ShiftTask)):
                    self.shift_task_list.append(ShiftTask)

    def InsertShiftTask(self, shift, tasklist):
        # Проходим по всем сменным заданиям в списке прошедших валидацию
        # Находим необходимые поля которые ссылаются на другие таблицы в БД
        # и создаём записи сменных заданий
        for task in tasklist:
            null_count = 0
            for i in task.Ordinal:
                if i == '0':
                    null_count += 1
                else:
                    break
            task.Ordinal = task.Ordinal[null_count:]
            shiftOid = shift[0][0]

            product = f"""
                    SELECT [Oid]
                        ,[Code]
                        ,[Name]
                        ,[Article]
                    FROM [MES_Iplast].[dbo].[Product] 
                    WHERE Code = '{task.ProductCode}'    
                """
            product = SQLManipulator.SQLExecute(product)[0][0]

            equipment = f"""
                    SELECT [Equipment].[Oid],
                        EquipmentType.[Name]
                    FROM [MES_Iplast].[dbo].[Equipment],EquipmentType WHERE 
                        [Equipment].NomenclatureGroup = (
                            SELECT [Oid] 
                            FROM [NomenclatureGroup]
                            WHERE [NomenclatureGroup].Code = '{task.Equipment}') AND
                    [Equipment].EquipmentType = 'CC019258-D8D7-4286-B2CD-706FA0A2DC9D' AND
                    EquipmentType.Oid = Equipment.EquipmentType
                """
            equipment_oid = SQLManipulator.SQLExecute(equipment)[0][0]

            specification = f"""
                    SELECT [Oid]
                    FROM [MES_Iplast].[dbo].[ProductSpecification] 
                    WHERE Code = '{task.Specification}'
                """
            specification = SQLManipulator.SQLExecute(specification)[0][0]

            ShiftTaskInsertSQL = f"""
                    INSERT INTO [ShiftTask] (
                            Oid,
                            [Shift],
                            Equipment,
                            Ordinal,
                            Product,
                            Specification,
                            Traits,
                            ExtraTraits,
                            PackingScheme,
                            PackingCount,
                            SocketCount,
                            ProductCount,
                            Cycle,
                            [Weight],
                            ProductURL,
                            PackingURL)
                    VALUES (NEWID(),
                        '{shiftOid}',
                        '{equipment_oid}',
                         {task.Ordinal},
                        '{product}',
                        '{specification}',
                        '{task.Traits}',
                        '{task.ExtraTraits}',
                        '{task.PackingScheme}',
                         {task.PackingCount},
                         {task.SocketCount},
                         {task.ProductCount},
                         {task.Cycle},
                         {float(task.Weight.replace(',','.'))},
                        '{task.ProductURL}',
                        '{task.PackingURL}')
                    """
            app.logger.info("Вставка сменного задания №" + task.Ordinal)
            SQLManipulator.SQLExecute(ShiftTaskInsertSQL)
