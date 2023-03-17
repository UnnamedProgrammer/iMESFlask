from iMES import db
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER, DECIMAL
from sqlalchemy import  ForeignKey, text
from sqlalchemy.orm import mapped_column



class SpecificationMaterial(db.Model):
    __tablename__ = "SpecificationMaterial"
    Oid = db.Column(UNIQUEIDENTIFIER, primary_key=True, server_default=text("newid()"), nullable=False)
    Specification = mapped_column(ForeignKey('ProductSpecification.Oid'), nullable=False)
    Material = mapped_column(ForeignKey('Material.Oid'), nullable=False)
    Count = db.Column(DECIMAL, nullable=False)