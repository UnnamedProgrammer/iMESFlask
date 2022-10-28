from iMES.Model.SQLManipulator import SQLManipulator
from progress.bar import IncrementalBar


class ShiftTaskModel(object):
    """
        Класс-модель сменного задания для выгрузки в базу данных.
        В поля должны вноситья типы данных аналогичным в базе данных iMES в таблице ShiftTask,
        но в коде питона в виде str()
        :param Shift - Oid Смены
        :param Equipment - Oid Оборудования (ТПА)
        :param ProductCode - Код продукта
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
    ProductCode = None
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
    Ordinal = None
    Product = None
    Articul = None
    ProductName = None

    def __init__(self,
                 _ID,
                 _Shift,
                 _Equipment,
                 _ProductCode,
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
                 _PackingURL,
                 _Ordinal,
                 _Product,
                 _Article):
                 
        self.ID = _ID
        self.Shift = _Shift
        self.Equipment = _Equipment
        self.ProductCode = _ProductCode
        self.Specification = _Specification
        self.Traits = _Traits
        self.ExtraTraits = _ExtraTraits
        self.PackingScheme = _PackingScheme
        self.PackingCount = _PackingCount
        self.SocketCount = _SocketCount
        self.ProductCount = _ProductCount
        self.Cycle = _Cycle
        self.Weight = _Weight
        self.ProductURL = _ProductURL
        self.PackingURL = _PackingURL
        self.Ordinal = _Ordinal
        self.Product = _Product
        self.Article = _Article
