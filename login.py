from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_user, logout_user, login_required
from user import users
from werkzeug.security import check_password_hash  # Para seguridad de contraseñas
import logging

auth = Blueprint("auth", __name__)
# Configuración básica para el logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

def configure_login(app):
    @auth.route("/terrarrhh/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form["username"]
            password = request.form["password"]
            user = users.get(username)
            
            if user:
                # Aquí deberías tener un método para verificar la contraseña de manera segura
                if (user.id == 'admin' and password == "admin") or \
                   (user.id == 'generalfood' and password == "generalfood") or \
                   (user.id == 'terrarrhh' and password == "terrarrhh"):
                    login_user(user)
                    # Redirigir según el rol del usuario
                    if user.role in ['admin', 'terrarrhh']:
                        logging.info('holaaa')
                        return redirect(url_for("routes.index"))
                    elif user.role == 'generalfood':
                        return redirect(url_for("routes.camara"))
                else:
                    logging.info('Autenticación fallida')
            # Si la autenticación falla
            return render_template("login.html", error="Credenciales inválidas")
        
        return render_template("login.html")

    @auth.route("/logout")
    @login_required
    def logout():
        logout_user()
        return redirect(url_for("auth.login"))

    app.register_blueprint(auth)  # Registrar el Blueprint de autenticación
