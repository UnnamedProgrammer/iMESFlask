from iMES.Model.BaseObjectModel import BaseObjectModel
from datetime import datetime

class TpaErrorsChecker(BaseObjectModel):
    """
        Класс отвечающий за проверку ошибок на ТПА, простои, отсутствующая 
        прессформа и прочие ошибки
    """
    def __init__(self, _app,_tpaoid) -> None:
        BaseObjectModel.__init__(self,_app)
        self.errors: list = []
        self.block_downtime: bool = False
        self.tpaoid: str = _tpaoid
        self.current_downtime_oids: list = []
    
    def _update_downtime_list(self):
        error_string = "УКАЖИТЕ ПРИЧИНУ ПРОСТОЯ."
        fail_list = self.SQLExecute(f"""
            SELECT [Oid]
            FROM [MES_Iplast].[dbo].[DowntimeJournal]
            WHERE Status = 0 AND Equipment = '{self.tpaoid}'
        """)
        if len(fail_list) > 0:
            self.current_downtime_oids.clear()
            for row in fail_list:
                self.current_downtime_oids.append(row[0])
            if not self._is_message_in_errors(error=error_string):
                self._add_error_message(error=error_string) 
        else:
            self._remove_error_message(error=error_string)
            return []
    
    def _add_error_message(self,error) -> None:
        time = datetime.now().strftime('%Y.%m.%d %H:%M:%S')
        self.errors.append({"Date":time, "Message":error})

    def _remove_error_message(self,error) -> None:
        for elem in self.errors:
            if elem["Message"] == error:
                self.errors.remove(elem)
    
    def _is_message_in_errors(self,error) -> bool:
        for elem in self.errors:
            if elem["Message"] == error:
                return True
        return False
        
    def _is_downtime_created(self,date) -> bool:
        time = date.strftime('%Y-%m-%dT%H:%M:%S')
        sql = self.SQLExecute(f"""
            SELECT [Oid],Equipment
            FROM [MES_Iplast].[dbo].[DowntimeJournal]
            WHERE StartDate = '{time}'
            """
        )
        if len(sql) > 0:
            return True
        else:
            return False
        

    def _create_downtime(self,date) -> None:
        time = date.strftime('%Y-%m-%dT%H:%M:%S')
        self.SQLExecute(f"""
        INSERT INTO [DowntimeJournal](Oid, Equipment, StartDate, EndDate, Status) 
        VALUES (NEWID(), '{self.tpaoid}','{time}',NULL,0)
        """)

    def Check_Downtime(self,tpaoid) -> bool:
        if tpaoid == None or tpaoid == '':
            return False
        self._update_downtime_list()
        sql = f"""
            SELECT TOP(1) [Date],Controller,[RFIDEquipmentBinding].RFIDEquipment
            FROM [MES_Iplast].[dbo].[RFIDClosureData], Equipment, [RFIDEquipmentBinding]
            WHERE 
                Equipment.Oid = '{tpaoid}' AND
                [RFIDEquipmentBinding].Equipment = Equipment.Oid AND
                [RFIDClosureData].Controller = [RFIDEquipmentBinding].RFIDEquipment
            ORDER BY Date DESC
        """
        last_closure_date = self.SQLExecute(sql)
        if len(last_closure_date) > 0:
            last_closure_date = last_closure_date[0][0]
            current_date = datetime.now()
            seconds = (current_date - last_closure_date).total_seconds()
            if seconds >= 400:
                if (self.block_downtime == False):
                    if not self._is_downtime_created(last_closure_date):
                        self._create_downtime(last_closure_date)
                        self.block_downtime = True
                return False
            else:
                self.block_downtime = False
                return True
        else:
            if (self.block_downtime == False):
                if not self._is_downtime_created(last_closure_date):
                    self._create_downtime(last_closure_date)
                    self.block_downtime = True
            return False