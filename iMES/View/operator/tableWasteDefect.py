from iMES import app
from iMES import socketio
from flask import render_template
from flask import request
from iMES import current_tpa
from flask_login import login_required

@login_required
@app.route('/operator/tableWasteDefect')
def tableWasteDefect():
    ip_addr = request.remote_addr
    return render_template("operator/tableWasteDefect/tableWasteDefect.html", current_tpa=current_tpa[ip_addr])

@login_required
@app.route('/operator/tableWasteDefect/wastes')
def wastes():
    ip_addr = request.remote_addr
    return render_template("operator/tableWasteDefect/wastes.html", current_tpa=current_tpa[ip_addr])

@login_required
@app.route('/operator/tableWasteDefect/wastes/anotherWastes')
def otherWastes():
    ip_addr = request.remote_addr
    return render_template("operator/tableWasteDefect/anotherWastes.html", current_tpa=current_tpa[ip_addr])
