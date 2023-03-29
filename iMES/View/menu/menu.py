from iMES import app
from flask import render_template, request
from flask_login import login_required, current_user
from iMES import current_tpa
from iMES import TpaList
from iMES.functions.redirect_by_role import redirect_by_role

# Метод отображения меню либо редиректа в зависимости от роли


@app.route('/menu')
@login_required
def menu():
    # Редиректим согласно роли
    ip_addr = request.remote_addr
    device_tpa = TpaList[ip_addr]
    current_user.get_roles(ip_addr)
    if current_user.Roles['SavedRoles'] is not None:
        return redirect_by_role(current_user.Roles, current_tpa[ip_addr])
    else:
        return render_template("menu.html",
                            device_tpa=device_tpa,
                            current_tpa=current_tpa[request.remote_addr])
