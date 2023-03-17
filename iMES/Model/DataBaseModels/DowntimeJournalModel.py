from iMES import db
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER, DATETIME, BIT
from sqlalchemy import text, ForeignKey
from sqlalchemy.orm import mapped_column

class DowntimeFailure():
    __tablename__ = "DowntimeJournal"
    Oid = db.Column(UNIQUEIDENTIFIER, primary_key=True, server_default=text("newid()"), nullable=False)
    Equipment = mapped_column(ForeignKey('Equipment.Oid'), nullable=False)
    StartDate = db.Column(DATETIME, nullable=False)
    EndDate = db.Column(DATETIME, nullable=True)
    Status = db.Column(BIT, nullable=False)