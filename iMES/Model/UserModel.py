from flask_login import UserMixin


class UserModel(UserMixin):
    """
        Класс модель для взаимодействия с авторизованным пользователем в системе
    """
    oid = None
    id = None
    name = None
    username = None
    CardNumber = None
    role = {}
    interfaces = None
    savedrole = False
    device_type = ''

    def __repr__(self):
        return '<User %r>' % self.name
