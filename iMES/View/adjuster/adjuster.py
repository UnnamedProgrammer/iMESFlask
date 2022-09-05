from iMES import app
from flask_login import login_required
from iMES.functions.CheckRolesForInterface import CheckRolesForInterface

# Метод возвращает окно наладчика
@app.route('/adjuster')
@login_required
def adjuster():
    return CheckRolesForInterface('Наладчик','adjuster/adjuster.html')

# Сырье до конца выпуска 
@app.route('/adjuster/RawMaterials')
@login_required
def adjusterRawMaterials():
    return CheckRolesForInterface('Наладчик','adjuster/rawMaterials.html')

# Фиксация отхода и брака
@app.route('/adjuster/WasteDefectFix')
@login_required
def adjusterWasteDefectFix():
    return CheckRolesForInterface('Наладчик','adjuster/wasteDefectFix.html')

# Сменное задание
@app.route('/adjuster/shiftTask')
@login_required
def adjusterShiftTask():
    return CheckRolesForInterface('Наладчик','adjuster/shiftTask.html')

