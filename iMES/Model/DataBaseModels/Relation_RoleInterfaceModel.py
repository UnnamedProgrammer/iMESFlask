from iMES import db
from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column

class Relation_RoleInterface(db.Model):
    __tablename__ = "Relation_RoleInterface"
    Role = mapped_column(ForeignKey('Role.Oid'), primary_key=True, nullable=False)
    Interface = mapped_column(ForeignKey('Interface.Oid'), primary_key=True, nullable=False)