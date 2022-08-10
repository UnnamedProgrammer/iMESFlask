from iMES import app
from flask import render_template


@app.route('/operator')
def operator():
    return render_template("operator/operator.html")


@app.route('/operator/ShiftTask')
def OperatorShiftTask():
    return render_template("operator/ShiftTask.html")
