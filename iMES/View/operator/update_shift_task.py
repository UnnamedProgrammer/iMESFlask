from audioop import reverse
from iMES import app
from iMES import socketio,current_tpa
from flask_login import login_required, current_user
from flask import request
from iMES.Model.BaseObjectModel import BaseObjectModel
from datetime import datetime
from iMES.Model.ShiftTaskModels.ShiftTaskLoad import ShiftTaskLoader

@socketio.on('UpdateShiftTask')
def UpdateShiftTask(data):
    ip_addr = request.remote_addr
    current_shift = current_tpa[ip_addr][2].shift_oid
    get_shift_task_from_db_sql = f"""
        SELECT TOP (1000) [Oid]
            ,[Shift]
            ,[Equipment]
            ,[Ordinal]
            ,[Product]
            ,[Specification]
            ,[Traits]
            ,[ExtraTraits]
            ,[PackingScheme]
            ,[PackingCount]
            ,[SocketCount]
            ,[ProductCount]
            ,[Cycle]
            ,[Weight]
            ,[ProductURL]
            ,[PackingURL]
        FROM [MES_Iplast].[dbo].[ShiftTask] WHERE Shift = '{current_shift}'
    """
    now = datetime.now()
    year = str(now.year)
    month = str(now.month)
    day = str(now.day)
    if now.month < 10:
        month = '0' + month
    if now.day < 10:
        day = '0' + day

    get_equip_nomenclature_oid_sql = f"""
        SELECT [NomenclatureGroup]
        FROM [MES_Iplast].[dbo].[Equipment]
        WHERE Oid = '{current_tpa[ip_addr][2].tpaoid}'
    """
    nom_group_oid = BaseObjectModel.SQLExecute(get_equip_nomenclature_oid_sql)
    if len(nom_group_oid) > 0:
        nom_group_oid = nom_group_oid[0][0]
    nom_group_sql = f"""
        SELECT [Code]
        FROM [MES_Iplast].[dbo].[NomenclatureGroup] WHERE Oid = '{nom_group_oid}' 
    """
    nom_group_sql = BaseObjectModel.SQLExecute(nom_group_sql)
    if len(nom_group_sql) > 0:
        nom_group = nom_group_sql[0][0]
        date = int(str(year + month + day))
        Loader = ShiftTaskLoader(nom_group, date, 3, app)
        Loader.Get_ShiftTask()
        new_shift_tasks_list = Loader.InsertToDataBase(get_task_flag=True)
        print(new_shift_tasks_list.sort(reverse=True))
    # shift_task_list = BaseObjectModel.SQLExecute(get_shift_task_from_db_sql)
    # for shift_task in shift_task_list:
    #     print(shift_task, end="\n")