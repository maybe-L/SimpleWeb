from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField, HiddenField
from wtforms.validators import DataRequired, Length, Email, EqualTo

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class WebsiteSetupForm(FlaskForm):
    website_url = StringField('Website URL', validators=[DataRequired()])
    website_name = StringField('Website Name', validators=[DataRequired()])
    submit = SubmitField('Set Up My Website')

class WebsiteSetupForm(FlaskForm):
    website_name = StringField('Website Name', validators=[DataRequired()])
    website_url = StringField('Website URL', validators=[DataRequired()])
    submit = SubmitField('Save My Website')

# 홈 페이지 전용 폼 클래스
class HomeEditForm(FlaskForm):
    content = TextAreaField('Home Content', validators=[DataRequired()])
    csrf_token = HiddenField()


# 나머지 메뉴 폼 클래스
class MenuEditForm(FlaskForm):
    content = TextAreaField('Content', validators=[DataRequired()])
    csrf_token = HiddenField()