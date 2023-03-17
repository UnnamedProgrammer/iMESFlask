from iMES import db
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER, BIT
from sqlalchemy import text



class TakenMeasures(db.Model):
    __tablename__ = "TakenMeasures"
    Oid = db.Column(UNIQUEIDENTIFIER, primary_key=True, server_default=text("newid()"), nullable=False)
    Name = db.Column(db.String(1000), nullable=False)
    Status = db.Column(BIT, nullable=False)
    SyncId = db.Column(UNIQUEIDENTIFIER, nullable=True)