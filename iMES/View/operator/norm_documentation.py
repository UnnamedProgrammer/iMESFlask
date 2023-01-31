from iMES import app, current_tpa, TpaList
from flask import render_template, request

@app.route("/operator/NormDocumentation")
def Norm_Documentation():
    ip_addr = request.remote_addr
    return render_template("operator/NormDocumentation.html", current_tpa=current_tpa[ip_addr],device_tpa=TpaList[request.remote_addr])