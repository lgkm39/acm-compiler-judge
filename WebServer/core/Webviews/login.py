import os
import sys

import settings, utils
from models import *
from forms import *
from ..web import app
from flask import flash, render_template
from flask.ext.login import login_user


@app.route(settings.WEBROOT + '/login', methods=['GET', 'POST'])
def login():
    tmp_form = LoginForm()

    if tmp_form.validate_on_submit():
        u = db_session.query(User).filter(User.username == tmp_form.username.data).first()
        if not u:
            flash("Can't Find Username")
        elif u.hash_password != tmp_form.password.data:
            flash("Password error")
        else:
            login_user(u)
            flash("Log in success")
    return render_template('userSystem/login.html', tmp_form=tmp_form)
