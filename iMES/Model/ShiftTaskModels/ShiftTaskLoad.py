"""Модуль для работы со сменными заданиями."""

import requests
import json
from iMES.Model.DataBaseModels.EquipmentModel import Equipment
from iMES.Model.DataBaseModels.EquipmentPerformanceModel import EquipmentPerformance
from iMES.Model.DataBaseModels.NomenclatureGroupModel import NomenclatureGroup
from iMES.Model.DataBaseModels.ProductModel import Product
from iMES.Model.DataBaseModels.ProductSpecificationModel import ProductSpecification
from iMES.Model.DataBaseModels.Relation_ProductPerformanceModel import Relation_ProductPerformance
from iMES.Model.DataBaseModels.ShiftTaskModel import ShiftTask
from iMES.Model.ShiftTaskModels.ShiftTaskModel import ShiftTaskModel
from iMES.Model.DataBaseModels.EquipmentTypeModel import EquipmentType
from iMES.Model.DataBaseModels.ShiftModel import Shift
from iMES import db
from sqlalchemy import extract, insert
import datetime
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

    def __init__(self, _nomenclature_group, _date: int, _shift: int, _app):
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
        self.app = _app

    # Метод парсит сменные задания в зависимости от переданного аргумента
    # _nomenclature_group и добавляет их в список self.shift_task_list
    def Get_ShiftTask(self) -> list:
        self.data = self.ShiftTask_Update()
        if self.data == '':
            self.app.logger.critical("Ошибка 1С при выгрузке сменного задания.")
            sys.exit()
        if isinstance(self.nomenclature_group, list):
            for NomGroup in self.nomenclature_group:
                self.Find_ShiftTask(NomGroup, self.data)
        elif isinstance(self.nomenclature_group, str):
            self.Find_ShiftTask(self.nomenclature_group, self.data)

    # Делает запрос в веб-сервис 1С получая json файл, парсит его
    # и возвращает в виде dict
    def ShiftTask_Update(self):
        json_data = requests.get(
            f"""http://work2-appserv-8.ipt.ls:4439/IplMES/hs/MES/GetProductionAssignment2?Date={str(self.date)}000000&Smena={str(self.shift)}""")
        with open('st.json', 'wb') as file_json:
            file_json.write(json_data.content)
            file_json.close()
        try:
            with open('st.json', 'r', encoding='utf-8-sig') as file_json:
                load_file = json.load(file_json)[0]
        except:
            with open('st.json', 'r', encoding='windows-1251',errors='ignore') as file_json:
                load_file = file_json.read()
                self.app.logger.critical(load_file)
                return ''
        return load_file

    # Определяет какое сейчас время суток, если в shift аргумент класса
    # было передано 3 то метод используется автоматически
    def Determine_Shift(self) -> int:
        # 0 - День, 1 - Ночь
        now = datetime.datetime.now()
        hour = now.hour
        if (hour >= 0 and hour < 7) or (hour >= 19 and hour <= 23):
            return 1
        elif hour >= 7 and hour < 19:
            return 0

    # Метод самопроверки значений класса перед вставкой в базу данных
    # Некоторые поля в таблице являются FK которые ссылаются на другие таблицы
    # В связи с этим нужно проверить есть ли зависимые значения в других таблицах
    # чтобы небыло конфликтов и ошибок
    def CheckingRequiredValuesInTheDataBase(self, ShiftTask) -> bool:
        # Проверка основных полей на None значение
        self.app.logger.info(
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
        for key in keys_list:
            if (args_cantbe_null[key] != None):
                continue
            else:
                error = f"Значение self.{key} в сменном задании №{ShiftTask.Ordinal} является None, что недопустимо."
                self.app.logger.critical(f"Ошибка: {error}")
                raise Exception(error)
        self.app.logger.info("Валидация полей закончена.")

        # Поиск записей в базе данных от которых зависит сменное задание
        # чтобы предотвратить ошибки вставки записи сменного задания в таблицу
        self.app.logger.info(
            f"Проверка наличия записей на которые ссылается сменное задание № {ShiftTask.Ordinal}:")
        self.app.logger.info(f"    Проверка наличия требуемых записей:")
        self.app.logger.info(f"        Проверка оборудования {ShiftTask.Equipment}")
        equipment = (db.session.query(Equipment.Oid, 
                                      EquipmentType.Name)
                                      .select_from(Equipment, EquipmentType)
                                      .where(Equipment.NomenclatureGroup == 
                                          db.session.query(NomenclatureGroup.Oid)
                                          .where(NomenclatureGroup.Code == ShiftTask.Equipment)
                                          .one_or_none()[0])
                                      .where(Equipment.EquipmentType == 'CC019258-D8D7-4286-B2CD-706FA0A2DC9D')
                                      .where(EquipmentType.Oid == Equipment.EquipmentType)
                                      .all())
        if len(equipment) > 0:
            pass
        else:
            self.app.logger.warning(
                f"Ошибка: Сменное задание № {ShiftTask.Ordinal} - в базе данных отсутствует запись об оборудовании {ShiftTask.Equipment} ")
            return False
        if equipment[0][1] == "Термопластавтомат":
            self.app.logger.info(
                f"        Термопластавтомат {ShiftTask.Equipment} найден")
            self.app.logger.info(
                f"        Проверка продукта {ShiftTask.ProductCode}")
            while True:
                product = db.session.query(Product.Oid).where(
                    Product.Code == ShiftTask.ProductCode).all()
                if (len(product) > 0):
                    self.app.logger.info(
                        f"        Продукт {ShiftTask.ProductCode} найден")
                    self.app.logger.info(
                        f"        Проверка спецификации {ShiftTask.Specification}")
                    specification = db.session.query(ProductSpecification.Oid).where(
                        ProductSpecification.Code == ShiftTask.Specification).all()
                    if len(specification) > 0:
                        self.app.logger.info(
                            f"        Спецификация {ShiftTask.Specification} найдена")
                        self.app.logger.info(
                            f"Валидация сменного задания № {ShiftTask.Specification} успешна.")
                        return True
                    else:
                        self.app.logger.warning(
                            f"Внимание: Сменное задание № {ShiftTask.Ordinal} - в базе данных отсутствует запись о спецификации {ShiftTask.Specification}")
                        self.app.logger.info(f"  Поиск спецификации {ShiftTask.Specification} в массиве 1С")
                        for specification_1C in self.data['Spec']:
                            spec1C_code = specification_1C['SpecCode']
                            if len(spec1C_code) < 11:
                                while len(spec1C_code) != 11:
                                    spec1C_code = '0' + spec1C_code
                            if spec1C_code == ShiftTask.Specification:
                                self.app.logger.info(f"  Спецификация {ShiftTask.Specification} найдена")
                                isActive = 0
                                if specification_1C['IsActive'] == "Да":
                                    isActive = 1
                                try:
                                    self.app.logger.info(f"  Сохранение спецификации {ShiftTask.Specification} в базе данных")    
                                    insert_spec = ProductSpecification()
                                    insert_spec.Code = spec1C_code
                                    insert_spec.Name = specification_1C['Spec']
                                    insert_spec.Product = product[0][0]
                                    insert_spec.UseFactor = float(specification_1C['UseFactor'])
                                    insert_spec.isActive = isActive
                                    db.session.add(insert_spec)
                                    db.session.commit()
                                except Exception as error:
                                    self.app.logger.error(
                                        f"[{datetime.datetime.now()}] <CheckingRequiredValuesInTheDataBase> {str(error)}")
                                break
                        self.app.logger.info(f"  Проверка наличия спецификации {ShiftTask.Specification} в базе данных")
                        if len(specification) > 0:
                            self.app.logger.info(
                                f"        Спецификация {ShiftTask.Specification} найдена")
                            self.app.logger.info(
                                f"Валидация сменного задания № {ShiftTask.Specification} успешна.")
                            self.app.logger.info(f"\r\n")
                            return True
                        else:
                            self.app.logger.warning(
                                f"Ошибка: Сменное задание № {ShiftTask.Ordinal} - в базе данных отсутствует запись о спецификации {ShiftTask.Specification}")
                            return False
                else:
                    self.app.logger.warning(
                        f"Ошибка: Сменное задание № {ShiftTask.Ordinal} - в базе данных отсутствует запись о продукте {ShiftTask.ProductCode} ")
                    self.app.logger.info(
                        f"Сменное задание № {ShiftTask.Ordinal} - вставка нового продукта {ShiftTask.ProductCode} в базу данных")
                    new_product = Product()
                    new_product.Code = ShiftTask.ProductCode
                    new_product.Name = ShiftTask.Product
                    new_product.Article = ShiftTask.Article
                    db.session.add(new_product)
                    db.session.commit()
                    self.app.logger.info(
                        f"Сменное задание № {ShiftTask.Ordinal} - Новый продукт {ShiftTask.ProductCode} добавлен в базу данных")
                    continue
        else:
            self.app.logger.warning(
                f"Ошибка: Сменное задание № {ShiftTask.Ordinal} - в базе данных отсутствует запись о оборудовании {ShiftTask.Equipment} ")
            return False

    # Главный метод который создаёт записи сменных заданий
    def InsertToDataBase(self, get_task_flag = False, to_current_shift = False) -> bool:
        # Задаём начальные переменные
        shift = self.Determine_Shift()
        shift_name = None
        start_date = None
        end_date = None
        
        # Проверяем длинну списка сменных заданий
        if len(self.shift_task_list) == 0:
            # Если заданий нет
            self.app.logger.warning(
                "В списке отсутсвуют сменные задания для выгрузки")
            return
        else:
            # Если есть то единожды в название смены
            # указываем смену сменного задания
            shift_name = self.shift_task_list[0].Shift
        # Если день то ищем дневную дату смены
        getshift = []
        if shift == 0:
            getshift = (db.session.query(Shift.Oid, Shift.Note)
             .filter(extract('hour', Shift.StartDate) == 7)
             .filter(extract('year', Shift.StartDate) == datetime.datetime.now().year)
             .filter(extract('month', Shift.StartDate) == datetime.datetime.now().month)
             .filter(extract('day', Shift.StartDate) == datetime.datetime.now().day).all())
        # Если ночь то ищем ночную дату смены
        elif shift == 1:
            getshift = (db.session.query(Shift.Oid, Shift.Note)
             .filter(extract('hour', Shift.StartDate) == 19)
             .filter(extract('year', Shift.StartDate) == datetime.datetime.now().year)
             .filter(extract('month', Shift.StartDate) == datetime.datetime.now().month)
             .filter(extract('day', Shift.StartDate) == datetime.datetime.now().day).all())
        if len(getshift) > 0:
            pass
        elif to_current_shift:
            for i in range(0,len(self.shift_task_list)):
                if self.shift_task_list[i].Cycle == '0':
                    product = (db.session.query(Product.Oid,
                                               Product.Code,
                                               Product.Name,
                                               Product.Article)
                                               .select_from(Product)
                                               .where(Product.Code == self.shift_task_list[i].ProductCode)
                                               .all()[0][0])

                    product_cycle = db.session.query(Relation_ProductPerformance.Cycle).where(
                        Relation_ProductPerformance.Product == product
                    ).all()
                    if bool(product_cycle):
                        self.shift_task_list[i].Cycle = str(product_cycle[0][0])
            self.InsertShiftTask(getshift[0][0], self.shift_task_list, get_tasks_flag=get_task_flag)
        else:
            if shift == 0:
                shift_delta = datetime.timedelta(hours=12)
                start_date = datetime.datetime(datetime.datetime.now().year,
                                               datetime.datetime.now().month,
                                               datetime.datetime.now().day,
                                               7, 0, 0)
                end_date = start_date + shift_delta
                start_date = start_date.strftime("%Y-%m-%dT%H:%M:%S")
                end_date = end_date.strftime("%Y-%m-%dT%H:%M:%S")
                
                insert_shift = Shift()
                insert_shift.StartDate = start_date
                insert_shift.EndDate = end_date
                insert_shift.Note = shift_name
                db.session.add(insert_shift)
                db.session.commit()
                getshift = db.session.query(
                    Shift.Oid).select_from(
                        Shift).where(Shift.StartDate == start_date).where(
                            Shift.EndDate == end_date).all()
            elif shift == 1:
                shift_delta = datetime.timedelta(hours=12)
                start_date = datetime.datetime(datetime.datetime.now().year,
                                               datetime.datetime.now().month,
                                               datetime.datetime.now().day,
                                               19, 0, 0)
                
                end_date = start_date + shift_delta
                start_date = start_date.strftime("%Y-%m-%dT%H:%M:%S")
                end_date = end_date.strftime("%Y-%m-%dT%H:%M:%S")

                insert_shift = Shift()
                insert_shift.StartDate = start_date
                insert_shift.EndDate = end_date
                insert_shift.Note = shift_name
                db.session.add(insert_shift)
                db.session.commit()
                getshift = db.session.query(
                    Shift.Oid).select_from(
                        Shift).where(Shift.StartDate == start_date).where(
                            Shift.EndDate == end_date).all()
                self.LoadEquipmentPerfomance(self.shift_task_list,self.data)
        # Определение цикла для прокдукта в сменном задании
        for i in range(0,len(self.shift_task_list)):
            if self.shift_task_list[i].Cycle == '0':
                product = (db.session.query(Product.Oid,
                            Product.Code,
                            Product.Name,
                            Product.Article)
                            .select_from(Product)
                            .where(Product.Code == self.shift_task_list[i].ProductCode)
                            .all()[0][0])

                product_cycle = db.session.query(Relation_ProductPerformance.Cycle).where(
                    Relation_ProductPerformance.Product == product
                ).all()
                if bool(product_cycle):
                    self.shift_task_list[i].Cycle = str(product_cycle[0][0])

        if get_task_flag == False:        
            self.InsertShiftTask(getshift[0][0], self.shift_task_list, get_tasks_flag=get_task_flag)
            return
        else:     
            shift_task_list = self.InsertShiftTask(
                getshift, self.shift_task_list, get_tasks_flag=get_task_flag)      
            return shift_task_list

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
            if (((task['oid'] == NomenclatureGroup) or
                (self.nomenclature_group == "")) and 'Socket' in task):

                traits = ""
                extratraits = ""
                if len(task["Characteristic"]) > 0:
                    dict_keys = [*task["Characteristic"].keys()]
                    for key in dict_keys:
                        traits = traits + f"{key}: {task['Characteristic'][key]}, "
                if len(task["Ingredient"]) > 0:
                    extratraits = task["Ingredient"]

                ShiftTask = ShiftTaskModel(task_id,
                                           task['Shift'],
                                           task['oid'],
                                           task['ProductCode'],
                                           SpecificationCodeCorrection,
                                           traits,
                                           extratraits,
                                           task['Packing'],
                                           task['PackingCount'],
                                           task['Socket'],
                                           task['ProductPlan'],
                                           task['ProductCycle'],
                                           task['ProductWeight'],
                                           task['nomencURL'],
                                           task['normUpacURL'],
                                           task['ShiftTask'],
                                           task['Product'],
                                           task['Articul'],
                                           task['WorkCenter']
                                           )
                if (self.CheckingRequiredValuesInTheDataBase(ShiftTask)):
                    self.shift_task_list.append(ShiftTask)

    def InsertShiftTask(self, shift, tasklist, get_tasks_flag):
        # Проходим по всем сменным заданиям в списке прошедших валидацию
        # Находим необходимые поля которые ссылаются на другие таблицы в БД
        # и создаём записи сменных заданий
        get_tasks_list = []
        for task in tasklist:
            null_count = 0
            for i in task.Ordinal:
                if i == '0':
                    null_count += 1
                else:
                    break
            task.Ordinal = task.Ordinal[null_count:]
            shiftOid = shift

            product = (db.session.query(Product.Oid,
                        Product.Code,
                        Product.Name,
                        Product.Article)
                        .select_from(Product)
                        .where(Product.Code == task.ProductCode)
                        .all()[0][0])

            equipment_oid = (db.session.query(Equipment.Oid, 
                                        EquipmentType.Name)
                                        .select_from(Equipment, EquipmentType)
                                        .where(Equipment.NomenclatureGroup == 
                                            db.session.query(NomenclatureGroup.Oid)
                                            .where(NomenclatureGroup.Code == task.Equipment)
                                            .one_or_none()[0])
                                        .where(Equipment.EquipmentType == 'CC019258-D8D7-4286-B2CD-706FA0A2DC9D')
                                        .where(EquipmentType.Oid == Equipment.EquipmentType)
                                        .all()[0][0])


            specification = db.session.query(ProductSpecification.Oid).where(
                        ProductSpecification.Code == task.Specification).all()[0][0]   
            if not get_tasks_flag:
                self.app.logger.info("Вставка сменного задания №" + task.Ordinal)
                if ',' in task.ProductCount: 
                    task.ProductCount = task.ProductCount.split(',')[0]               
                insert_new_shift_task = ShiftTask()
                insert_new_shift_task.Shift = shiftOid
                insert_new_shift_task.Equipment = equipment_oid
                insert_new_shift_task.Ordinal = int(task.Ordinal)
                insert_new_shift_task.Product = product
                insert_new_shift_task.Specification = specification
                insert_new_shift_task.Traits = task.Traits
                insert_new_shift_task.ExtraTraits = task.ExtraTraits
                insert_new_shift_task.PackingScheme = task.PackingScheme
                insert_new_shift_task.PackingCount = task.PackingCount
                insert_new_shift_task.SocketCount = task.SocketCount
                insert_new_shift_task.ProductCount = task.ProductCount
                insert_new_shift_task.Cycle = task.Cycle
                insert_new_shift_task.Weight = float(task.Weight.replace(',','.'))
                insert_new_shift_task.ProductURL = task.ProductURL
                insert_new_shift_task.PackingURL = task.PackingURL
                insert_new_shift_task.WorkCenter = task.WorkCenter
                db.session.add(insert_new_shift_task)
                db.session.commit()
            else:
                get_tasks_list.append(('NOID',
                                        shiftOid,
                                        equipment_oid,
                                        task.Ordinal,
                                        product,
                                        specification,
                                        task.Traits,
                                        task.ExtraTraits,
                                        task.PackingScheme,
                                        task.PackingCount,
                                        task.SocketCount,
                                        task.ProductCount,
                                        task.Cycle,
                                        float(task.Weight.replace(',','.')),
                                        task.ProductURL,
                                        task.PackingURL,
                                        task.WorkCenter))
        if get_tasks_flag:
            return get_tasks_list

    def LoadEquipmentPerfomance(self,tasklist,jsondata):
        for task in tasklist:
            for EP in jsondata["EquipmentPerformance"]:
                if (EP["ProductCode"] == task.ProductCode):
                    for ep in EP["EquipmentPerformance"]:
                        nomenclaturegroup_oid = (db.session.query(NomenclatureGroup.Oid)
                                                                      .select_from(NomenclatureGroup)
                                                                      .where(NomenclatureGroup.Code == EP['NomenclatureGroupCode'])
                                                                      .all()[0][0])
                        main_equipment_oid = (db.session.query(Equipment.Oid)
                                                              .select_from(Equipment)
                                                              .where(NomenclatureGroup.Code == EP['NomenclatureGroupCode'])
                                                              .where(Equipment.NomenclatureGroup == NomenclatureGroup.Oid)
                                                              .where(Equipment.EquipmentType == 'CC019258-D8D7-4286-B2CD-706FA0A2DC9D')
                                                              .all[0])
                        rig_equipment_oid = (db.session.query(Equipment.Oid).where(Equipment.Code == ep["EquipmentPerformance"]).all()[0])
                        total_socket_count = ep["TotalSocketCount"]

                        finded_ep = (db.session.query(EquipmentPerformance.Oid)
                                          .where(EquipmentPerformance.NomenclatureGroup == nomenclaturegroup_oid)
                                          .where(EquipmentPerformance.MainEquipment == main_equipment_oid)
                                          .where(EquipmentPerformance.RigEquipment == rig_equipment_oid)
                                          .where(EquipmentPerformance.TotalSocketCount == int(total_socket_count))
                                          .all())
                        if len(finded_ep) > 0:
                            product_oid = db.session.query(Product.Oid).where(Product.Code == EP["ProductCode"]).all()[0][0]
                            relation_product_ep = (db.session.query(Relation_ProductPerformance.EquipmentPerformance)
                                                                    .where(Relation_ProductPerformance.EquipmentPerformance == finded_ep[0][0])
                                                                    .where(Relation_ProductPerformance.Product == product_oid)
                                                                    .where(Relation_ProductPerformance.SocketCount == int(ep['SocketCount']))
                                                                    .where(Relation_ProductPerformance.Cycle == float(ep['Cycle'].replace(',','.')))
                                                                    .all())
                            if (len(relation_product_ep) > 0):
                                continue
                            else:
                                try:
                                    new_rel_ep = Relation_ProductPerformance()
                                    new_rel_ep.EquipmentPerformance = finded_ep[0][0]
                                    new_rel_ep.Product = product_oid
                                    new_rel_ep.SocketCount = int(ep['SocketCount'])
                                    new_rel_ep.Cycle = float(ep['Cycle'].replace(',','.'))
                                    db.session.add(new_rel_ep)
                                    db.session.commit()
                                except Exception as error:
                                    self.app.logger.error(f"[{datetime.datetime.now()}] <LoadEquipmentPerfomance> {str(error)}")
                                    continue
                        else:
                            product_oid = ""
                            new_ep = EquipmentPerformance()
                            new_ep.NomenclatureGroup = nomenclaturegroup_oid
                            new_ep.MainEquipment = main_equipment_oid
                            new_ep.RigEquipment = rig_equipment_oid
                            new_ep.TotalSocketCount = int(total_socket_count)
                            db.session.add(new_ep)
                            db.session.commit()
                            ep_oid = (db.session.query(EquipmentPerformance.Oid)
                                                                 .where(EquipmentPerformance.NomenclatureGroup == nomenclaturegroup_oid)
                                                                 .where(EquipmentPerformance.MainEquipment == main_equipment_oid)
                                                                 .where(EquipmentPerformance.RigEquipment == rig_equipment_oid)
                                                                 .where(EquipmentPerformance.TotalSocketCount == int(total_socket_count))
                                                                 .all())
                            if len(ep_oid) > 0:
                                ep_oid = ep_oid[0][0]
                            else: continue
                            product_oid = db.session.quer(Product.Oid).where(Product.Code == EP["ProductCode"]).all()[0][0]
                            relation_product_ep = (db.session.query(Relation_ProductPerformance.EquipmentPerformance)
                                                                    .where(Relation_ProductPerformance.EquipmentPerformance == ep_oid)
                                                                    .where(Relation_ProductPerformance.Product == product_oid)
                                                                    .where(Relation_ProductPerformance.SocketCount == int(ep['SocketCount']))
                                                                    .where(Relation_ProductPerformance.Cycle == float(ep['Cycle'].replace(',','.')))
                                                                    .all())
                            if (len(relation_product_ep) > 0):
                                continue
                            else:
                                insert_rel_ep_sql = Relation_ProductPerformance()
                                insert_rel_ep_sql.EquipmentPerformance = ep_oid
                                insert_rel_ep_sql.Product = product_oid
                                insert_rel_ep_sql.SocketCount = int(ep['SocketCount'])
                                insert_rel_ep_sql.Cycle = float(ep['Cycle'].replace(',','.'))
                                db.session.add(insert_rel_ep_sql)
                                db.session.commit()
        