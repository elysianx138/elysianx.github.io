from flask_wtf import FlaskForm, file
from wtforms import StringField, PasswordField, TextAreaField, FileField, HiddenField
from wtforms.validators import DataRequired, Length, Email, Optional


class LoginForm(FlaskForm):
    username = StringField(validators=[DataRequired()])
    password = PasswordField(validators=[DataRequired()])


class RegisterForm(FlaskForm):
    username = StringField(validators=[DataRequired(), Length(min=3, max=20)])
    password = PasswordField(validators=[DataRequired(), Length(min=6)])
    admin_code = StringField(validators=[Optional()])


class UploadForm(FlaskForm):
    file = FileField(validators=[file.FileAllowed(
        ['png', 'jpg', 'jpeg', 'gif', 'md', 'txt', 'pdf', 'doc', 'docx'],
        message='文件类型不支持'
    )])


class EditProfileForm(FlaskForm):
    username = StringField(validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField(validators=[Email(message='邮箱格式不正确')])
    bio = TextAreaField(validators=[Optional()])


class ArticleForm(FlaskForm):
    title = StringField(validators=[DataRequired(message='标题不能为空'), Length(max=200)])
    body = TextAreaField(validators=[DataRequired(message='内容不能为空')])


class AnnouncementForm(FlaskForm):
    title = StringField(validators=[DataRequired(message='标题不能为空'), Length(max=200)])
    body = TextAreaField(validators=[DataRequired(message='内容不能为空')])


class DeleteAnnouncementForm(FlaskForm):
    id = HiddenField(validators=[DataRequired()])
