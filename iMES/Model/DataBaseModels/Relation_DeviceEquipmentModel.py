from iMES import db
from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column




class Relation_DeviceEquipment(db.Model):
    __tablename__ = "Relation_DeviceEquipment"
    Device = mapped_column(ForeignKey('Device.Oid'), primary_key=True, nullable=False)
    Equipment = mapped_column(ForeignKey('Equipment.Oid'), primary_key=True, nullable=False)
    