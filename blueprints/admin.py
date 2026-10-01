from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from extensions import db
from models import ActionLog, Role, User
from utils import flash_error, log_action, paginate, require_role

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/users")
@login_required
@require_role("admin")
def users():
    pag = paginate(User.query.order_by(User.username))
    return render_template("admin/users.html", pagination=pag,
                           roles=Role.query.order_by(Role.name).all())


@admin_bp.route("/users/new", methods=["POST"])
@login_required
@require_role("admin")
def user_new():
    try:
        u = User(
            username=request.form["username"].strip(),
            full_name=request.form["full_name"].strip(),
            email=request.form["email"].strip(),
            role_id=int(request.form["role_id"]),
        )
        u.set_password(request.form["password"])
        db.session.add(u)
        db.session.flush()
        log_action("create_user", "User", u.id, u.username)
        db.session.commit()
        flash("Пользователь создан", "success")
    except Exception as e:
        db.session.rollback()
        flash_error(e)
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:uid>/toggle", methods=["POST"])
@login_required
@require_role("admin")
def user_toggle(uid):
    u = db.session.get(User, uid) or abort(404)
    if u.id == current_user.id:
        flash("Нельзя заблокировать самого себя", "warning")
    else:
        u.is_active_flag = not u.is_active_flag
        log_action("toggle_user", "User", u.id, f"active={u.is_active_flag}")
        db.session.commit()
        flash("Статус пользователя изменён", "info")
    return redirect(url_for("admin.users"))


@admin_bp.route("/log")
@login_required
@require_role("admin")
def log():
    pag = paginate(ActionLog.query.order_by(ActionLog.created_at.desc()), per_page=50)
    return render_template("admin/log.html", pagination=pag)