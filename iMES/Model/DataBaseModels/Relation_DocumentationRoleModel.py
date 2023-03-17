from iMES import db
from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column

class Relation_DocumentationRole(db.Model):
    __tablename__ = "Relation_DocumentationRole"
    Documentation = mapped_column(ForeignKey('Documentation.Oid'), primary_key=True, nullable=False)
    Role = mapped_column(ForeignKey('Role.Oid'), primary_key=True, nullable=False)