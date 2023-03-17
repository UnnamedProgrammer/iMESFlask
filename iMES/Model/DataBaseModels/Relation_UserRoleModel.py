from iMES import db
from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column

class Relation_UserRole(db.Model):
    __tablename__ = "Relation_UserRole"
    User = mapped_column(ForeignKey('User.Oid'), primary_key=True, nullable=False)
    Role = mapped_column(ForeignKey('Role.Oid'), primary_key=True, nullable=False)