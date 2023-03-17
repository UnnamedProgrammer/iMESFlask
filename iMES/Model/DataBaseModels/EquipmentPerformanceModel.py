from iMES import db
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER, INTEGER
from sqlalchemy import text, ForeignKey
from sqlalchemy.orm import mapped_column

class EquipmentPerformance(db.Model):
    __tablename__ = "EquipmentPerformance"
    Oid = db.Column(UNIQUEIDENTIFIER, primary_key=True, server_default=text("newid()"), nullable=False)
    NomenclatureGroup = mapped_column(ForeignKey('NomenclatureGroup.Oid'), nullable=False)
    MainEquipment = mapped_column(ForeignKey('Equipment.Oid'), nullable=False)
    RigEquipment = mapped_column(ForeignKey('RigEquipment.Oid'), nullable=True)
    TotalSocketCount = db.Column(INTEGER, nullable=False)