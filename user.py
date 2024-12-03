from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask import abort

class User(UserMixin):
    def __init__(self, id, role):
        self.id = id
        self.role = role  # Asegúrate de almacenar el rol del usuario

    def get_id(self):
        return self.id

# Puedes usar una base de datos o un diccionario simple para almacenar los usuarios
users = {
    'admin': User('admin', 'admin'),
    'rrhh': User('terrarrhh', 'terrarrhh'),
    'generalfood': User('generalfood', 'generalfood')
}
