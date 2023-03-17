from iMES import db
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy import text, ForeignKey
from sqlalchemy.orm import mapped_column


class SavedRole(db.Model):
    __tablename__ = "SavedRole"
    Oid = db.Column(UNIQUEIDENTIFIER, primary_key=True, server_default=text("newid()"), nullable=False)
    User = mapped_column(ForeignKey('User.Oid'), nullable=False)
    Role = mapped_column(ForeignKey('Role.Oid'), nullable=False)
    Device = mapped_column(ForeignKey('Device.Oid'), nullable=False)