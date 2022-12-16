from iMES.Model.BaseObjectModel import BaseObjectModel
from datetime import datetime

class TpaErrorsChecker(BaseObjectModel):
    """
        Класс отвечающий за проверку ошибок на ТПА, простои, отсутствующая 
        прессформа и прочие ошибки
    """
    def __init__(self, _app,_tpaoid) -> None:
        BaseObjectModel.__init__(self,_app)
        self.app_link = _app
        self.errors: list = []
        self.block_downtime: bool = False
        self.tpaoid: str = _tpaoid
        self.current_downtime_oids: list = []
        self.system_user = self.SQLExecute("""
            SELECT [Oid] FROM [User] WHERE UserName = 'mes.system'
        """)
        if len(self.system_user) > 0:
            self.system_user = self.system_user[0][0]
        else:
            self.system_user = None
        self.error_string_const = "УКАЖИТЕ ПРИЧИНУ ПРОСТОЯ."
    
    def _update_downtime_list(self):
        fail_list = self.SQLExecute(f"""
            SELECT [Oid], StartDate 
            FROM [MES_Iplast].[dbo].[DowntimeFailure]
            WHERE Creator = '{self.system_user}' AND Equipment = '{self.tpaoid}'
        """)
        if len(fail_list) > 0:
            self.current_downtime_oids.clear()
            self.current_downtime_oids.append(fail_list[0][0])
            if not self._is_message_in_errors(self.error_string_const):
                self._add_error_message(self.error_string_const,fail_list[0][1])
        else:
            self._remove_error_message(error=self.error_string_const)
            return []
    
    def _add_error_message(self,error,date) -> None:
        time = date.strftime('%Y.%m.%d %H:%M:%S')
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
            FROM [MES_Iplast].[dbo].[DowntimeFailure]
            WHERE StartDate = '{time}'
            """
        )
        if len(sql) > 0:
            return True
        else:
            return False
        

    def _create_downtime(self,date) -> None:
        time = date.strftime('%Y-%m-%dT%H:%M:%S')
        if len(self.system_user) > 0:
            dowtime_type = self.SQLExecute("""
                SELECT [Oid] FROM DowntimeType WHERE Name = 'Не задан'
            """)
            if len(dowtime_type) > 0:
                dowtime_type = dowtime_type[0][0]
                self.SQLExecute(f"""
                    INSERT INTO DowntimeFailure (Oid,
                                    Equipment,
                                    StartDate,
                                    EndDate,
                                    DowntimeType,
                                    MalfunctionCause,
                                    MalfunctionDescription,
                                    TakenMeasures,
                                    Note,
                                    CreateDate,
                                    Creator)
                    VALUES (NEWID(),
                            '{self.tpaoid}',
                            '{time}',
                            NULL,
                            '{dowtime_type}',
                            NULL,
                            NULL,
                            NULL,
                            NULL,
                            '{time}',
                            '{self.system_user}')
                """)
                return True
            else:
                self.app.logger.warning(f"[{datetime.now()}] Тип простоя 'Не задан' отсутсвует, операция отменена.")
        else:
            self.app.logger.warning(f"[{datetime.now()}] Отсутсвует системный пользователь, операция отменена.")
        return False

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
                if not self._is_downtime_created(last_closure_date):
                    if self._create_downtime(last_closure_date):
                        if not self._is_message_in_errors(error=self.error_string_const):
                            self._add_error_message(self.error_string_const,last_closure_date) 
                return False
            else:
                if len(self.current_downtime_oids) > 0:
                    self.SQLExecute(f"""
                        UPDATE [DowntimeFailure]
                        SET EndDate = '{datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}'
                        WHERE Oid = '{self.current_downtime_oids[0]}'
                    """)
                return True
        else:
            return False