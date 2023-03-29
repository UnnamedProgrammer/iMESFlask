from iMES import app
import json
from iMES import tpasresultapi
from flask import request
from iMES.functions.get_graph_data import get_graph_data_by_ctpa
from iMES.functions.get_execute_plan import get_execute_plan


@app.route('/api/tpainfo')
def tpainfo():
    return json.dumps(build_tpa_info())


@app.route('/api/get_graph')
def tpa_graph():
    tpa_oid = request.args.getlist('oid')
    if len(tpa_oid) > 0:
        tpa_oid = tpa_oid[0]
        finded_tpa = None
        for tpa in tpasresultapi:
            if tpa[2].tpa == tpa_oid:
                finded_tpa = tpa
        if finded_tpa is not None:
            return get_graph_data_by_ctpa(finded_tpa[2])
        else:
            return {'error': 'Неизвестный идентификатор.'}
    else:
        return {'error': 'В запросе отсутствует идентификатор'}


@app.route("/api/tpa_data")
def tpa_data():
    tpa_oid = request.args.getlist('oid')
    if len(tpa_oid) > 0:
        tpa_oid = tpa_oid[0]
        for tpa in tpasresultapi:
            if tpa[2].tpa == tpa_oid:
                MesState = tpa[2].state
                pressform = tpa[2].pressform
                if isinstance(tpa[2].production_plan, int):
                    data = [{
                        "Oid": tpa[2].tpa,
                        "Name": tpa[1],
                        "MESState": MesState,
                        "EAMState": None,
                        "ExecPlan": get_execute_plan(tpa[2]),
                        "PressForm": pressform,
                        "Product": tpa[2].product,
                        "Plan": tpa[2].production_plan,
                        "Fact": tpa[2].product_fact,
                        "plan_cycle": tpa[2].cycle,
                        "fact_cycle": tpa[2].cycle_fact,
                        "plan_weight": tpa[2].plan_weight,
                        "average_weight": tpa[2].average_weight,
                        "tpa_syncid": tpa[2].sync_oid
                    }]
                else:
                    data = [{
                        "Oid": tpa[2].tpa,
                        "Name": tpa[1],
                        "MESState": MesState,
                        "EAMState": None,
                        "ExecPlan": get_execute_plan(tpa[2]),
                        "PressForm": pressform,
                        "Product": list(tpa[2].product),
                        "Plan": list(tpa[2].production_plan),
                        "Fact": list(tpa[2].product_fact),
                        "plan_cycle": tpa[2].cycle,
                        "fact_cycle": tpa[2].cycle_fact,
                        "plan_weight": list(tpa[2].plan_weight),
                        "average_weight": list(tpa[2].average_weight),
                        "tpa_syncid": tpa[2].sync_oid
                    }]
                return data
        return {'error': 'Неизвестный идентификатор.'}
    else:
        return {'error': 'В запросе отсутствует идентификатор'}


def build_tpa_info():
    tpadata = []
    for tpa in tpasresultapi:
        update_tpa(tpa, tpadata)
    return tpadata


def update_tpa(tpa, tpadata):
    MesState = tpa[2].state
    pressform = tpa[2].pressform
    if MesState is True:
        state = 'В работе'
    else:
        state = 'В простое'
    if isinstance(tpa[2].product_fact, tuple):
        fact = tpa[2].product_fact[0]
    else:
        fact = tpa[2].product_fact
    if isinstance(tpa[2].production_plan, tuple):
        plan = tpa[2].production_plan[0]
    else:
        plan = tpa[2].production_plan
    tpadata.append(
        {
            'TpaOid': tpa[2].tpa,
            'Name': tpa['Name'],
            'EamState': None,
            'MesState': state,
            'PressForm': pressform,
            'fact': str(fact),
            'plan': str(plan),
            'sync_id': tpa[2].sync_oid
        }
    )
