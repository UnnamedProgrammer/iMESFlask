from iMES import db
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER, DATETIME, BIT
from sqlalchemy import text, ForeignKey
from sqlalchemy.orm import mapped_column


class DocumentReadStatus(db.Model):
    __tablename__ = "Documentation"
    Oid = db.Column(UNIQUEIDENTIFIER, primary_key=True, server_default=text("newid()"), nullable=False)
    User = mapped_column(ForeignKey('User.Oid'), nullable=False)
    Document = mapped_column(ForeignKey('Documentation.Oid'), nullable=False)
    Status = db.Column(BIT, nullable=False)
    ReadDate = db.Column(DATETIME, nullable=True)