from iMES.Model.SQLManipulator import SQLManipulator
from progress.bar import IncrementalBar


class ShiftTaskModel():
    """
        Класс-модель сменного задания для выгрузки в базу данных.
        В поля должны вноситья типы данных аналогичным в базе данных iMES в таблице ShiftTask,
        но в коде питона в виде str()
        :param Shift - Oid Смены
        :param Equipment - Oid Оборудования (ТПА)
        :param Ordinal - None 
        :param Product - Код продукта
        :param Specification - Код спецификации
        :param Traits - None
        :param ExstraTraints - None
        :param PackingScheme - Текст схемы упаковки
        :param PackingCount - число продукта в упаковке
        :param SocketCount - Гнёздность пресс-формы
        :param ProductCount - План продукта
        :param Cycle - Цикл продукта
        :param Weight - Вес продукта
        :param ProductURL - URL на документ продукта в Directum
        :param PackingURL - URL на документ упаковки в Directum
    """
    ID = None
    Shift = None
    Equipment = None
    Ordinal = None
    Product = None
    Specification = None
    Traits = None
    ExstraTraints = None
    PackingScheme = None
    PackingCount = None
    SocketCount = None
    ProductCount = None
    Cycle = None
    Weight = None
    ProductURL = None
    PackingURL = None

    def __init__(self,
                _ID,
                _Shift,
                _Equipment,
                _Ordinal,
                _Product,
                _Specification,
                _Traits,
                _ExtraTraits,
                _PackingScheme,
                _PackingCount,
                _SocketCount,
                _ProductCount,
                _Cycle,
                _Weight,
                _ProductURL,
                _PackingURL):
        self.ID = _ID
        self.Shift = _Shift
        self.Equipment = _Equipment
        self.Ordinal = _Ordinal
        self.Product = _Product
        self.Specification = _Specification
        self.Traits = _Traits
        self.ExstraTraints = _ExtraTraits
        self.PackingScheme = _PackingScheme
        self.PackingCount = _PackingCount
        self.SocketCount = _SocketCount
        self.ProductCount = _ProductCount
        self.Cycle = _Cycle
        self.Weight = _Weight
        self.ProductURL = _ProductURL
        self.PackingURL = _PackingURL

    # Метод самопроверки значений класса перед вставкой в базу данных
    def CheckingRequiredValuesInTheDataBase(self) -> bool:
        # Проверка основных полей на None значение
        progressbar = IncrementalBar()
        print(f"Валидация обязательных значений сменного задания № {self.ID}")
        args_cantbe_null = {"Shift":self.Shift,
                            "Equipment":self.Equipment,
                            "Product":self.Product,
                            "Specification":self.Specification,
                            "PackingCount":self.PackingCount,
                            "SocketCount":self.SocketCount,
                            "ProductCount":self.ProductCount,
                            "Cycle":self.Cycle,
                            "Weight":self.Weight}
        keys_list = list(args_cantbe_null.keys())
        progressbar.max = len(keys_list)
        for key in keys_list:
            progressbar.message = f"Валидация self.{key}"
            progressbar.next()
            if (args_cantbe_null[key] != None):
                continue
            else:
                error = f"Значение self.{key} в сменном задании №{self.ID} является None, что недопустимо."
                print(f"Ошибка: {error}")
                raise Exception(error)
        progressbar.finish()
        print("Валидация полей закончена.")

        # Поиск записей в базе данных от которых зависит сменное задание
        # чтобы предотвратить ошибки вставки записи сменного задания в таблицу
        print(f"Проверка наличия записей на которые ссылается сменное задание № {self.ID}:",end="\n")
        print(f"    Проверка наличия требуемых записей:",end="\r\n")
        print(f"        Проверка оборудования {self.Equipment}")
        equipment_sql = """
            SELECT [Equipment].[Oid],
                EquipmentType.[Name]
            FROM [MES_Iplast].[dbo].[Equipment],EquipmentType WHERE 
                [Equipment].NomenclatureGroup = (SELECT [Oid] 
                                                FROM [NomenclatureGroup]
                                                WHERE [NomenclatureGroup].Code = '000000131') AND
                [Equipment].EquipmentType = 'CC019258-D8D7-4286-B2CD-706FA0A2DC9D' AND
                EquipmentType.Oid = Equipment.EquipmentType
        """
        equipment = SQLManipulator.SQLExecute(equipment_sql)
        if equipment[0][1] == "Термопластавтомат": 
            print(f"        Термопластавтомат {self.Equipment} найден", end="\n")              
            print(f"        Проверка продукта {self.Product}",end="\r\n")
            product = f"""
                SELECT [Oid]
                FROM [MES_Iplast].[dbo].[Product] WHERE Code = '{self.Product}'
            """
            if (len(product) > 0):
                print(f"        Продукт {self.Product} найден",end="\n")
                print(f"        Проверка спецификации {self.Specification}",end="\r\n")
                sql = f"""
                        SELECT [Oid]
                        FROM [MES_Iplast].[dbo].[ProductSpecification] WHERE Code = '{self.Specification}'
                      """
                specification = SQLManipulator.SQLExecute(sql)
                if len(specification > 0):
                    print(f"        Спецификация {self.Specification} найдена",end="\n")
                    print(f"Валидация сменного задания № {self.Specification} успешна.")
                    return True
            else:
                print(f"Ошибка: Сменное задание № {self.ID} - в базе данных отсутствует запись о продукте {self.Product} ")
                return False
        else:
            print(f"Ошибка: Сменное задание № {self.ID} - в базе данных отсутствует запись о оборудовании {self.Equipment} ")
            return False

    def InsertToDataBase(self):
        validate = self.CheckingRequiredValuesInTheDataBase()
        if validate == False:
            print("Всё ок")
        else:
            print("Ошибка")

    
        