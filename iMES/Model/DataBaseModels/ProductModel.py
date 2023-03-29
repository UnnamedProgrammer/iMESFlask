from iMES import db
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy import text
from sqlalchemy.orm import mapped_column



class Product(db.Model):
    __tablename__ = "Product"
    Oid = mapped_column(UNIQUEIDENTIFIER, primary_key=True, server_default=text("newid()"), nullable=False)
    Code = db.Column(db.String(20), nullable=False)
    Name = db.Column(db.String(100), nullable=False)
    Article = db.Column(db.String(100), nullable=False)