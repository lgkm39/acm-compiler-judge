# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import uuid
import json
import functools
from datetime import datetime
import StringIO
from ansi2html import ansi2html
from flask import request, redirect, session, url_for, flash, render_template, jsonify, abort, send_file, Response

from web import app
from models import *
from database import db_session
import settings, utils


def copy_sqlalchemy_object_as_dict(o):
    d = dict(o.__dict__)
    del d['_sa_instance_state']
    return d


@app.route(settings.WEBROOT)
def homepage():
    return render_template('homepage.html')


@app.route(settings.WEBROOT + '/compilers')
def compilers():
    compilers = db_session.query(Compiler).order_by(Compiler.id.asc()).all()
    versions = []
    for c in compilers:
        if c.latest_version_id:
            v = db_session.query(Version).filter(Version.id == c.latest_version_id).one()
        else:
            v = None
        versions.append(v)
    return render_template('compilers.html', compilers=compilers, versions=versions)


def get_verion_testrun_counts(version):
    passed = {k: 0 for k in settings.TEST_PHASES}
    total = {k: 0 for k in settings.TEST_PHASES}
    for r in db_session.query(TestRun).filter(TestRun.version_id == version.id):
        total[r.phase] += 1
        if r.status == 'passed':
            passed[r.phase] += 1
    ret = {p: (passed[p], total[p]) if total[p] else None for p in settings.TEST_PHASES}
    ret['build'] = version.phase != 'build'
    return ret


@app.route(settings.WEBROOT + '/builds')
def builds():
    try: start = int(request.args['start'])
    except: start = ''
    try: compiler_id = int(request.args['compiler_id'])
    except: compiler_id = ''
    sha = request.args.get('sha', '')
    phase = request.args.get('phase', '')
    status = request.args.get('status', '')

    query = db_session.query(Version).order_by(Version.id.desc())
    if compiler_id: query = query.filter(Version.compiler_id == compiler_id)
    if sha: query = query.filter(Version.sha.like(sha + '%'))
    if phase: query = query.filter(Version.phase == phase)
    if status: query = query.filter(Version.status == status)
    if start: query = query.filter(Version.id <= start)
    query = query.limit(settings.BUILDS_PER_PAGE)
    versions = query.all()
    counts = [get_verion_testrun_counts(v) for v in versions]
    return render_template('builds.html', versions=versions, counts=counts)


@app.route(settings.WEBROOT + '/runs')
def runs():
    try: start = int(request.args['start'])
    except: start = ''
    try: version_id = int(request.args['build_id'])
    except: version_id = ''
    try: testcase_id = int(request.args['testcase_id'])
    except: testcase_id = ''
    phase = request.args.get('phase', '')
    status = request.args.get('status', '')

    query = db_session.query(TestRun).order_by(TestRun.id.desc())
    if version_id: query = query.filter(TestRun.version_id == version_id)
    if testcase_id: query = query.filter(TestRun.testcase_id == testcase_id)
    if phase: query = query.filter(TestRun.phase == phase)
    if status: query = query.filter(TestRun.status == status)
    if start: query = query.filter(TestRun.id <= start)
    query = query.limit(settings.RUNS_PER_PAGE)
    rs = query.all()
    ts = {t.id: t for t in db_session.query(Testcase)}
    return render_template('runs.html', testruns=rs, testcases=ts)


@app.route(settings.WEBROOT + '/testcases')
def testcases():
    ts = db_session.query(Testcase).order_by(Testcase.id.desc()).all()
    return render_template('testcases.html', testcases=ts)


@app.route(settings.WEBROOT + '/build/<int:id>')
def build(id):
    v = db_session.query(Version).filter(Version.id == id).first()
    if not v:
        return abort(404)
    c = db_session.query(Compiler).filter(Compiler.id == v.compiler_id).one()
    ls = db_session.query(BuildLog).filter(BuildLog.version_id == id).order_by(BuildLog.id.desc()).all()
    rs = db_session.query(TestRun).filter(TestRun.version_id == id).order_by(TestRun.id.desc()).all()
    ts = {t.id: t for t in db_session.query(Testcase)}
    return render_template('build.html', compiler=c, version=v, build_logs=ls, testruns=rs, testcases=ts)



@app.route(settings.WEBROOT + '/download/buildlog_<int:id>.html')
def download_buildlog(id):
    l = db_session.query(BuildLog).filter(BuildLog.id == id).first()
    if not l:
        return abort(404)
    path = os.path.join(settings.CORE_BUILD_LOG_PATH, '{:d}.txt'.format(l.id))
    if not os.path.exists(path):
        return abort(404)
    with open(path) as f:
        text = f.read()
    html = ansi2html(text, palette='console')
    return render_template('buildlog.html', log=html, buildlog=l)


@app.route(settings.WEBROOT + '/download/testcase_<int:id>.txt')
def download_testcase(id):
    t = db_session.query(Testcase).filter(Testcase.id == id).first()
    if not t:
        return abort(404)
    if not t.is_public:
        return abort(401)
    text = utils.testcase_to_text(json.loads(t.content))
    return Response(text, content_type='text/plain; charset=utf-8')


def token_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.form.get('token', None)
        if token != settings.JUDGE_TOKEN:
            return abort(401)
        return f(*args, **kwargs)
    return decorated_function


@app.route(settings.WEBROOT + '/backend/dispatch/build', methods=['POST'])
@token_required
def backend_dispatch_build():
    version = db_session.query(Version)\
                        .filter(Version.phase == 'build', Version.status == 'pending')\
                        .order_by(Version.id.asc())\
                        .first()
    if not version:
        return jsonify({'found': False})
    compiler = db_session.query(Compiler).filter(Compiler.id == version.compiler_id).one()
    ret = {
        'found': True, 
        'compiler': copy_sqlalchemy_object_as_dict(compiler),
        'version': copy_sqlalchemy_object_as_dict(version)
    }
    version.status = 'building'
    db_session.commit()
    return jsonify(ret)


@app.route(settings.WEBROOT + '/backend/submit/build_log', methods=['POST'])
@token_required
def backend_submit_build_log():
    id = int(request.form['id'])
    print id
    judge = request.form['judge']
    print judge
    message = request.form['message']
    print message
    committed_at = utils.parse_to_utc(request.form['committed_at'])
    print committed_at
    status = request.form['status']
    print status
    build_time = float(request.form['build_time'])
    print build_time
    log = request.form['log']
    print log

    version = db_session.query(Version).filter(Version.id == id).one()
    build_log = BuildLog(version_id=version.id,
                         build_time=build_time,
                         created_at=datetime.utcnow())
    db_session.add(build_log)
    db_session.commit()
    with open(os.path.join(settings.CORE_BUILD_LOG_PATH, '{:d}.txt'.format(build_log.id)), 'w') as f:
        f.write(log)

    version.message = message
    version.committed_at = committed_at
    if status == 'ok':
        version.phase = settings.TEST_PHASES[0]
        version.status = 'pending'
    else:
        version.status = 'failed'
    db_session.commit()
    return jsonify({'ack': True})


@app.route(settings.WEBROOT + '/backend/dispatch/testrun', methods=['POST'])
@token_required
def backend_dispatch_testrun():
    t = db_session.query(TestRun)\
                  .filter(TestRun.status == 'pending')\
                  .order_by(TestRun.id.asc())\
                  .first()
    if not t:
        return jsonify({'found': False})
    v = db_session.query(Version).filter(Version.id == t.version_id).one()
    c = db_session.query(Compiler).filter(Compiler.id == v.compiler_id).one()
    ret = {
        'found': True,
        'testrun': copy_sqlalchemy_object_as_dict(t),
        'version': copy_sqlalchemy_object_as_dict(v),
        'compiler': copy_sqlalchemy_object_as_dict(c)
    }
    t.status = 'running'
    t.dispatch_at = datetime.utcnow()
    db_session.commit()
    return jsonify(ret)


@app.route(settings.WEBROOT + '/backend/submit/testrun', methods=['POST'])
@token_required
def backend_submit_testrun():
    id = int(request.form['id'])
    judge = request.form['judge']
    status = request.form['status']
    running_time = float(request.form['running_time'])
    stderr = request.form['stderr']

    r = db_session.query(TestRun).filter(TestRun.id == id).one()
    r.finished_at = datetime.utcnow()
    r.running_time = running_time
    r.status = status
    db_session.commit()
    path = os.path.join(settings.CORE_TESTRUN_STDERR_PATH, '{:d}.txt'.format(id))
    with open(path, 'w') as f:
        f.write(stderr)
    return jsonify({'ack': True})


@app.route(settings.WEBROOT + '/backend/download/testcase/<int:id>.json', methods=['POST'])
@token_required
def backend_download_testcase(id):
    t = db_session.query(Testcase).filter(Testcase.id == id).one()
    return Response(t.content, mimetype='application/json')
