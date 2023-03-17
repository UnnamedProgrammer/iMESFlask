from iMES import db
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER, INTEGER
from sqlalchemy import text

class Material(db.Model):
    __tablename__ = "Material"
    Oid = db.Column(UNIQUEIDENTIFIER, primary_key=True, server_default=text("newid()"), nullable=False)
    Code = db.Column(db.String(20), nullable=False)
    Name = db.Column(db.String(100), nullable=False)
    Article = db.Column(db.String(100), nullable=False)
    Type = db.Column(INTEGER, nullable=False)