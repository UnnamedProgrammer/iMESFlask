from iMES import app
from flask_login import login_required
from iMES.functions.CheckRolesForInterface import CheckRolesForInterface

# Отображение окна оператора


@app.route('/operator')
@login_required
def operator():
    return CheckRolesForInterface('Оператор', 'operator/operator.html')

@login_required
@app.route('/operator/tableWasteDefect')
def tableWasteDefect():
    return CheckRolesForInterface('Оператор', 'operator/tableWasteDefect/tableWasteDefect.html')

@login_required
@app.route('/operator/tableWasteDefect/wastes')
def wastes():
    return CheckRolesForInterface('Оператор', 'operator/tableWasteDefect/wastes.html')


@login_required
@app.route('/operator/tableWasteDefect/wastes/anotherWastes')
def otherWastes():
    return CheckRolesForInterface('Оператор', 'operator/tableWasteDefect/anotherWastes.html')


# Отображение окна сменного задания


@app.route('/operator/ShiftTask')
@login_required
def OperatorShiftTask():
    return CheckRolesForInterface('Оператор', 'operator/ShiftTask.html')

# Изменение этикетки


@app.route('/operator/ChangeLabel')
@login_required
def OperatorChangeLabel():
    return CheckRolesForInterface('Оператор', 'operator/changeLabel.html')

# Схема упаковки


@app.route('/operator/PackingScheme')
@login_required
def OperatorPackingScheme():
    return CheckRolesForInterface('Оператор', 'operator/packingScheme.html')
