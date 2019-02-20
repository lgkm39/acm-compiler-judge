# -*- coding: utf-8 -*-
from flask_wtf import FlaskForm
# from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, IntegerField, SelectField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
# from app.models import User
from wtforms import *

# __tablename__ = 'midinfo'
# id = Column(Integer, primary_key=True)
# user_id = Column(Integer, ForeignKey('users.id'))
# TA = student = Column(String)
# self_form = Column(String)
# TA_form = Column(String)


class MidInfoForm(FlaskForm):
    TA = SelectField(
        'TA',
        choices=[
            (u'盛佩瑶', u'盛佩瑶'),
            (u'卢思迪', u'卢思迪'),
            (u'郑怜悯', u'郑怜悯'),
            (u'陈欣昊', u'陈欣昊')
        ],
        render_kw={
            'class': 'form-control monospace',
        }
    )
    self_report = TextAreaField(
        'midterm report',
        render_kw={
            'placeholder': 'Your midterm report',
            'class': 'form-control monospace',
            'rows': '10',
        }
    )
    TA_report = TextAreaField(
        'TA_report',
        render_kw={
            'placeholder': 'TA report',
            'class': 'form-control monospace',
            'rows': '10',
        }
    )
    submit = SubmitField(
        'Submit',
        render_kw={
            'class': "btn btn-primary",
        }
    )


class CompilerForm(FlaskForm):
    student = StringField(
        'Student Name',
        validators=[DataRequired()],
        render_kw={
            'placeholder': 'Your Name',
            'class': 'form-control monospace',
        }
    )
    repo_url = StringField(
        'Repository URL',
        validators=[DataRequired()],
        render_kw={
            'placeholder': 'Your Repository Url',
            'class': 'form-control monospace',
        }
    )
    submit = SubmitField(
        'Submit',
        render_kw={
            'class': "btn btn-primary",
        }
    )


class TestcaseForm(FlaskForm):
    program = TextAreaField(
        'program',
        validators=[DataRequired()],
        render_kw = {
            'placeholder': 'Your program',
            'class': 'form-control monospace',
            'rows': '10',
        }
    )
    output = TextAreaField(
        'output',
        render_kw={
            'placeholder': 'Output of your program',
            'class': 'form-control monospace'
        }
    )
    input = TextAreaField(
        'input',
        render_kw={
            'placeholder': 'input of your program',
            'class': 'form-control monospace'
        }
    )
    phase = SelectField(
        'phrase',
        choices=[
            ('semantic pretest', 'semantic pretest'),
            ('semantic extended', 'semantic extended'),
            ('codegen pretest', 'codegen pretest'),
            ('codegen extended', 'codegen extended'),
            ('optim pretest', 'optim pretest'),
            ('optim extended', 'optim extended')
        ],
        render_kw = {
            'class': 'form-control monospace',
        }
    )

    assert_ = SelectField(
        'assert',
        choices=[
            ('success_compile', 'success_compile'),
            ('failure_compile', 'failure_compile'),
            ('exitcode', 'exitcode'),
            ('output', 'output'),
        ],
        render_kw = {
            'class': 'form-control monospace',
        }
    )

    timeout = StringField(
        'timeout',
        render_kw={
            'class': 'form-control monospace',
            'placeholder': 'time limit of your program',
        }
    )

    comment = StringField(
        'comment',
        render_kw = {
            'class': 'form-control monospace',
            'placeholder': 'briefly describe your program`',
        }
    )
    exitcode = StringField(
        'exitcode',
        render_kw = {
            'class': 'form-control monospace',
            'placeholder': '0 ~ 255',
        }
    )
    submit = SubmitField(
        'Submit',
        render_kw={
            'class': "btn btn-primary",
        }
    )


class ModifyPasswordForm(FlaskForm):
    old_password = PasswordField(
        'Old Password',
        validators=[DataRequired()],
        render_kw={
            'class': 'form-control monospace',
            'placeholder': 'Whatever',
        }
    )

    password = PasswordField(
        'New Password',
        validators=[DataRequired()],
        render_kw={
            'class': 'form-control monospace',
            'placeholder': 'Whatever',
        }
    )

    password2 = PasswordField(
        'Repeat Password',
        validators=[DataRequired(), EqualTo('password')],
        render_kw={
            'class': 'form-control monospace',
            'placeholder': 'Whatever',
        }
    )

    submit = SubmitField(
        'Confirm',
        render_kw={
            'class': "btn btn-primary",
        }
    )


class ModifyInformationForm(FlaskForm):
    email = StringField(
        'Email',
        validators=[],
        render_kw={
            'class': 'form-control monospace',
            'placeholder': 'Whatever',
        }
    )
    student_name = StringField(
        'Your real name',
        validators=[],
        render_kw={
            'class': 'form-control monospace',
            'placeholder': 'Whatever',
        }
    )
    student_id = StringField(
        'Your student id',
        validators=[],
        render_kw={
            'class': 'form-control monospace',
            'placeholder': 'Whatever',
        }
    )
    repo_url = StringField(
        'Repo',
        render_kw = {
            'class': 'form-control monospace',
            'placeholder': 'Whatever',
        }
    )
    submit = SubmitField(
        'Confirm',
        render_kw={
            'class': "btn btn-primary",
        }
    )


class LoginForm(FlaskForm):
    username = StringField(
        'Username',
        validators=[DataRequired()],
        render_kw={
            'class': 'form-control monospace',
            'placeholder': 'Whatever',
        }
    )
    password = PasswordField(
        'Password',
        validators=[DataRequired()],
        render_kw={
            'class': 'form-control monospace',
            'placeholder': 'Whatever',
        }
    )

    submit = SubmitField(
        'Login',
        render_kw={
            'class': "btn btn-primary",
        }
    )


class RegistrationForm(FlaskForm):
    username = StringField(
        'Username',
        validators=[DataRequired()],
        render_kw={
            'class': 'form-control monospace',
            'placeholder': 'Whatever',
        }
    )
    password = PasswordField(
        'Password',
        validators=[DataRequired()],
        render_kw={
            'class': 'form-control monospace',
            'placeholder': 'Whatever',
        }
    )
    password2 = PasswordField(
        'Repeat Password',
        validators=[DataRequired(), EqualTo('password')],
        render_kw={
            'class': 'form-control monospace',
            'placeholder': 'Whatever',
        }
    )
    email = StringField(
        'Email',
        validators=[],
        render_kw={
            'class': 'form-control monospace',
            'placeholder': 'Whatever',
        }
    )
    student_name = StringField(
        'Your real name',
        validators=[],
        render_kw={
            'class': 'form-control monospace',
            'placeholder': 'Whatever',
        }
    )
    student_id = StringField(
        'Your student id',
        validators=[],
        render_kw={
            'class': 'form-control monospace',
            'placeholder': 'Whatever',
        }
    )
    repo_url = StringField(
        'Repo',
        validators=[],
        render_kw = {
            'class': 'form-control monospace',
            'placeholder': 'Whatever',
        }
    )
    submit = SubmitField(
        'Register',
        render_kw={
            'class': "btn btn-primary",
        }
    )

    # def validate_username(self, username):
    #     user = User.query.filter_by(username=username.data).first()
    #     if user is not None:
    #         raise ValidationError('Please use a different username.')
    #
    # def validate_email(self, email):
    #     user = User.query.filter_by(email=email.data).first()
    #     if user is not None:
    #         raise ValidationError('Please use a different email address.')
