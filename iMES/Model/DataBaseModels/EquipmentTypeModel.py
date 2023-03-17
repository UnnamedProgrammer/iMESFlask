from iMES import db
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy import text

class EquipmentType(db.Model):
    __tablename__ = "EquipmentType"
    Oid = db.Column(UNIQUEIDENTIFIER, primary_key=True, server_default=text("newid()"), nullable=False)
    Name = db.Column(db.String(100), nullable=False)
    SyncId = db.Column(UNIQUEIDENTIFIER, nullable=True)