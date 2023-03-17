from iMES import db
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER, DECIMAL, DATETIME
from sqlalchemy import ForeignKey, text
from sqlalchemy.orm import mapped_column



class ProductWeight(db.Model):
    __tablename__ = "ProductWeight"
    Oid = db.Column(UNIQUEIDENTIFIER, primary_key=True, server_default=text("newid()"), nullable=False)
    ProductionData = mapped_column(ForeignKey('ProductionData.Oid'), nullable=False)
    Weight = db.Column(DECIMAL, nullable=True)
    CreateDate = db.Column(DATETIME, nullable=False)
    Creator = mapped_column(ForeignKey('User.Oid'), nullable=False)
