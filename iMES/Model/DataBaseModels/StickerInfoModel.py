from iMES import db
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER, INTEGER, DATETIME
from sqlalchemy import  ForeignKey, text
from sqlalchemy.orm import mapped_column



class StickerInfo(db.Model):
    __tablename__ = "StickerInfo"
    Oid = db.Column(UNIQUEIDENTIFIER, primary_key=True, server_default=text("newid()"), nullable=False)
    Equipment = mapped_column(ForeignKey('Equipment.Oid'), nullable=False)
    Product = mapped_column(ForeignKey('Product.Oid'), nullable=False)
    StickerCount = db.Column(INTEGER, nullable=False)
    CreateDate = db.Column(DATETIME, nullable=False)
    Creator = mapped_column(ForeignKey('User.Oid'), nullable=False)
