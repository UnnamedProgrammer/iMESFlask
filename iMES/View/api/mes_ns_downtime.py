from iMES import app, TpaList, db 
from flask import request
from iMES.Model.DataBaseModels.DowntimeFailureModel import DowntimeFailure as DF
from iMES.Model.DataBaseModels.TakenMeasuresModel import TakenMeasures as TM
from iMES.Model.DataBaseModels.MalfunctionDescriptionModel import MalfunctionDescription as MDesc
from iMES.Model.DataBaseModels.MalfunctionCauseModel import MalfunctionCause as MCause
from iMES.Model.DataBaseModels.EmployeeModel import Employee
from iMES.Model.DataBaseModels.UserModel import User


@app.route('/api/downtime')
def get_downtime_list():
    tpa_oid = request.args.getlist('oid')[0]
    df_list = {}
    for tpa in TpaList:
        if tpa[0] == tpa_oid.lower():
            df = (db.session.query(DF.Oid,
                                DF.Equipment,
                                DF.StartDate,
                                DF.EndDate,
                                MCause.Name,
                                MDesc.Name,
                                TM.Name,
                                DF.Note,
                                DF.CreateDate,
                                Employee.LastName,
                                Employee.FirstName,
                                Employee.MiddleName)
                                .select_from(DF, Employee, User)
                                .outerjoin(MCause)
                                .outerjoin(MDesc)
                                .outerjoin(TM)
                                .outerjoin(Employee)
                                .where(User.Oid == DF.Creator)
                                .where(DF.Equipment == tpa[0])
                                .order_by(DF.StartDate.desc())
                                .all())
            if len(df) > 0:
                df_list[tpa[0]] = []
                for downtime in df:
                    if ((downtime[9] is None) or 
                        (downtime[10] is None) or 
                        (downtime[11] is None)):
                        creator = 'system'
                    else:
                        creator = f"{downtime[9]} {downtime[10]} {downtime[11]}"
                    end_date = ''
                    if downtime[3] is not None:
                        end_date = downtime[3].strftime("%Y.%m.%d %H.%M.%S") 
                    df_list[tpa[0]].append({
                        'oid': downtime[0],
                        'StartDate': downtime[2].strftime("%Y.%m.%d %H.%M.%S"),
                        'EndDate': end_date,
                        'MalfunctionCause': downtime[4],
                        'MalfunctionDescription': downtime[5],
                        'TakenMesures': downtime[6],
                        'Note': downtime[7],
                        'CreateDate': downtime[8].strftime("%Y.%m.%d %H.%M.%S"),
                        'Creator': creator
                    })
    return df_list
                
    