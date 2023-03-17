from iMES import db
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from sqlalchemy import text, ForeignKey
from sqlalchemy.orm import mapped_column

class LastSavedRole(db.Model):
    __tablename__ = "LastSavedRole"
    Oid = db.Column(UNIQUEIDENTIFIER, primary_key=True, server_default=text("newid()"), nullable=False)
    Device = mapped_column(ForeignKey('Device.Oid'), nullable=False)
    SavedRole = mapped_column(ForeignKey('SavedRole.Oid'), nullable=False)