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
    ReadingAllDocs = False
    Showed_notify = False

    def __repr__(self):
        return '<User %r>' % self.name
    
    def __str__(self) -> str:
        return f"<User {self.id} {self.name} {self.username} {self.role} {self.interface} {self.savedrole}>"
    
    def get_id(self):
        return self.id
