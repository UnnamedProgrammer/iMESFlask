from flask import request
from iMES import app
from iMES.Model.BaseObjectModel import BaseObjectModel
from datetime import datetime


@app.route("/GetNormDocumentation", methods=['POST'])
def GetNormDocumentation():
    # Получение документа из директума
    request_data = request.get_json()
    EDocLink = request_data['EDocLink']
    Roles = request_data['Role']
    CreateDate = datetime.strptime(request_data['CreateDate'], '%Y-%m-%d %H:%M:%S')
    StrDate = CreateDate.strftime('%Y-%m-%dT%H:%M:%S')
    # Вставка записи документа в БД
    BaseObjectModel.SQLExecute(
        f"""
            INSERT INTO Documentation (Oid, DocURL, CreateDate)
            VALUES (NEWID(),'{EDocLink}','{StrDate}')
        """
    )

    NewDocOid = BaseObjectModel.SQLExecute(
        f"""
            SELECT [Oid]
            FROM [MES_Iplast].[dbo].[Documentation]
            WHERE DocURL = '{EDocLink}' AND
                  CreateDate = '{StrDate}'  
        """
    )
    if len(NewDocOid) > 0:
        NewDocOid = NewDocOid[0][0]

        for role in Roles:
            BaseObjectModel.SQLExecute(
                f"""
                    INSERT INTO Relation_DocumentationRole (Document,[Role])
                    VALUES ('{NewDocOid}',(SELECT Oid FROM [Role] WHERE [Name] = '{role}'))    
                """
            )

    #{'EDocLink': 'http://pink/doc.asp?sys=DIRECTUM&id=1987402', 'Role': ['Оператор'], 'CreateDate': '01.02.2023 11:10:56'}
    return 'Insert success.'
