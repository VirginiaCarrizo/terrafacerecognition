from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_user, logout_user, login_required, logout_user
from app import app
from user import users

auth = Blueprint("auth", __name__)

@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = users.get(username)
        if user=='admin' or user=='generalfood' and password == "generalfood":  # Valida correctamente la contraseña
            login_user(user)
            return redirect(url_for("https://terragene.life/terrarrhh/camara"))
        if user=='admin' or user=='terrarrhh' and password == "terrarrhh":  # Valida correctamente la contraseña
            login_user(user)
            return redirect(url_for("https://terragene.life/terrarrhh"))
    return render_template("login.html")

@auth.route("/logout")
@login_required
def logout():
    logout_user()  # Cierra la sesión del usuario
    return redirect(url_for("login"))  # Redirige al login
    
@auth.errorhandler(403)
def forbidden(error):
    return "Access Forbidden", 403  # Mensaje que se mostrará cuando el usuario no tenga permisos

app.register_blueprint(auth)  # Rutas de autenticación
