from iMES.Model.SQLManipulator import SQLManipulator

class BaseObjectModel(SQLManipulator):
    """
        Базовый класс для всех объектов в системе, его наследует любой класс,
        требуется для расширения логики объектов
    """
    def __init__(self,_app) -> None:
        SQLManipulator.__init__(SQLManipulator,_app)