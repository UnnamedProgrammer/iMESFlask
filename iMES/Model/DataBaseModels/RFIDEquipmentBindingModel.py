from iMES import db
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER, BIT, DATETIME
from sqlalchemy import ForeignKey, text
from sqlalchemy.orm import mapped_column


class RFIDEquipmentBinding(db.Model):
    __tablename__ = "RFIDEquipmentBinding"
    Oid = db.Column(UNIQUEIDENTIFIER, primary_key=True, server_default=text("newid()"), nullable=False)
    RFIDEquipment = mapped_column(ForeignKey('RFIDEquipment.Oid'), nullable=False)
    Equipment = mapped_column(ForeignKey('Equipment.Oid'), nullable=True)
    InstallDate = db.Column(DATETIME, nullable=True)
    RemoveDate = db.Column(DATETIME, nullable=True)
    State = db.Column(BIT, nullable=False)