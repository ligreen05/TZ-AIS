from flask_wtf import FlaskForm
from wtforms import (
    DateField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Optional


class ReceiptForm(FlaskForm):
    doc_date = DateField("Дата", validators=[DataRequired()])
    supplier_id = SelectField("Поставщик", coerce=int, validators=[DataRequired()])
    warehouse_id = SelectField("Склад", coerce=int, validators=[DataRequired()])
    comment = StringField("Комментарий", validators=[Optional()])
    submit = SubmitField("Провести приёмку")


class ShipmentForm(FlaskForm):
    doc_date = DateField("Дата", validators=[DataRequired()])
    customer_id = SelectField("Покупатель", coerce=int, validators=[DataRequired()])
    warehouse_id = SelectField("Склад", coerce=int, validators=[DataRequired()])
    comment = StringField("Комментарий", validators=[Optional()])
    submit = SubmitField("Провести отгрузку")


class TransferForm(FlaskForm):
    doc_date = DateField("Дата", validators=[DataRequired()])
    warehouse_id = SelectField("Склад", coerce=int, validators=[DataRequired()])
    comment = StringField("Комментарий", validators=[Optional()])
    submit = SubmitField("Провести перемещение")


class WriteOffForm(FlaskForm):
    doc_date = DateField("Дата", validators=[DataRequired()])
    warehouse_id = SelectField("Склад", coerce=int, validators=[DataRequired()])
    reason = StringField("Причина", validators=[Optional()])
    comment = TextAreaField("Комментарий", validators=[Optional()])
    submit = SubmitField("Провести списание")


class InventoryForm(FlaskForm):
    doc_date = DateField("Дата", validators=[DataRequired()])
    warehouse_id = SelectField("Склад", coerce=int, validators=[DataRequired()])
    comment = StringField("Комментарий", validators=[Optional()])
    submit = SubmitField("Создать черновик")