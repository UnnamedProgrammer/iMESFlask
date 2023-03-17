from iMES import db
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy import text, ForeignKey
from sqlalchemy.orm import mapped_column

class Equipment(db.Model):
    __tablename__ = "Equipment"
    Oid = db.Column(UNIQUEIDENTIFIER, primary_key=True, server_default=text("newid()"), nullable=False)
    Code = db.Column(db.String(20), nullable=True)
    Name = db.Column(db.String(100), nullable=False)
    EquipmentType = mapped_column(ForeignKey('EquipmentType.Oid'), nullable=False)
    Area = mapped_column(ForeignKey('Area.Oid'), nullable=True)
    NomenclatureGroup = mapped_column(ForeignKey('NomenclatureGroup.Oid'), nullable=True)
    InventoryNumber = db.Column(db.String(20), nullable=True)
    SyncId = db.Column(UNIQUEIDENTIFIER, nullable=True)