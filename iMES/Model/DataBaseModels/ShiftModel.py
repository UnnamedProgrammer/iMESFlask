from iMES import db
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER, DATETIME
from sqlalchemy import text



class Shift(db.Model):
    __tablename__ = "Shift"
    Oid = db.Column(UNIQUEIDENTIFIER, primary_key=True, server_default=text("newid()"), nullable=False)
    StartDate = db.Column(DATETIME, nullable=False)
    EndDate = db.Column(DATETIME, nullable=False)
    Note = db.Column(db.String(16), nullable=True)