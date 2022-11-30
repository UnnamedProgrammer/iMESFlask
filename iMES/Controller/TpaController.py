from iMES.Controller.ShiftTaskDataGrubber import ShiftTaskDataGrubber
from iMES.Controller.TpaErrorsChecker import TpaErrorsChecker

class TpaController(TpaErrorsChecker,ShiftTaskDataGrubber):
    def __init__(self,_TpaOid) -> None:
        ShiftTaskDataGrubber.__init__(self)
        self.Controller = self
        self.tpa = _TpaOid