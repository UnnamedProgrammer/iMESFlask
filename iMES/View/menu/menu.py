from iMES import app
from flask import render_template
from flask_login import login_required

@app.route('/menu')
@login_required
def menu():
    return render_template("menu.html")
