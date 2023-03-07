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
            if tpa['Controller'].tpa == tpa_oid:
                finded_tpa = tpa
        if finded_tpa is not None:
            return get_graph_data_by_ctpa(finded_tpa['Controller'])
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
            if tpa['Controller'].tpa == tpa_oid:
                MesState = tpa['Controller'].state
                pressform = tpa['Controller'].pressform
                if isinstance(tpa['Controller'].production_plan, int):
                    data = [{
                        "Oid": tpa['Controller'].tpa,
                        "Name": tpa['Name'],
                        "MESState": MesState,
                        "EAMState": None,
                        "ExecPlan": get_execute_plan(tpa['Controller']),
                        "PressForm": pressform,
                        "Product": tpa['Controller'].product,
                        "Plan": tpa['Controller'].production_plan,
                        "Fact": tpa['Controller'].product_fact,
                        "plan_cycle": tpa['Controller'].cycle,
                        "fact_cycle": tpa['Controller'].cycle_fact,
                        "plan_weight": tpa['Controller'].plan_weight,
                        "average_weight": tpa['Controller'].average_weight,
                        "tpa_syncid": tpa['Controller'].sync_oid
                    }]
                else:
                    data = [{
                        "Oid": tpa['Controller'].tpa,
                        "Name": tpa['Name'],
                        "MESState": MesState,
                        "EAMState": None,
                        "ExecPlan": get_execute_plan(tpa['Controller']),
                        "PressForm": pressform,
                        "Product": list(tpa['Controller'].product),
                        "Plan": list(tpa['Controller'].production_plan),
                        "Fact": list(tpa['Controller'].product_fact),
                        "plan_cycle": tpa['Controller'].cycle,
                        "fact_cycle": tpa['Controller'].cycle_fact,
                        "plan_weight": list(tpa['Controller'].plan_weight),
                        "average_weight": list(tpa['Controller'].average_weight),
                        "tpa_syncid": tpa['Controller'].sync_oid
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
    MesState = tpa['Controller'].state
    pressform = tpa['Controller'].pressform
    if MesState is True:
        state = 'В работе'
    else:
        state = 'В простое'
    if isinstance(tpa['Controller'].product_fact, tuple):
        fact = tpa['Controller'].product_fact[0]
    else:
        fact = tpa['Controller'].product_fact
    if isinstance(tpa['Controller'].production_plan, tuple):
        plan = tpa['Controller'].production_plan[0]
    else:
        plan = tpa['Controller'].production_plan
    tpadata.append(
        {
            'TpaOid': tpa['Controller'].tpa,
            'Name': tpa['Name'],
            'EamState': None,
            'MesState': state,
            'PressForm': pressform,
            'fact': str(fact),
            'plan': str(plan),
            'sync_id': tpa['Controller'].sync_oid
        }
    )
