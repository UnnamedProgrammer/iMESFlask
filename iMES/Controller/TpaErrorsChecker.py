from iMES.Model.BaseObjectModel import BaseObjectModel

class TpaErrorsChecker(BaseObjectModel):
    def __init__(self) -> None:
        self.Controller = None
        self.errors = []

    def CheckShiftTask(self):
        pass

    def CheckPressFromForProduct(self):
        pass