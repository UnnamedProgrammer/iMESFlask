from asyncio.windows_events import NULL
from iMES.Model.SQLManipulator import SQLManipulator
from flask_login import UserMixin

class UserModel(UserMixin):
    id = NULL
    name = NULL
    username = NULL
    CardNumber = NULL
    role = NULL
    interfaces = NULL
    
    def __repr__(self):
        return '<User %r>' % self.name