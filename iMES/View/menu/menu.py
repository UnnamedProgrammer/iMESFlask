from iMES import app
from flask import render_template, request
from flask_login import login_required
from iMES import current_tpa
from iMES import TpaList

@app.route('/menu')
@login_required
def menu():
    device_tpa = TpaList[request.remote_addr]
    return render_template("menu.html",
                           device_tpa = device_tpa,
                           current_tpa = current_tpa[request.remote_addr])
