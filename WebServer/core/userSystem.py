# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from models import *
from database import db_session

from web import app
from flask_login import LoginManager

login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'login'
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db_session.query(User).filter(User.id == user_id).first()


