from iMES import app
from flask_login import login_required,current_user
from iMES.functions.CheckRolesForInterface import CheckRolesForInterface

@app.route('/operator')
@login_required
def operator():
    return CheckRolesForInterface('Оператор','operator/operator.html')


@app.route('/operator/ShiftTask')
@login_required
def OperatorShiftTask():
    return CheckRolesForInterface('Оператор','operator/ShiftTask.html')
