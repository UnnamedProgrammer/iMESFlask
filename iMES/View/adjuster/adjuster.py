from iMES import app
from flask import render_template


@app.route('/adjuster')
def adjuster():
    return render_template("adjuster/adjuster.html")
