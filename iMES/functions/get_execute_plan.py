from iMES.Controller.TpaController import TpaController
from datetime import datetime, timedelta
from iMES.Model.DataBaseModels.ProductionDataModel import ProductionData
from iMES import db, app


def get_execute_plan(current_tpa: TpaController):
    with app.app_context():
        try:
            get_last_closure = (db.session.query(ProductionData.StartDate,
                                                ProductionData.CountFact,
                                                ProductionData.CycleFact,
                                                ProductionData.EndDate)
                                                .where(ProductionData.ShiftTask == current_tpa.shift_task_oid[0])
                                                .first())
            remaining_quantity = current_tpa.production_plan[0] - \
                get_last_closure[0][1]
            production_time = (get_last_closure[0][2] / 60)
            minutes_to_plan_end = remaining_quantity * production_time
            old_diff_time = datetime.now() - get_last_closure[0][3]
            end_date = (
                datetime.now() + timedelta(minutes=float(minutes_to_plan_end))) - old_diff_time
            return str(end_date - datetime.now())
        except:
            return ""
