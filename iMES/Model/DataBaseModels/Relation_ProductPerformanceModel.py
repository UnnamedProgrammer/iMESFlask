from iMES import db
from sqlalchemy.dialects.mssql import INTEGER
from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column

class Relation_ProductPerformance(db.Model):
    __tablename__ = "Relation_ProductPerformance"
    EquipmentPerfromance = mapped_column(ForeignKey('EquipmentPerformance.Oid'), primary_key=True, nullable=False)
    Product = mapped_column(ForeignKey('Product.Oid'), primary_key=True, nullable=False)
    SocketCount = db.Column(INTEGER, nullable=False)
    Cycle = db.Column(INTEGER, nullable=False)