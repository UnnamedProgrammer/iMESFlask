from sqlalchemy import extract
from iMES import app, db
from datetime import date

from iMES.Model.DataBaseModels.EquipmentModel import Equipment
from iMES.Model.DataBaseModels.MaterialModel import Material
from iMES.Model.DataBaseModels.ProductModel import Product
from iMES.Model.DataBaseModels.ProductWasteModel import ProductWaste
from iMES.Model.DataBaseModels.ProductWeightModel import ProductWeight
from iMES.Model.DataBaseModels.ProductionDataModel import ProductionData
from iMES.Model.DataBaseModels.ShiftModel import Shift
from iMES.Model.DataBaseModels.NomenclatureGroupModel import NomenclatureGroup
from iMES.Model.DataBaseModels.ProductSpecificationModel import ProductSpecification

import json

from iMES.Model.DataBaseModels.ShiftTaskModel import ShiftTask

@app.route('/1CUnlouding/Date=<string:date_time>/STNumber=<string:stnum>')
def UnloudingTo1C(date_time,stnum):
    # Убираем лишние нули так как в базе номер сменки без нулей
    data = []
    ordinal = ''
    slc = 0
    for i in stnum:
        if i == '0':
            slc += 1
        else:
            break
    ordinal = stnum[slc:]
    # Ищем в базе смену в зависимости от даты
    date_time = date(int(date_time[:-4]),int(date_time[4:-2]),int(date_time[6:]))
    shift = (db.session.query(Shift.Oid, Shift.Note)
             .filter(extract('year', Shift.StartDate) == date_time.year)
             .filter(extract('month', Shift.StartDate) == date_time.month)
             .filter(extract('day', Shift.StartDate) == date_time.day).all())
    # Если нашли смену то ищем сменные задания с заданным номером и сменой
    if len(shift) > 0:
        full_task_list = []
        if len(shift) == 1:
            shift_tasks = (db.session.query(ShiftTask.Oid,
                                            ShiftTask.Shift,
                                            ShiftTask.Equipment,
                                            ShiftTask.Product,
                                            ShiftTask.Specification,
                                            ShiftTask.ProductCount,
                                            ShiftTask.Cycle,
                                            ShiftTask.Weight,
                                            ShiftTask.Weight,
                                            ShiftTask.SocketCount,
                                            )
                                            .where(ShiftTask.Ordinal == ordinal)
                                            .where(ShiftTask.Shift == shift[0][0])
                                            .all())
            full_task_list = shift_tasks
        # Проходим по каждому сменному заданию и ищем все данные связанные с ним
        pd = []
        count = 0
        for task in full_task_list:
            # Поиск номенклатуры ТПА
            nomenclature_code = \
                (db.session.query(NomenclatureGroup.Name,
                                  NomenclatureGroup.Name)
                                  .select_from(NomenclatureGroup, Equipment)
                                  .where(Equipment.Oid == task[2])
                                  .where(NomenclatureGroup.Oid == Equipment.NomenclatureGroup)
                                  .all())
                                  
            # Поиск продукта сменки
            product = (db.session.query(Product.Oid,
                                       Product.Code,
                                       Product.Name,
                                       Product.Article)
                                       .select_from(Product)
                                       .where(Product.Oid == task[3]).all())

            # Поиск данных по произведенному продукту
            production_data = (db.session.query(ProductionData.Oid,
                                               ProductionData.ShiftTask,
                                               ProductionData.RigEquipment,
                                               ProductionData.Status,
                                               ProductionData.StartDate,
                                               ProductionData.EndDate,
                                               ProductionData.CountFact,
                                               ProductionData.CycleFact,
                                               ProductionData.WeightFact,
                                               ProductionData.SpecificationFact)
                                               .select_from(ProductionData)
                                               .where(ProductionData.ShiftTask == task[0])
                                               .all())
            
            if len(product) > 0:
                pass
            else:
                return f'В сменном задании {task[0]} не указан продукт.'
                
            if len(nomenclature_code) > 0:
                spec = (db.session.query(ProductSpecification.Oid,
                                         ProductSpecification.Code,
                                         ProductSpecification.Name,
                                         ProductSpecification.Product,
                                         ProductSpecification.UseFactor,
                                         ProductSpecification.isActive)
                                         .select_from(ProductSpecification)
                                         .where(ProductSpecification.Oid == task[4])
                                         .all())
                if len(spec) > 0:
                    pass
                else:
                    return f'В сменном задании {task[0]} неизвестная спецификация.'

                # Вставляем трафарет данных по сменному задания
                data.append({'oid':nomenclature_code[0][1],
                             'name':nomenclature_code[0][0],
                             'product_code': product[0][1],
                             'product': product[0][2],
                             'specefication': spec[0][2],
                             'specification_code': spec[0][1],
                             'plan': str(task[5]),
                             'weight': str(task[7]),
                             'shift': shift[0][1],
                             'cycle': str(task[6]),
                             'production_data': []})

                if len(production_data) > 0:
                    # Ищем все данные привязанные к production data
                    for pd in production_data:
                        # Получаем ПФ
                        rig_equipment = (db.session.query(Equipment.Oid,
                                                         Equipment.Code,
                                                         Equipment.Name,
                                                         Equipment.EquipmentType,
                                                         Equipment.Area,
                                                         Equipment.NomenclatureGroup,
                                                         Equipment.InventoryNumber,
                                                         Equipment.SyncId)
                                                         .select_from(Equipment)
                                                         .where(Equipment.Oid == pd[2])
                                                         .all())
                        # Получаем фактическую спецификацию
                        spec_fact = (db.session.query(ProductSpecification.Oid,
                                                      ProductSpecification.Code,
                                                      ProductSpecification.Name,
                                                      ProductSpecification.Product,
                                                      ProductSpecification.UseFactor,
                                                      ProductSpecification.isActive)
                                                      .select_from(ProductSpecification)
                                                      .where(ProductSpecification.Oid == pd[9])
                                                      .all())
                        # Заполняем лист отходов брака
                        wastes_list = []
                        prod_wastes = \
                            (db.session.query(ProductWaste.Oid,
                                            ProductWaste.ProductionData,
                                            ProductWaste.Material,
                                            ProductWaste.Type,
                                            ProductWaste.Weight,
                                            ProductWaste.Count,
                                            ProductWaste.Downtime,
                                            ProductWaste.Note,
                                            ProductWaste.CreateDate,
                                            ProductWaste.Creator)
                                            .select_from(ProductWaste)
                                            .where(ProductWaste.ProductionData == pd[0])
                                            .all())

                        if len(prod_wastes) > 0:
                            for waste in prod_wastes:
                                if waste[2] != None:
                                    material_data = (db.session.query(Material.Oid,
                                                                     Material.Code,
                                                                     Material.Name,
                                                                     Material.Article,
                                                                     Material.Type)
                                                                     .select_from(Material)
                                                                     .where(Material.Oid == waste[2])
                                                                     .all())
                                    if len(material_data) > 0 or waste[2] == None:
                                        typew = ''
                                        if waste[3] == 0:
                                            typew = 'Отход'
                                        else:
                                            typew = 'Брак'
                                        if typew == 'Отход':
                                            wastes_list.append(
                                                {
                                                    'wastes_name': material_data[0][2],
                                                    'wastes_code': material_data[0][1],
                                                    'type': typew,
                                                    'weight': str(waste[4]),
                                                    'create_date': waste[8].strftime('%Y-%m-%d %H:%M:%S')
                                                }                                     
                                            )
                                        elif typew == 'Брак':
                                            wastes_list.append(
                                                {
                                                    'type': typew,
                                                    'weight': str(waste[4]),
                                                    'count': str(waste[5]),
                                                    'create_date': waste[8].strftime('%Y-%m-%d %H:%M:%S')
                                                }                                     
                                            )
                                    else:
                                        return f'Неизвестная запись в [Material]'
                        # Заполняем данные по введёному весу
                        prod_weight_list = []
                        prod_weight = \
                            (db.session.query(ProductWeight.Oid,
                                            ProductWeight.ProductionData,
                                            ProductWeight.CreateDate,
                                            ProductWeight.CreateDate,
                                            ProductWeight.Creator)
                                            .select_from(ProductWeight)
                                            .where(ProductWeight.ProductionData == pd[0])
                                            .all())
                        if len(prod_weight) > 0:
                            for weight in prod_weight:
                                prod_weight_list.append({
                                    'weight': str(weight[2]),
                                    'create_date': weight[3].strftime('%Y-%m-%d %H:%M:%S')
                                })
                        if len(spec_fact) == 0:
                            return f'В productiondata {pd[0]} неизвестная спецификация'
                        else:
                            spec_fact = spec_fact[0]

                        # Вставляем все данные в трафарет
                        if len(rig_equipment) > 0:
                            data[count]['production_data'].append({'press_form': rig_equipment[0][2],
                                                                   'pressform_code': rig_equipment[0][1],
                                                                   'start_date': str(pd[4]),
                                                                   'end_date': str(pd[5]),
                                                                   'count_fact': str(pd[6]),
                                                                   'cycle_fact': str(pd[7]),
                                                                   'weight_fact': str(pd[8]),
                                                                   'spec_fact' : spec_fact[2],
                                                                   'spec_code_fact': spec_fact[1],
                                                                   'wastes': wastes_list,
                                                                   'entered_weight': prod_weight_list
                                                                  })
                        else:
                            return f'В productiondata {pd[0]} неизвестная ПФ'
            else:
                return 'В одном из сменных заданий нет номенклатурной группы.'
            count += 1   
    else:
        return 'Не удалось найти смену, возможно неверно указана дата.'
    # Возвращаем данные в виде json
    # флаг ensire_ascii нужен для отображаения символов отличных от ascii
    return json.dumps({'data': data}, ensure_ascii=False)