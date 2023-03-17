from iMES import db
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy import text

class NomenclatureGroup(db.Model):
    __tablename__ = "NomenclatureGroup"
    Oid = db.Column(UNIQUEIDENTIFIER, primary_key=True, server_default=text("newid()"), nullable=False)
    Code = db.Column(db.String(20), nullable=False)
    Name = db.Column(db.String(100), nullable=False)