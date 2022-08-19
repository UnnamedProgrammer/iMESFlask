from iMES import app
from flask_login import login_required
from iMES.functions.CheckRolesForInterface import CheckRolesForInterface

# Отображение окна оператора
@app.route('/operator')
@login_required
def operator():
    return CheckRolesForInterface('Оператор','operator/operator.html')

# Отображение окна сменного задания
@app.route('/operator/ShiftTask')
@login_required
def OperatorShiftTask():
    return CheckRolesForInterface('Оператор','operator/ShiftTask.html')
