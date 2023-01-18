from flask_login import UserMixin


class UserModel(UserMixin):
    """
        Класс модель для взаимодействия с авторизованным пользователем в системе
    """
    id = None
    name = None
    username = None
    CardNumber = None
    role = {}
    interface = None
    savedrole = False
    device_type = ''

    def __repr__(self):
        return '<User %r>' % self.name
    
    def get_id(self):
        return self.id
