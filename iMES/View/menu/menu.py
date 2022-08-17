from iMES import app
from flask import render_template,redirect
from flask_login import login_required,current_user

@app.route('/menu')
@login_required
def menu():
    if current_user.role == 'Оператор':
        return redirect('operator')
    if current_user.role == 'Наладчик':
        return redirect('/adjuster')
    return render_template("menu.html")
