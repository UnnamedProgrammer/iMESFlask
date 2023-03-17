from iMES import db
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER, DECIMAL, INTEGER
from sqlalchemy import  ForeignKey, text
from sqlalchemy.orm import mapped_column




class ShiftTask(db.Model):
    __tablename__ = "ShiftTask"
    Oid = db.Column(UNIQUEIDENTIFIER, primary_key=True, server_default=text("newid()"), nullable=False)
    Shift = mapped_column(ForeignKey('Shift.Oid'), nullable=False)
    Equipment = mapped_column(ForeignKey('Equipment.Oid'), nullable=False)
    Ordinal = db.Column(INTEGER, nullable=False)
    Product = mapped_column(ForeignKey('Product.Oid'), nullable=False)
    Specification = mapped_column(ForeignKey('ProductSpecification.Oid'), nullable=False)
    Traits = db.Column(db.String(200), nullable=True)
    ExtraTraits = db.Column(db.String(400), nullable=True)
    PackingScheme = db.Column(db.String(1500), nullable=True)
    PackingCount = db.Column(INTEGER, nullable=False)
    SocketCount = db.Column(INTEGER, nullable=False)
    ProductCount = db.Column(INTEGER, nullable=False)
    Cycle = db.Column(INTEGER, nullable=False)
    Weight = db.Column(DECIMAL, nullable=False)
    ProductURL = db.Column(db.String(400), nullable=True)
    PackingURL = db.Column(db.String(400), nullable=True)
    WorkCenter = db.Column(db.String(20), nullable=True)