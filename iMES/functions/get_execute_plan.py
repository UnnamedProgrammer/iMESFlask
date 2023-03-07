from iMES.Controller.TpaController import TpaController
from iMES.Model.SQLManipulator import SQLManipulator
from datetime import datetime, timedelta


def get_execute_plan(current_tpa: TpaController):
    try:
        get_last_closure_sql = f"""
            SELECT TOP (1)
                [StartDate]
                ,[CountFact]
                ,[CycleFact]
                ,[EndDate]
            FROM [MES_Iplast].[dbo].[ProductionData] WHERE ShiftTask = '{current_tpa.shift_task_oid[0]}'
        """
        get_last_closure = SQLManipulator.SQLExecute(get_last_closure_sql)
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
