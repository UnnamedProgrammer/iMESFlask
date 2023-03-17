from iMES import db
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER, BIT
from sqlalchemy import text

class DowntimeType(db.Model):
    __tablename__ = "DowntimeType"
    Oid = db.Column(UNIQUEIDENTIFIER, primary_key=True, server_default=text("newid()"), nullable=False)
    Name = db.Column(db.String(100), nullable=False)
    Status = db.Column(BIT, nullable=False)
    SyncId = db.Column(UNIQUEIDENTIFIER, nullable=False)