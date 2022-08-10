from iMES import app
from flask import render_template


@app.route('/operator/tableWeight')
def tableWeight():
    return render_template("operator/tableWeight.html")
