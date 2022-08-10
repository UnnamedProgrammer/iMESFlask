from iMES import app
from flask import render_template


@app.route('/operator/tableWasteDefect')
def tableWasteDefect():
    return render_template("operator/tableWasteDefect.html")
