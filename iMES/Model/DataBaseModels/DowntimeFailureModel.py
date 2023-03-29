from iMES import db
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER, DATETIME, INTEGER
from sqlalchemy import text, ForeignKey
from sqlalchemy.orm import mapped_column

class DowntimeFailure(db.Model):
    __tablename__ = "DowntimeFailure"
    Oid = db.Column(UNIQUEIDENTIFIER, primary_key=True, server_default=text("newid()"), nullable=False)
    Equipment = mapped_column(ForeignKey('Equipment.Oid'), nullable=False)
    StartDate = db.Column(DATETIME, nullable=False)
    EndDate = db.Column(DATETIME, nullable=True)
    DowntimeType = mapped_column(ForeignKey('DowntimeType.Oid'), nullable=False)
    MalfunctionCause = mapped_column(ForeignKey('MalfunctionCause.Oid'), nullable=True)
    MalfunctionDescription = mapped_column(ForeignKey('MalfunctionDescription.Oid'), nullable=True)
    TakenMeasures = mapped_column(ForeignKey('TakenMeasures.Oid'), nullable=True)
    Note = db.Column(db.String(1000), nullable=True)
    CreateDate = db.Column(DATETIME, nullable=False)
    Creator = mapped_column(ForeignKey('User.Oid'), nullable=True)
    ValidClosures = db.Column(INTEGER, nullable=True)