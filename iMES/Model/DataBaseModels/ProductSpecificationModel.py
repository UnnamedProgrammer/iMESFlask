from iMES import db
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER, DECIMAL, BIT
from sqlalchemy import ForeignKey, text
from sqlalchemy.orm import mapped_column



class ProductSpecification(db.Model):
    __tablename__ = "ProductSpecification"
    Oid = db.Column(UNIQUEIDENTIFIER, primary_key=True, server_default=text("newid()"), nullable=False)
    Code = db.Column(db.String(20), nullable=False)
    Name = db.Column(db.String(100), nullable=False)
    Product = mapped_column(ForeignKey('Product.Oid'), nullable=False)
    UseFactor = db.Column(DECIMAL, nullable=False)
    isActive = db.Column(BIT, nullable=False)