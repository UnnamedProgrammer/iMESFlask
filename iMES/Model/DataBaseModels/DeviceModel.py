from iMES import db
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy import text, ForeignKey
from sqlalchemy.orm import mapped_column

class Device(db.Model):
    __tablename__ = "Device"
    Oid = db.Column(UNIQUEIDENTIFIER, primary_key=True, server_default=text("newid()"), nullable=False)
    Name = db.Column(db.String(100), nullable=False)
    Description = db.Column(db.String(100), nullable=True)
    DeviceId = db.Column(db.String(40), nullable=False)
    DeviceType = mapped_column(ForeignKey('DeviceType.Oid'), nullable=False)
