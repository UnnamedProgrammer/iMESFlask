from iMES import db
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER, DATETIME
from sqlalchemy import text


class Documentation(db.Model):
    __tablename__ = "Documentation"
    Oid = db.Column(UNIQUEIDENTIFIER, primary_key=True, server_default=text("newid()"), nullable=False)
    DocURL = db.Column(db.String(400), nullable=False)
    CreateDate = db.Column(DATETIME, nullable=False)