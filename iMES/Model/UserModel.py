from iMES.Model.SQLManipulator import SQLManipulator
from flask_login import UserMixin

class UserModel(UserMixin):
    id = 12345
    name = "Ермолаев Василий Евгеньевич"

    def __repr__(self):
        return '<User %r>' % self.name