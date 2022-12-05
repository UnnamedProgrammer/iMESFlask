from iMES.Controller.ShiftTaskDataGrubber import ShiftTaskDataGrubber
from iMES.Controller.TpaErrorsChecker import TpaErrorsChecker

class TpaController(TpaErrorsChecker,ShiftTaskDataGrubber):
    """
        Самый главный класс представляющий ТПА в интерфейсе программы
        информация из этого класса передаётся через сокет в интерфейс пользователя
    """
    def __init__(self,_app,_TpaOid) -> None:
        ShiftTaskDataGrubber.__init__(self,_app)
        self.Controller = self
        self.tpa = _TpaOid