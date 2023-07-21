from flask_login import UserMixin


class User(UserMixin):
    def __init__(self, username):
        super().__init__()
        self.id = username
        self.username = username
        self.par = {}

    def setParameters(self, par):
        self.par = par
        self.par['username'] = self.username
        self.par['id'] = self.id
