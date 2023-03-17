from iMES import db
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy import text




class Employee(db.Model):
    __tablename__ = "Employee"
    Oid = db.Column(UNIQUEIDENTIFIER, primary_key=True, server_default=text("newid()"), nullable=False)
    LastName = db.Column(db.String(40), nullable=False)
    FirstName = db.Column(db.String(40), nullable=False)
    MiddleName = db.Column(db.String(40), nullable=False)