from iMES import app
from flask import render_template



@app.route("/admin")
def admin_panel():
    return render_template("admin_panel.html")