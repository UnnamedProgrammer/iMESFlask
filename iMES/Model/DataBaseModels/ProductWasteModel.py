from iMES import db
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER, DECIMAL, BIT, DATETIME
from sqlalchemy import ForeignKey, text
from sqlalchemy.orm import mapped_column



class ProductWaste(db.Model):
    __tablename__ = "ProductWaste"
    Oid = db.Column(UNIQUEIDENTIFIER, primary_key=True, server_default=text("newid()"), nullable=False)
    ProductionData = mapped_column(ForeignKey('ProductionData.Oid'), nullable=False)
    Material = mapped_column(ForeignKey('Material.Oid'), nullable=True)
    Type = db.Column(BIT, nullable=False)
    Weight = db.Column(DECIMAL, nullable=True)
    Count = db.Column(DECIMAL, nullable=True)
    Downtime = mapped_column(ForeignKey('DowntimeFailure.Oid'), nullable=True)
    Note = db.Column(db.String(1000), nullable=True)
    CreateDate = db.Column(DATETIME, nullable=False)
    Creator = mapped_column(ForeignKey('User.Oid'), nullable=False)