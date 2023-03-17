from iMES import db
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER, BIT, DATETIME
from sqlalchemy import ForeignKey, text
from sqlalchemy.orm import mapped_column
from flask_jwt_extended import create_access_token
from datetime import timedelta

class User(db.Model):
    __tablename__ = "User"
    Oid = db.Column(UNIQUEIDENTIFIER, primary_key=True, server_default=text("newid()"), nullable=False)
    Employee = mapped_column(ForeignKey('Employee.Oid'), nullable=True)
    UserName = db.Column(db.String, nullable=False)
    Password = db.Column(db.String, nullable=True)
    CardNumber = db.Column(db.String, nullable=True)
    isActive = db.Column(BIT, nullable=False)
    Creator = mapped_column(ForeignKey('User.Oid'), nullable=True)
    CreateDate = db.Column(DATETIME, nullable=True)
    ModifyDate = db.Column(DATETIME, nullable=True)

    def __init__(self,password):
        self.password = password

    def get_token(self, token_time = 24):
        time_delta = timedelta(token_time)
        token = create_access_token(identity=self.Oid, expires_delta=time_delta)
        return token

    @classmethod
    def Authentication(cls, username, password):
        user = cls.query.filter(cls.UserName == username).one()
        if user:
            if password != user.Password:
                raise Exception("Неверный логин или пароль")
        return user