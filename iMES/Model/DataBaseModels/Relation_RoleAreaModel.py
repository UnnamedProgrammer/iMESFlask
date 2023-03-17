from iMES import db
from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column

class Relation_RoleArea(db.Model):
    __tablename__ = "Relation_RoleArea"
    Role = mapped_column(ForeignKey('Role.Oid'), primary_key=True, nullable=False)
    Area = mapped_column(ForeignKey('Area.Oid'), primary_key=True, nullable=False)