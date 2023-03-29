from iMES import db
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER, BIT, DATETIME, INTEGER
from sqlalchemy import ForeignKey, text
from sqlalchemy.orm import mapped_column



class RFIDClosureData(db.Model):
    __tablename__ = "RFIDClosureData"
    Oid = db.Column(UNIQUEIDENTIFIER, primary_key=True, server_default=text("newid()"), nullable=False)
    Controller = mapped_column(ForeignKey('RFIDEquipment.Oid'), nullable=False)
    Label = mapped_column(ForeignKey('RFIDEquipment.Oid'), nullable=False)
    Date = db.Column(DATETIME, nullable=False)
    Cycle = db.Column(INTEGER, nullable=False)
    Status = db.Column(BIT, nullable=False)