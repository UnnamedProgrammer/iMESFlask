from iMES import db
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER, DATETIME
from sqlalchemy import  ForeignKey, text
from sqlalchemy.orm import mapped_column



class TechnologicalParametersJournal(db.Model):
    __tablename__ = "TechnologicalParametersJournal"
    Oid = db.Column(UNIQUEIDENTIFIER, primary_key=True, server_default=text("newid()"), nullable=False)
    MainEquipment = mapped_column(ForeignKey('Equipment.Oid'), nullable=False)
    RigEquipment = mapped_column(ForeignKey('Equipment.Oid'), nullable=False)
    ChangeCouse = db.Column(db.String(1000), nullable=False)
    Parameter = mapped_column(ForeignKey('TechnologicalParameter.Oid'), nullable=False)
    OldValue = db.Column(db.String(100), nullable=False)
    NewValue = db.Column(db.String(100), nullable=False)
    Note = db.Column(db.String(1000), nullable=True)
    CreateDate = db.Column(DATETIME, nullable=False)
    Creator = mapped_column(ForeignKey('User.Oid'), nullable=False)