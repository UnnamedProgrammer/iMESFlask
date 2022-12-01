from asyncio.windows_events import NULL
from flask_login import UserMixin


class UserModel(UserMixin):
    """
        Класс модель для взаимодействия с авторизованным пользователем в системе
    """
    id = NULL
    name = NULL
    username = NULL
    CardNumber = NULL
    role = {}
    interfaces = NULL
    savedrole = False
    device_type = ''

    def __repr__(self):
        return '<User %r>' % self.name
