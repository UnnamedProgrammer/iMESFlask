from iMES import db
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER, DECIMAL, DATETIME, INTEGER
from sqlalchemy import ForeignKey, text
from sqlalchemy.orm import mapped_column



class PrinterInfo(db.Model):
    __tablename__ = "PrinterInfo"
    Device = mapped_column(ForeignKey('User.Oid'),UNIQUEIDENTIFIER, primary_key=True, server_default=text("newid()"), nullable=False)
    PaperLength = db.Column(DECIMAL, nullable=False)
    ReplaceDate = db.Column(DATETIME, nullable=True)
    DayCount = db.Column(INTEGER, nullable=True)
    StickerCount = db.Column(INTEGER, nullable=True)