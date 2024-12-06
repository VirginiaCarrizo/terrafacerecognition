from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_user, logout_user, login_required
from user import users
import logging

auth = Blueprint("auth", __name__)

def configure_login(app):
    @auth.route("/login", methods=["GET", "POST"])
    def login():
        logging.info(f"Método de la solicitud: {request.method}")
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")
            logging.info('Llegué al manejo de POST')
            user = users.get(username)
            logging.info(f'Usuario obtenido: {user}')
            if user:
                if (user.id == 'admin' and password == "admin") or \
                   (user.id == 'generalfood' and password == "generalfood") or \
                   (user.id == 'terrarrhh' and password == "terrarrhh"):
                    login_user(user)
                    logging.info('Autenticación exitosa')
                    # Redirigir según el rol del usuario
                    if user.role in ['admin', 'terrarrhh']:
                        return redirect(url_for("routes.index"))
                    elif user.role == 'generalfood':
                        return redirect(url_for("routes.camara"))
                else:
                    logging.info('Contraseña incorrecta')
                    return render_template("login.html", error="Credenciales inválidas")
            else:
                logging.info('Usuario no encontrado')
                return render_template("login.html", error="Credenciales inválidas")
        else:
            logging.info('Solicitud GET recibida, mostrando formulario de inicio de sesión')
            return render_template("login.html")

    @auth.route("/logout")
    @login_required
    def logout():
        logout_user()
        return redirect(url_for("auth.login"))

    app.register_blueprint(auth, url_prefix='/terrarrhh')  # Registrar el Blueprint de autenticación
