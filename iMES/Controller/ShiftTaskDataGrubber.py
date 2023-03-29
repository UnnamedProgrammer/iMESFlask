from iMES.Model.DataBaseModels.EquipmentModel import Equipment
from iMES.Model.DataBaseModels.NomenclatureGroupModel import NomenclatureGroup
from iMES.Model.DataBaseModels.ProductModel import Product
from iMES.Model.DataBaseModels.ProductionDataModel import ProductionData
from iMES.Model.DataBaseModels.RFIDClosureDataModel import RFIDClosureData
from iMES.Model.DataBaseModels.RFIDEquipmentBindingModel import RFIDEquipmentBinding
from iMES import db, app
from iMES.Model.DataBaseModels.ShiftModel import Shift
from iMES.Model.DataBaseModels.ShiftTaskModel import ShiftTask
from iMES.Model.DataBaseModels.ProductSpecificationModel import ProductSpecification
from iMES.Model.DataBaseModels.ProductWasteModel import ProductWaste
from sqlalchemy import func

class ShiftTaskDataGrubber():
    """
        Класс отвечающий за хранение данных по выполняемому на данный момент
        сменному задания на определённом ТПА
    """
    def __init__(self,_app, _db) -> None:
        self.tpa = ''
        self.pressform = 'Не определена'
        self.production_plan = (0,)
        self.cycle = 0
        self.cycle_fact = 0
        self.plan_weight = (0,)
        self.average_weight = (0,)
        self.shift = ''
        self.shift_oid = ''
        self.shift_task_oid = ''
        self.product_fact = (0,)
        self.label = ''
        self.controller = 'Empty'
        self.PackingURL = ''
        self.StartDate = None
        self.EndDate = None
        self.ProductCount = 0
        self.wastes = (0,)
        self.shift_tasks_traits = ()
        self.specifications = []
        self.traits = ()
        self.product = ()
        self.product_oids = ()
        self.pressform_oid = ""
        self.defectives = ()
        self.PackingScheme = ""
        self.specName = ()
        self.WorkCenter = ""
        self.socket_count = ""
        self.TpaNomenclatureCode = ""
        self.sync_oid = ""
        self.state = False
        self.db = _db
        self.app = _app

    def update_pressform(self):
        # Проверка прессформы
        with self.app.app_context():
            if self.tpa != '':
                pf = None
                controller = self.db.session.query(RFIDEquipmentBinding).where(
                    RFIDEquipmentBinding.Equipment == self.tpa).first()
                if controller is not None:
                    pf = (self.db.session.query(Equipment.Name, 
                                        RFIDClosureData.Date, 
                                        Equipment.Oid)
                                        .select_from(Equipment, RFIDClosureData, RFIDEquipmentBinding)
                                        .where(RFIDClosureData.Controller == controller.RFIDEquipment)
                                        .where(RFIDEquipmentBinding.RFIDEquipment == RFIDClosureData.Label)
                                        .where(Equipment.Oid == RFIDEquipmentBinding.Equipment)
                                        .order_by(RFIDClosureData.Date.desc())
                                        .first()
                                        )
                else:
                    pf = []
                if pf is not None:
                    if len(pf) == 0:
                        pressform = 'Метка не привязана к прессформе'
                    else:
                        pressform = pf[0]
                        self.pressform_oid = pf[2]
                else:
                    pressform = 'Не определена'
                    self.pressform_oid = ""
                return pressform
            else:
                pressform = 'Не определена'
                return pressform
    

    # Метод получения данных из сменного задания
    def data_from_shifttask(self):
        with app.app_context():
            self.pressform = self.update_pressform()
            production_data = (db.session.query(ProductionData)
                                            .select_from(ProductionData, ShiftTask)
                                            .where(ProductionData.Status == 1)
                                            .where(ShiftTask.Equipment == self.tpa)
                                            .where(ProductionData.ShiftTask == ShiftTask.Oid)
                                            .order_by(ProductionData.StartDate.desc())
                                            .first())
            if production_data:
                data = db.session.query(ShiftTask).where(ShiftTask.Oid == production_data.ShiftTask).all()                                                 
                # Получение номенклатурной группы ТПА
                equipngroup = db.session.query(Equipment).where(Equipment.Oid == self.tpa).one_or_none()     
                if equipngroup is not None:
                    nomenclature = db.session.query(NomenclatureGroup).where(
                        NomenclatureGroup.Oid == equipngroup.NomenclatureGroup).one_or_none()
                    if nomenclature is not None:
                        self.TpaNomenclatureCode = nomenclature.Code
                    else:
                        self.TpaNomenclatureCode = ""
                else:
                    self.TpaNomenclatureCode = ""

                #---------------------------------------------------
                # Простая передача из БД в поля класса
                if data is not None:
                    st_oid = []
                    product_list = []
                    production_plan = []
                    plan_weight = []
                    traits = []
                    specs = []
                    traits_operator = []
                    product_oids = []
                    spec_names = []
                    for shift_task in data:
                        st_oid.append(shift_task.Oid)
                        product = db.session.query(Product).where(Product.Oid == shift_task.Product).one_or_none()
                        if product is not None:
                            product_list.append(product.Name)
                        production_plan.append(shift_task.ProductCount)
                        plan_weight.append(f"{float(shift_task.Weight):.{2}f}")
                        traits_operator.append(shift_task.Traits)
                        product_oids.append(shift_task.Product)
                        self.cycle = shift_task.Cycle
                        shift = db.session.query(Shift).order_by(Shift.StartDate.desc()).first()
                        self.shift = shift.Note
                        purls = shift_task.PackingURL.split(",")
                        for i in range(0, len(purls)):
                            self.PackingURL = purls[i][36:].replace(" ", "")
                        else:
                            self.PackingURL = purls[i][36:]
                        self.PackingScheme = shift_task.PackingScheme
                        self.shift_oid = shift_task.Shift
                        spec_code = db.session.query(ProductSpecification).where(
                            ProductSpecification.Oid == shift_task.Specification).one_or_none()
                        if spec_code is not None:
                            specs.append((spec_code.Code)[2:])
                            spec_names.append(spec_code.Name)

                    self.specifications = specs            
                    self.shift_task_oid = st_oid
                    self.product = tuple(product_list)
                    self.production_plan = tuple(production_plan)
                    self.plan_weight = tuple(plan_weight)
                    self.traits = tuple(traits_operator)
                    self.product_oids = tuple(product_oids)
                    self.specName = tuple(spec_names)
                    self.WorkCenter = shift_task.WorkCenter
                    self.socket_count = shift_task.SocketCount
                    for i in range(0,len(data)):
                        traits.append([self.product[i],
                                    f"{data[i].Traits} {data[i].ExtraTraits}",
                                    self.production_plan[i],
                                    self.cycle,
                                    self.plan_weight[i]])
                    self.shift_tasks_traits = tuple(traits)
                else:
                    self.shift_task_oid = ()
                    self.product = 'Нет сменного задания'
                    self.production_plan = 0
                    self.cycle = 0
                    self.plan_weight = 0
                    self.shift = shift.Note
                    self.shift_oid = shift.Oid

                if self.shift_task_oid != None and len(self.shift_task_oid) > 0:
                    product_data = []
                    product_data.append([production_data.CountFact, 
                                            production_data.CycleFact, 
                                            production_data.WeightFact,
                                            production_data.StartDate,
                                            production_data.EndDate])
                    if len(product_data) > 0:
                        product_fact = []
                        for pd in product_data:
                            self.StartDate = pd[3]
                            self.EndDate = pd[4]
                            if pd[0] == None:               
                                product_fact = [0]
                            else:
                                product_fact.append(pd[0])
                            if pd[1] == None:
                                self.cycle_fact = 0
                            else:
                                self.cycle_fact = f"{float(pd[1]):.{1}f}"
                        self.product_fact = tuple(product_fact)
                        self.ProductCount = len(self.product)
                average_weight = []
                wastes = []
                defectives = []
                average_weight_result = None
                if production_data is not None:
                    average_weight_result = production_data.WeightFact
                wastes_result = (db.session.query(func.sum(ProductWaste.Weight))
                                            .where(ProductWaste.ProductionData == production_data.Oid)
                                            .where(ProductWaste.Type == 0)
                                            .all())
                defectives_result = (db.session.query(func.sum(ProductWaste.Count))
                                            .where(ProductWaste.ProductionData == production_data.Oid)
                                            .where(ProductWaste.Type == 1)
                                            .all())
                if average_weight_result is not None:
                    average_weight.append(f"{float(average_weight_result):.{2}f}")
                else:
                    average_weight.append(f"{0.00:.{2}f}")
                if len(wastes_result) > 0:
                    if (wastes_result[0][0] != None):
                        wastes.append(f"{float(wastes_result[0][0]):.{0}f}")
                    else:
                        wastes.append(0)
                else:
                    wastes.append(0)
                
                if len(defectives_result) > 0 and defectives_result[0][0] != None:
                    defectives.append(int(defectives_result[0][0]))
                else:
                    defectives.append(0)

                self.wastes = tuple(wastes)
                self.average_weight = tuple(average_weight)
                self.defectives = tuple(defectives)
                controller = db.session.query(RFIDEquipmentBinding.RFIDEquipment).where(
                    RFIDEquipmentBinding.Equipment == self.tpa
                ).all()
                if len(controller) > 0:
                    self.controller = str(controller[0][0])
                else:
                    self.controller = 'Empty'