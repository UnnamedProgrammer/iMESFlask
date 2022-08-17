from iMES import app
from flask import redirect, render_template, send_file,request
from iMES.Model.DirectumInterationModule import DirectumIntegration
import os
from flask_login import login_required
from iMES import current_tpa,TpaList

DirectumConnection = DirectumIntegration()
InstructionsId = [182675, 1057032, 277104, 1083964]


@app.route('/operator/visualinstructions/')
@login_required
def VisualInstructions():
    device_tpa = TpaList[request.remote_addr]
    Authorization = DirectumConnection.Authorization()
    table = """"""
    if (Authorization == True):
        for i in range(0, len(InstructionsId)):
            Name = DirectumConnection.DirectumGetDocumentName(
                InstructionsId[i])
            if Name != "":
                tr_table = f"""
                                <tr>
                                    <td class="align-middle">{Name}</td>
                                    <td>
                                        <a class="table_button button-1 btn" onclick="LinkClick();"
                                        href="/operator/visualinstructions/DAuth={Authorization}/ddoc={InstructionsId[i]}">
                                            Открыть
                                        </a>
                                    </td>
                                </tr>
                            """
                table = table + tr_table
    else:
        return render_template("Show_error.html", error=Authorization,
                               ret="/operator")
    return render_template("operator/tableVisualInstruction.html", table=table,device_tpa = device_tpa,
                           current_tpa = current_tpa[request.remote_addr])


@app.route('/operator/visualinstructions/DAuth=<string:status>/ddoc=<string:instructionid>')
@login_required
def GetVisualInstruction(instructionid, status):
    if (status == "True"):
        if (os.path.exists(f"iMES/templates/Directum/doc_{instructionid}")):
            return render_template(
                f"Directum/doc_{instructionid}/{instructionid}_frame.html")
        else:
            doc = DirectumConnection.DirectumGetDocument(instructionid)
            if (isinstance(doc, str)):
                return render_template("Show_error.html", error=doc,
                                       ret="/operator")
            return render_template(
                f"Directum/doc_{instructionid}/{instructionid}_frame.html")
    else:
        if (DirectumConnection.Authorization()):
            return redirect("/operator/visualinstructions/")
        else:
            return render_template("Show_error.html",
                                   error='Не удалось авторизоваться в СЭД "Directum"',
                                   ret="/operator")


@app.route('/operator/visualinstructions/ddoc=<string:instructionid>&Show')
@login_required
def ShowVisualInstruction(instructionid):
    return render_template(f"Directum/doc_{instructionid}/{instructionid}.html")


@app.route('/operator/visualinstructions/images/<string:image>')
@login_required
def LoadImagesVisualInstruction(image):
    return send_file(f"static\\Directum\\images\\{image}")
