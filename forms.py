from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FileField, SelectField, TextField, TextAreaField, DateTimeField
from wtforms.validators import InputRequired, Email, EqualTo
import datetime 
import email_validator

class SignUpForm(FlaskForm):
    full_name = StringField('Full Name', validators = [InputRequired()])
    email = StringField('Email',
                        validators = [InputRequired(), Email()])
    password = PasswordField('Password', validators = [InputRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators = [InputRequired(), EqualTo('password')])
    bio = StringField('Biography', validators = [InputRequired()])
    image = FileField('Image', validators = [InputRequired()])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators = [InputRequired(), Email()])
    password = PasswordField('Password', validators = [InputRequired()])
    login_options=("Author","Content Moderator")
    login_as = SelectField(label="Login As:",choices=login_options,validators=[InputRequired()])
    submit = SubmitField('Login')

#changes
class ChangePassword(FlaskForm):
    email = StringField('Email',
                        validators = [InputRequired(), Email()])
    password = PasswordField('Password', validators = [InputRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators = [InputRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')


class CreateStory(FlaskForm):
    themes = ("-","Wholesome", "Tech", "Humour", "Mystic", "Sci-Fi", "Entertainment", "Food", "Sport", "Religious", "Random")
    title = StringField(label='Title',validators = [InputRequired()])
    content = TextAreaField(label='Content',validators = [InputRequired()])
    theme = SelectField(label="Theme: ", choices =themes, validators = [InputRequired()])
    submit = SubmitField(label='Create New Story!')

class UploadStory(FlaskForm):
    doc = FileField('Text', validators = [InputRequired()])
    themes = ("-","Wholesome", "Tech", "Humour", "Mystic", "Sci-Fi", "Entertainment", "Food", "Sport", "Religious", "Random")
    title = StringField(label='Title',validators = [InputRequired()])
    theme = SelectField(label="Theme: ", choices =themes, validators = [InputRequired()])
    submit = SubmitField(label='Upload New Story!')
        

class Comment(FlaskForm):
	comment = StringField(label='Comment',validators = [InputRequired()])
	submit = SubmitField(label='Post Comment')

class EditName(FlaskForm):
    name = StringField(label='New Username',validators = [InputRequired()])
    submit = SubmitField(label='submit')

class EditEmail(FlaskForm):
    email = StringField('Email',
                    validators = [InputRequired(), Email()])
    submit = SubmitField(label='submit')

class EditPassword(FlaskForm):
    password = PasswordField('Password', validators = [InputRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators = [InputRequired(), EqualTo('password')])
    submit = SubmitField(label='submit')

class EditBio(FlaskForm):
    bio = StringField(label = 'Biography', validators = [InputRequired()])
    submit = SubmitField(label='submit')

class EditPic(FlaskForm):
    image = FileField('Image', validators = [InputRequired()])
    submit = SubmitField(label='submit')

class AuthorSearch(FlaskForm):
    name = StringField(label = 'Name')
    email = StringField(label = 'Email')
    submit = SubmitField(label='Search')

class ArticleSearch(FlaskForm):
    title = StringField(label = 'Title')
    author = StringField(label = 'Author')
    themes = ("-","Wholesome", "Tech", "Humour", "Mystic", "Sci-Fi", "Entertainment", "Food", "Sport", "Religious", "Random")
    theme = SelectField(label="Theme ", choices = themes)
    submit = SubmitField(label='Search')

class YoutubeUpload(FlaskForm):
    link = StringField(label = 'Link')
    submit = SubmitField(label = 'Upload')