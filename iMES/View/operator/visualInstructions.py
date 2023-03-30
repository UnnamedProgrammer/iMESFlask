from iMES import app
from flask import redirect, render_template, send_file, request
from iMES.Model.DirectumInterationModule import DirectumIntegration
import os, json
from flask_login import login_required
from iMES import current_tpa, TpaList
from iMES.functions.device_tpa import device_tpa

DirectumConnection = DirectumIntegration()

# Метод отображающий окно со списком визуальных инструкций


@app.route('/operator/visualinstructions/')
@login_required
def VisualInstructions():
    ip_addr = request.remote_addr
    device_tpas = device_tpa(ip_addr)
    InstructionsId = []
    doc = None
    if ip_addr in current_tpa.keys():
        with open('st.json', 'r', encoding='utf-8-sig') as file_json:
            json_file = json.load(file_json)[0]
            for task in json_file['Order']:
                if task['WorkCenter'] == current_tpa[ip_addr][2].WorkCenter:
                    doc = task['normUpacURL'][36:].replace("¶", "")
                    InstructionsId.append(doc)
            file_json.close()
        Authorization = DirectumConnection.Authorization()
        table = """"""
        if (Authorization == True):
            for i in range(0, len(InstructionsId)):
                if InstructionsId[i] == '':
                    continue
                Name = DirectumConnection.DirectumGetDocumentName(
                    InstructionsId[i])
                if Name != "":
                    tr_table = f"""
                                    <tr>
                                        <td class="align-middle">{Name}</td>
                                        <td class="table__button nopadding">
                                            <a class="btn__table btn__table_dark" onclick="LinkClick();"
                                            href="/operator/visualinstructions/ddoc={InstructionsId[i]}&get">
                                                Открыть
                                            </a>
                                        </td>
                                    </tr>
                                """
                    table = table + tr_table
        else:
            return render_template("Show_error.html", error=Authorization,
                                ret="/operator", device_tpa=device_tpas,
                                current_tpa=current_tpa[request.remote_addr])
        return render_template("operator/tableVisualInstruction.html", table=table, device_tpa=device_tpas,
                            current_tpa=current_tpa[request.remote_addr])
    else:
        return redirect("/")


@app.route('/operator/visualinstructions/ddoc=<string:instructionid>&get')
@login_required
def GetVisualInstruction(instructionid):
    ip_addr = request.remote_addr
    device_tpas = device_tpa(ip_addr)
    if (os.path.exists(f"iMES/templates/Directum/doc_{instructionid}")):
        return render_template(f"Directum/doc_{instructionid}/{instructionid}_frame.html")
    else:
        doc = DirectumConnection.DirectumGetDocument(instructionid, 'visual_instructions')
        if (isinstance(doc, str)):
            return render_template("Show_error.html", error=doc,
                                   ret="/operator", device_tpa=device_tpas,
                                   current_tpa=current_tpa[request.remote_addr])
        return render_template(
            f"Directum/doc_{instructionid}/{instructionid}_frame.html")


@app.route('/operator/visualinstructions/ddoc=<string:instructionid>&show')
@login_required
def ShowVisualInstruction(instructionid):
    return render_template(f"Directum/doc_{instructionid}/{instructionid}.html")


@app.route('/operator/visualinstructions/images/<string:image>')
@login_required
def LoadImagesVisualInstruction(image):
    return send_file(f"static\\Directum\\images\\{image}")
