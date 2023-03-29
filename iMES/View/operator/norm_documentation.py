from pydoc import Doc
from iMES import app, current_tpa, TpaList, db
from flask import render_template, request, redirect
from flask_login import current_user, login_required
from iMES.Model.DirectumInterationModule import DirectumIntegration
from iMES.Model.DataBaseModels.DocumentReadStatusModel import DocumentReadStatus
from iMES.Model.DataBaseModels.DocumentationModel import Documentation

@app.route("/NormDocumentation")
@login_required
def Norm_Documentation():
    archive = False
    doc_names = []
    doc_links = []
    ip_addr = request.remote_addr
    Docs = db.session.query(DocumentReadStatus.Document).where(
        DocumentReadStatus.User == current_user.Oid).where(
            DocumentReadStatus.Status == 0
        ).all()
    if len(Docs) > 0:
        Directum = DirectumIntegration()
        Directum.Authorization()
        for doc in Docs:
            doc_link = db.session.query(Documentation.DocURL).where(Documentation.Oid == doc[0]).one_or_none()[0]
            doc_link_modify = doc_link[36:].replace(" ", "")
            doc_name = Directum.DirectumGetDocumentName(doc_link_modify)
            Directum.DirectumGetDocument(doc_link_modify, "normative_documetation")
            doc_names.append(doc_name)
            doc_links.append(f"/NormDocumentation/id={doc_link_modify}")
    return render_template("operator/NormDocumentation.html", current_tpa=current_tpa[ip_addr],
                                                              device_tpa=TpaList[request.remote_addr],
                                                              doc_names=doc_names,
                                                              doc_links=doc_links,
                                                              archive=archive)

@app.route("/NormDocumentation/id=<string:id>")
@login_required
def ShowDocumentation(id):
    return render_template(
            f"Directum/doc_{id}/{id}_frame.html")

@app.route("/NormDocumentation/Accept/id=<string:id>")
@login_required
def AcceptDoc(id):

    Document = db.session.query(Documentation).where(Documentation.DocURL == f'http://pink/doc.asp?sys=DIRECTUM&id={id}').one_or_none()
    ReadStatus = db.session.query(DocumentReadStatus).where(
        DocumentReadStatus.User == current_user.Oid).where(
            DocumentReadStatus.Document == Document.Oid
        ).one_or_none()
    ReadStatus.Status = 1
    db.session.commit()
    return redirect("/NormDocumentation")

@app.route("/NormDocumentation/Archive")
@login_required
def DocsArchive():
    archive = True
    doc_names = []
    doc_links = []
    ip_addr = request.remote_addr
    Docs = db.session.query(DocumentReadStatus.Document).where(
        DocumentReadStatus.User == current_user.Oid).where(
            DocumentReadStatus.Status == 1
        ).all()
    if len(Docs) > 0:
        Directum = DirectumIntegration()
        Directum.Authorization()
        for doc in Docs:
            doc_link = db.session.query(Documentation.DocURL).where(Documentation.Oid == doc[0]).one_or_none()[0]
            doc_link_modify = doc_link[36:].replace(" ", "")
            doc_name = Directum.DirectumGetDocumentName(doc_link_modify)
            Directum.DirectumGetDocument(doc_link_modify, "normative_documetation")
            doc_names.append(doc_name)
            doc_links.append(f"/NormDocumentation/id={doc_link_modify}")
    return render_template("operator/NormDocumentation.html", current_tpa=current_tpa[ip_addr],
                                                            device_tpa=TpaList[request.remote_addr],
                                                            doc_names=doc_names,
                                                            doc_links=doc_links,
                                                            archive=archive)