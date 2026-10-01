from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Length


class LoginForm(FlaskForm):
    username = StringField("Логин", validators=[
        DataRequired(message="Введите логин"),
        Length(min=3, max=64),
    ])
    password = PasswordField("Пароль", validators=[
        DataRequired(message="Введите пароль"),
    ])
    submit = SubmitField("Войти")

from wtforms import PasswordField
from wtforms.validators import EqualTo, Length


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField("Текущий пароль", validators=[
        DataRequired(message="Введите текущий пароль"),
    ])
    new_password = PasswordField("Новый пароль", validators=[
        DataRequired(message="Введите новый пароль"),
        Length(min=8, message="Пароль должен быть не короче 8 символов"),
    ])
    confirm_password = PasswordField("Подтвердите новый пароль", validators=[
        DataRequired(message="Повторите новый пароль"),
        EqualTo("new_password", message="Пароли не совпадают"),
    ])
    submit = SubmitField("Сменить пароль")