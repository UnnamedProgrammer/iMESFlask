from iMES.Model.BaseObjectModel import BaseObjectModel

class TpaErrorsChecker(BaseObjectModel):
    """
        Класс отвечающий за проверку ошибок на ТПА, простои, отсутствующая 
        прессформа и прочие ошибки
    """
    def __init__(self) -> None:
        self.Controller = None
        self.errors = []

    def CheckShiftTask(self):
        pass

    def CheckPressFromForProduct(self):
        pass