from iMES.Model.SQLManipulator import SQLManipulator

class BaseObjectModel(SQLManipulator):
    def __init__(self) -> None:
        SQLManipulator.__init__(SQLManipulator)
        pass
        