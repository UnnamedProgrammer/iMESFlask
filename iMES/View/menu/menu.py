from iMES import app
from flask import render_template, request,redirect
from flask_login import login_required,current_user
from iMES import current_tpa
from iMES import TpaList

@app.route('/menu')
@login_required
def menu():
    device_tpa = TpaList[request.remote_addr]
    if current_user.role == 'Оператор':
        return redirect('/operator')
    if current_user.role == 'Наладчик':
        return redirect('/adjuster')
    return render_template("menu.html",
                           device_tpa = device_tpa,
                           current_tpa = current_tpa[request.remote_addr])
