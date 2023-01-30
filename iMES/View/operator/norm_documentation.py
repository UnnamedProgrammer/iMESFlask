from iMES import app, current_tpa
from flask import render_template

@app.route("/operator/NormDocumentation")
def Norm_Documentation():
    return render_template("operator/NormDocumentation.html", current_tpa = current_tpa)