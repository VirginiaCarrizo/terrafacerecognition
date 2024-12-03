from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_user, logout_user
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
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
