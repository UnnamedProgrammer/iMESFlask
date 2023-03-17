from decimal import Decimal
from iMES import db
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER, INTEGER, DATETIME, DECIMAL
from sqlalchemy import ForeignKey, text
from sqlalchemy.orm import mapped_column



class ProductionData(db.Model):
    __tablename__ = "ProductionData"
    Oid = db.Column(UNIQUEIDENTIFIER, primary_key=True, server_default=text("newid()"), nullable=False)
    ShiftTask = mapped_column(ForeignKey('ShiftTask.Oid'), nullable=False)
    RigEquipment = mapped_column(ForeignKey('Equipment.Oid'), nullable=True)
    Status = db.Column(INTEGER, nullable=True)
    StartDate = db.Column(DATETIME, nullable=True)
    EndDate = db.Column(DATETIME, nullable=True)
    CountFact = db.Column(INTEGER, nullable=True)
    CycleFact = db.Column(DECIMAL, nullable=True)
    WeightFact = db.Column(DECIMAL, nullable=True)
    SpecificationFact = mapped_column(ForeignKey('ProductSpecification.Oid'), nullable=True)