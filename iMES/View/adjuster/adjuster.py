from iMES import app
from flask_login import login_required
from iMES.functions.CheckRolesForInterface import CheckRolesForInterface

# Метод возвращает окно наладчика
@app.route('/adjuster')
@login_required
def adjuster():
    return CheckRolesForInterface('Наладчик','adjuster/adjuster.html')
