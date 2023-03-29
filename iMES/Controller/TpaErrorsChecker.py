from datetime import datetime
from iMES import db
from iMES.Model.DataBaseModels.DowntimeFailureModel import DowntimeFailure
from iMES.Model.DataBaseModels.EquipmentModel import Equipment
from iMES.Model.DataBaseModels.EquipmentPerformanceModel import EquipmentPerformance
from iMES.Model.DataBaseModels.RFIDClosureDataModel import RFIDClosureData
from iMES.Model.DataBaseModels.RFIDEquipmentBindingModel import RFIDEquipmentBinding
from iMES.Model.DataBaseModels.Relation_ProductPerformanceModel import Relation_ProductPerformance
from iMES.Model.DataBaseModels.UserModel import User
from iMES.Model.DataBaseModels.DowntimeTypeModel import DowntimeType

class TpaErrorsChecker():
    """
        Класс отвечающий за проверку ошибок на ТПА, простои, отсутствующая 
        прессформа и прочие ошибки
    """
    def __init__(self, _app,_tpaoid) -> None:
        self.app_link = _app
        self.errors: list = []
        self.block_downtime: bool = False
        self.tpaoid: str = _tpaoid
        self.current_downtime_oids: list = []
        self.system_user = (db.session.query(User.Oid).where(User.UserName == 'mes.system').all())
        if len(self.system_user) > 0:
            self.system_user = self.system_user[0][0]
        else:
            self.system_user = None
        self.error_string_const = "УКАЖИТЕ ПРИЧИНУ ПРОСТОЯ."
        self.error_pressform_string_const = "ПРЕССФОРМА НЕ СООТВЕТСВУЕТ ПРОДУКТУ."
        self.pressform_error = False
        self.need_pressform_oid = ""

    def __update_downtime_list(self):
        with self.app_link.app_context():
            fail_list = (db.session.query(DowntimeFailure.Oid,
                                        DowntimeFailure.StartDate)
                                        .select_from(DowntimeFailure)
                                        .where(DowntimeFailure.Creator == self.system_user)
                                        .where(DowntimeFailure.Equipment == self.tpaoid)
                                        .where(DowntimeFailure.EndDate == None)
                                        .all())
            if len(fail_list) > 0:
                self.current_downtime_oids.clear()
                self.current_downtime_oids.append(fail_list[0][0])
                if not self.__is_message_in_errors(self.error_string_const):
                    self.__add_error_message(self.error_string_const,fail_list[0][1])
            else:
                self.__remove_error_message(error=self.error_string_const)
                return []
    
    def __add_error_message(self,error,date) -> None:
        time = date.strftime('%Y.%m.%d %H:%M:%S')
        self.errors.append({"Date":time, "Message":error})

    def __remove_error_message(self,error) -> None:
        for elem in self.errors:
            if elem["Message"] == error:
                self.errors.remove(elem)
    
    def __is_message_in_errors(self,error) -> bool:
        for elem in self.errors:
            if elem["Message"] == error:
                return True
        return False
        
    def __is_downtime_created(self,date) -> bool:
        with self.app_link.app_context():
            time = date.strftime('%Y-%m-%dT%H:%M:%S')
            existing_downtime = (db.session.query(DowntimeFailure.Oid, 
                                                DowntimeFailure.Equipment)
                                                .where(DowntimeFailure.StartDate == time)
                                                .all())
            if len(existing_downtime) > 0:
                return True
            else:
                return False
        

    def __create_downtime(self,date) -> None:
        with self.app_link.app_context():
            time = date.strftime('%Y-%m-%dT%H:%M:%S')
            if len(self.system_user) > 0:
                downtime_type = (db.session.query(DowntimeType.Oid)
                                                .select_from(DowntimeType)
                                                .where(DowntimeType.Name == 'Не задан')
                                                .all())
                if len(downtime_type) > 0:
                    downtime_type = downtime_type[0][0]
                    new_downtime = DowntimeFailure()
                    new_downtime.Equipment = self.tpaoid
                    new_downtime.StartDate = time
                    new_downtime.EndDate = None
                    new_downtime.DowntimeType = downtime_type
                    new_downtime.MalfunctionCause = None
                    new_downtime.MalfunctionDescription = None
                    new_downtime.TakenMeasures = None
                    new_downtime.Note = None
                    new_downtime.CreateDate = time
                    new_downtime.Creator = self.system_user
                    db.session.add(new_downtime)
                    db.session.commit()
                    return True
                else:
                    self.app.logger.error(f"[{datetime.now()}] <__create_downtime> Тип простоя 'Не задан' отсутсвует, операция отменена.")
            else:
                self.app.logger.error(f"[{datetime.now()}] <__create_downtime> Отсутсвует системный пользователь, операция отменена.")
            return False

    def Check_Downtime(self,tpaoid) -> bool:
        with self.app_link.app_context():
            if tpaoid == None or tpaoid == '':
                return False
            self.__update_downtime_list()
            last_closure_date = (db.session.query(RFIDClosureData.Date,
                                                RFIDClosureData.Controller,
                                                RFIDEquipmentBinding.RFIDEquipment)
                                                .select_from(RFIDClosureData, Equipment, RFIDEquipmentBinding)
                                                .where(Equipment.Oid == tpaoid)
                                                .where(RFIDEquipmentBinding.Equipment == Equipment.Oid)
                                                .where(RFIDClosureData.Controller == RFIDEquipmentBinding.RFIDEquipment)
                                                .order_by(RFIDClosureData.Date.desc())
                                                .first())
            if (len(last_closure_date) > 0):
                last_closure_date = last_closure_date[0]
                current_date = datetime.now()
                seconds = (current_date - last_closure_date).total_seconds()
                fails_without_reason = (db.session.query(DowntimeFailure.Oid,
                                                        DowntimeFailure.StartDate)
                                                        .select_from(DowntimeFailure)
                                                        .where(DowntimeFailure.Creator == self.system_user)
                                                        .where(DowntimeFailure.Equipment == self.tpaoid)
                                                        .where(DowntimeFailure.MalfunctionCause == None)
                                                        .order_by(DowntimeFailure.StartDate.desc())
                                                        .all())
                if len(fails_without_reason) > 0:
                    if not self.__is_message_in_errors(error=self.error_string_const):
                        self.__add_error_message(self.error_string_const,fails_without_reason[0][1]) 
                if seconds >= 400:
                    if not self.__is_downtime_created(last_closure_date):
                        self.__create_downtime(last_closure_date)
                    return False
                else:
                    if len(self.current_downtime_oids) > 0:
                        df = db.session.query(DowntimeFailure).where(DowntimeFailure.Oid == self.self.current_downtime_oids[0]).one_or_none()
                        if df is not None:
                            df.EndDate = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
                            db.session.commit()
                        self.current_downtime_oids.remove(self.current_downtime_oids[0])
                    return True
            else:
                return False
    
    def Check_pressform(self):
        with self.app_link.app_context():
            if self.product == 'Нет сменного задания':
                return
            for i in range(0, len(self.product_oids)):
                equipment_perfomance = (db.session.query(Relation_ProductPerformance.EquipmentPerformance)
                                                        .select_from(Relation_ProductPerformance)
                                                        .where(Relation_ProductPerformance.Product == self.product_oids[i])
                                                        .all())
                if len(equipment_perfomance) > 0:     
                    rig_from_ep = (db.session.query(EquipmentPerformance.RigEquipment)
                                                    .where(EquipmentPerformance.Oid == equipment_perfomance[0][0])
                                                    .all())
                    if len(rig_from_ep) > 0:
                        self.need_pressform_oid = rig_from_ep[0][0]
                        if self.pressform_oid == rig_from_ep[0][0]:
                            self.__remove_error_message(self.error_pressform_string_const)
                            self.pressform_error = False
                        else:
                            if not self.__is_message_in_errors(self.error_pressform_string_const):
                                self.__add_error_message(self.error_pressform_string_const,datetime.now())
                                self.pressform_error = True
