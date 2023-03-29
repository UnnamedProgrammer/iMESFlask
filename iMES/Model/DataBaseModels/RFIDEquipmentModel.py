from iMES import db
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER, BIT, DATETIME, INTEGER
from sqlalchemy import ForeignKey, text
from sqlalchemy.orm import mapped_column



class RFIDEquipment(db.Model):
    __tablename__ = "RFIDEquipment"
    Oid = db.Column(UNIQUEIDENTIFIER, primary_key=True, server_default=text("newid()"), nullable=False)
    Code = db.Column(db.String(40), nullable=False)
    RFIDEquipmentType = mapped_column(ForeignKey('RFIDEquipmentType.Oid'), nullable=True)
    State = db.Column(INTEGER, nullable=False)