from iMES import db
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy import ForeignKey,text
from sqlalchemy.orm import mapped_column


class Role(db.Model):
    __tablename__ = "Role"
    Oid = db.Column(UNIQUEIDENTIFIER, primary_key=True, server_default=text("newid()"), nullable=False)
    Name = db.Column(db.String(100), nullable=False)
    DeviceType = mapped_column(ForeignKey('DeviceType.Oid'), nullable=True)