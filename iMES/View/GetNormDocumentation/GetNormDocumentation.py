from flask import request
from iMES import app, db
from datetime import datetime
from iMES.Model.DataBaseModels.DocumentationModel import Documentation
from iMES.Model.DataBaseModels.RoleModel import Role
from iMES.Model.DataBaseModels.Relation_DocumentationRoleModel import Relation_DocumentationRole

@app.route("/GetNormDocumentation", methods=['POST'])
def GetNormDocumentation():
    # Получение документа из директума
    request_data = request.get_json()
    EDocLink = request_data['EDocLink']
    Roles = request_data['Role']
    CreateDate = datetime.strptime(request_data['CreateDate'], '%Y-%m-%d %H:%M:%S')
    StrDate = CreateDate.strftime('%Y-%m-%dT%H:%M:%S')
    # Вставка записи документа в БД
    new_document = Documentation()
    new_document.DocURL = EDocLink
    new_document.CreateDate = StrDate
    db.session.add(new_document)
    db.session.commit()

    NewDocOid = db.session.query(Documentation.Oid).where(
        Documentation.DocURL == EDocLink).where(
            Documentation.CreateDate == StrDate
        ).one_or_none()
    if NewDocOid is not None:
        NewDocOid = NewDocOid[0]

        for role in Roles:
            role_oid = db.session.query(Role.Oid).where(Role.Name == role).one_or_none()
            if role_oid is not None:
                doc_role_relation = Relation_DocumentationRole()
                doc_role_relation.Documentation = NewDocOid
                doc_role_relation.Role = role_oid
                db.session.add(doc_role_relation)
                db.session.commit()
            else:
                return f'ОШИБКА: В базе данных iMES не найдено данной роли {role_oid}.'
    else:
        return 'ОШИБКА: Документ не был найден в базе данных iMES.'

    #{'EDocLink': 'http://pink/doc.asp?sys=DIRECTUM&id=1987402', 'Role': ['Оператор'], 'CreateDate': '01.02.2023 11:10:56'}
    return 'Insert success.'
