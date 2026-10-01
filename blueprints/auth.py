from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from extensions import db
from forms import LoginForm
from forms.auth import ChangePasswordForm
from models import User
from utils.logging import log_action

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data.strip()).first()
        if user and user.check_password(form.password.data) and user.is_active:
            login_user(user)
            log_action("login", "User", user.id)
            db.session.commit()

            nxt = request.args.get("next")
            if nxt and (not nxt.startswith("/") or nxt.startswith("//")):
                nxt = None
            return redirect(nxt or url_for("main.dashboard"))

        flash("Неверный логин или пароль", "danger")

    return render_template("login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    log_action("logout", "User", current_user.id)
    db.session.commit()
    logout_user()
    return redirect(url_for("auth.login"))


@auth_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.old_password.data):
            flash("Неверный текущий пароль", "danger")
        else:
            current_user.set_password(form.new_password.data)
            log_action("change_password", "User", current_user.id)
            db.session.commit()
            flash("Пароль успешно изменён", "success")
            return redirect(url_for("main.dashboard"))

    return render_template("auth/change_password.html", form=form)