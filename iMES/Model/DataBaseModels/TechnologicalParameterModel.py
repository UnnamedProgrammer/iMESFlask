from iMES import db
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER, BIT
from sqlalchemy import  ForeignKey, text
from sqlalchemy.orm import mapped_column



class TechnologicalParameter(db.Model):
    __tablename__ = "TechnologicalParameter"
    Oid = db.Column(UNIQUEIDENTIFIER, primary_key=True, server_default=text("newid()"), nullable=False)
    Name = db.Column(db.String(100), nullable=False)
    Status = db.Column(BIT, nullable=False)