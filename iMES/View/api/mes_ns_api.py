from iMES import app
import json 
from iMES import tpasresultapi
import time

@app.route('/api/tpainfo')
def tpainfo():
    return json.dumps(build_tpa_data(list(tpasresultapi)))


def build_tpa_data(tpas: list):
    tpadata = []
    for tpa in tpasresultapi:
        update_tpa(tpa, tpadata)
    return tpadata

def update_tpa(tpa, tpadata):
    MesState = tpa['Controller'].state
    pressform = tpa['Controller'].pressform
    if MesState == True:
        state = 'В работе'
    else:
        state = 'В простое'
    fact = 0
    plan = 0
    if isinstance(tpa['Controller'].product_fact,tuple):
        fact = tpa['Controller'].product_fact[0]
    else:
        fact = tpa['Controller'].product_fact
    if isinstance(tpa['Controller'].production_plan,tuple):
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
            'fact':str(fact),
            'plan':str(plan),
            'sync_id': tpa['Controller'].sync_oid
        }
    )