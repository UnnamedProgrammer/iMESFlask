from iMES import app
from flask import render_template, request, redirect
from flask_login import login_required, current_user
from iMES import current_tpa
from iMES import TpaList

# Метод отображения меню либо редиректа в зависимости от роли


@app.route('/menu')
@login_required
def menu():
    device_tpa = TpaList[request.remote_addr]
    if current_user.savedrole == True:
        if (current_user.role == 'Оператор'):
            return redirect('/operator')
        elif (current_user.role == 'Наладчик'):
            return redirect('/adjuster')
        elif (current_user.role == {0: 'Наладчик'}):
            return redirect('/adjuster')
        elif (current_user.role == {0: 'Оператор'}):
            return redirect('/operator')
    return render_template("menu.html",
                           device_tpa=device_tpa,
                           current_tpa=current_tpa[request.remote_addr])
