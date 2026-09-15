from flask_wtf import FlaskForm
from wtforms import (
    DecimalField,
    FileField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Email, Length, NumberRange, Regexp


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Password", validators=[DataRequired(), Length(max=128)])
    submit = SubmitField("Login")

class UserForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(min=2, max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    role = SelectField(
        "Role",
        choices=[("admin", "Admin"), ("manager", "Manager"), ("employee", "Employee")],
    )
    password = PasswordField("Password", validators=[Length(max=128)])
    submit = SubmitField("Save")

class ProductForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(min=1, max=120)])
    description = TextAreaField("Description", validators=[Length(max=500)])
    price = DecimalField(
        "Price", validators=[DataRequired(), NumberRange(min=0.01, max=100000000)]
    )
    quantity = IntegerField(
        "Quantity", validators=[DataRequired(), NumberRange(min=0, max=1000000)]
    )
    low_stock_threshold = IntegerField(
        "Low stock threshold",
        validators=[DataRequired(), NumberRange(min=0, max=100000)],
    )
    submit = SubmitField("Save")

class CustomerForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(min=2, max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    phone = StringField(
        "Phone",
        validators=[
            Length(max=30),
            Regexp(r"^[0-9+\-\s()]*$", message="Invalid phone format."),
        ],
    )
    submit = SubmitField("Save")

class SaleForm(FlaskForm):
    customer_id = SelectField("Customer", coerce=int, validators=[DataRequired()])
    product_id = SelectField("Product", coerce=int, validators=[DataRequired()])
    quantity = IntegerField(
        "Quantity", validators=[DataRequired(), NumberRange(min=1, max=100000)]
    )
    submit = SubmitField("Create Sale")

class UploadForm(FlaskForm):
    file = FileField("Invoice attachment")
    submit = SubmitField("Upload")

class TotpForm(FlaskForm):
    code = StringField(
        "Verification code",
        validators=[
            DataRequired(),
            Length(min=6, max=6),
            Regexp(r"^\d{6}$", message="Enter the 6-digit code."),
        ],
    )
    submit = SubmitField("Verify")

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField(
        "Current password", validators=[DataRequired(), Length(max=128)]
    )
    new_password = PasswordField(
        "New password", validators=[DataRequired(), Length(max=128)]
    )
    confirm_password = PasswordField(
        "Confirm new password", validators=[DataRequired(), Length(max=128)]
    )
    submit = SubmitField("Change Password")

class ResetPasswordForm(FlaskForm):
    new_password = PasswordField(
        "New password", validators=[DataRequired(), Length(max=128)]
    )
    confirm_password = PasswordField(
        "Confirm new password", validators=[DataRequired(), Length(max=128)]
    )
    submit = SubmitField("Reset Password")
