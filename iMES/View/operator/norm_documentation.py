from ast import arg
from iMES import app, current_tpa, TpaList
from flask import render_template, request, redirect
from flask_login import current_user, login_required
from iMES.Model.BaseObjectModel import BaseObjectModel
from iMES.Model.DirectumInterationModule import DirectumIntegration

@app.route("/NormDocumentation")
@login_required
def Norm_Documentation():
    archive = False
    Docs = []
    doc_names = []
    doc_links = []
    ip_addr = request.remote_addr
    if current_user.id != None:
        DocsOids = BaseObjectModel.SQLExecute(
            f"""
                SELECT [Document]
                FROM [MES_Iplast].[dbo].[DocumentReadStatus]
                WHERE [User] = '{current_user.id}' AND [Status] = 0
            """
        )
        if len(DocsOids) > 0:
            for doc_oid in DocsOids:
                Docs = BaseObjectModel.SQLExecute(
                    f"""
                        SELECT [DocURL]
                        FROM [MES_Iplast].[dbo].[Documentation]
                        WHERE Oid = '{doc_oid[0]}' 
                    """
                )
            Directum = DirectumIntegration()
            Directum.Authorization()
            for doc in Docs:
                doc_id = doc[0][36:].replace(" ", "")
                doc_name = Directum.DirectumGetDocumentName(doc_id)
                Directum.DirectumGetDocument(doc_id, "normative_documetation")
                doc_names.append(doc_name)
                doc_links.append(f"/NormDocumentation/id={doc_id}")
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
    doc_oid = BaseObjectModel.SQLExecute(
        f"""
            SELECT TOP (1000) [Oid]
                ,[DocURL]
                ,[CreateDate]
            FROM [MES_Iplast].[dbo].[Documentation]
            WHERE DocURL = 'http://pink/doc.asp?sys=DIRECTUM&id={id}'
        """
    )
    if len(doc_oid) > 0:
        BaseObjectModel.SQLExecute(
            f"""
                UPDATE DocumentReadStatus
                SET Status = 1
                WHERE [User] = '{current_user.id}' AND Document = '{doc_oid[0][0]}'   
            """
        )
    return redirect("NormDocumentation")

@app.route("/NormDocumentation/Archive")
@login_required
def DocsArchive():
    archive = True
    Docs = []
    doc_names = []
    doc_links = []
    ip_addr = request.remote_addr
    if current_user.id != None:
        DocsOids = BaseObjectModel.SQLExecute(
            f"""
                SELECT [Document]
                FROM [MES_Iplast].[dbo].[DocumentReadStatus]
                WHERE [User] = '{current_user.id}' AND [Status] = 1
            """
        )
        if len(DocsOids) > 0:
            for doc_oid in DocsOids:
                Docs = BaseObjectModel.SQLExecute(
                    f"""
                        SELECT [DocURL]
                        FROM [MES_Iplast].[dbo].[Documentation]
                        WHERE Oid = '{doc_oid[0]}' 
                    """
                )
            Directum = DirectumIntegration()
            Directum.Authorization()
            for doc in Docs:
                doc_id = doc[0][36:].replace(" ", "")
                doc_name = Directum.DirectumGetDocumentName(doc_id)
                Directum.DirectumGetDocument(doc_id, "normative_documetation")
                doc_names.append(doc_name)
                doc_links.append(f"/NormDocumentation/id={doc_id}")
    return render_template("operator/NormDocumentation.html", current_tpa=current_tpa[ip_addr],
                                                            device_tpa=TpaList[request.remote_addr],
                                                            doc_names=doc_names,
                                                            doc_links=doc_links,
                                                            archive=archive)