from flask_wtf import FlaskForm
from wtforms import DecimalField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, Optional


class ProductForm(FlaskForm):
    sku = StringField("Артикул", validators=[
        DataRequired(), Length(min=2, max=32),
    ])
    name = StringField("Наименование", validators=[
        DataRequired(), Length(min=2, max=255),
    ])
    category_id = SelectField("Категория", coerce=int, validators=[Optional()])
    unit_id = SelectField("Единица измерения", coerce=int, validators=[Optional()])
    min_stock = DecimalField("Минимальный остаток", validators=[
        Optional(), NumberRange(min=0),
    ], default=0)
    submit = SubmitField("Сохранить")