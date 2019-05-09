# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import uuid
import json
import functools
import subprocess
import StringIO

from datetime import datetime
from collections import namedtuple
from ansi2html import ansi2html
from flask import request, redirect, session, url_for, flash, render_template, jsonify, abort, send_file, Response
from forms import *
from web import app
from models import *
from database import db_session
import settings, utils
from userSystem import login_manager
from flask_login import LoginManager, login_required, login_user, logout_user, UserMixin, current_user

JudgeStatus = namedtuple('JudgeStatus', ['name', 'action', 'time'])
judge_status = {}


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
            login_user(u, remember=True)
            return render_template('homepage.html')

    return render_template('userSystem/login.html', tmp_form=tmp_form)


@login_required
@app.route(settings.WEBROOT + '/logout', methods=['GET', 'POST'])
def logout():
    logout_user()
    return render_template('homepage.html')


@app.route(settings.WEBROOT + '/register', methods=['GET', 'POST'])
def register():
    tmp_form = RegistrationForm()

    if tmp_form.validate_on_submit():
        u = db_session.query(User).filter(User.username == tmp_form.username.data).first()
        if u:
            flash('User already exist')
        else:
            c = db_session.query(Compiler).filter(Compiler.repo_url == tmp_form.repo_url.data).first()

            if not c and tmp_form.repo_url.data:
                c = Compiler(
                    student=tmp_form.student_name.data,
                    repo_url=tmp_form.repo_url.data
                )
                db_session.add(c)
                db_session.commit()

            new_user = User(
                username=tmp_form.username.data,
                hash_password=tmp_form.password.data,
                email=tmp_form.email.data,
                student_name=tmp_form.student_name.data,
                student_id=tmp_form.student_id.data
            )

            if c:
                new_user.compiler_id = c.id

            db_session.add(new_user)
            db_session.commit()

            return render_template('homepage.html')

    return render_template('userSystem/register.html', tmp_form=tmp_form)


@login_required
@app.route(settings.WEBROOT + '/modify_information', methods=['GET', 'POST'])
def modify_information():
    tmp_form = ModifyInformationForm()

    if tmp_form.validate_on_submit():
        current_user.email = tmp_form.email.data,
        current_user.student_name = tmp_form.student_name.data,
        current_user.student_id = tmp_form.student_id.data
        c = db_session.query(Compiler).filter(Compiler.repo_url == tmp_form.repo_url.data).first()

        if not c and tmp_form.repo_url.data:
            c = Compiler(
                student=tmp_form.student_name.data,
                repo_url=tmp_form.repo_url.data
            )
            db_session.add(c)
            db_session.commit()

        if c and tmp_form.repo_url.data and tmp_form.student_name.data:
            c.student = tmp_form.student_name.data
            c.repo_url = tmp_form.repo_url.data

        if c:
            current_user.compiler_id = c.id

        db_session.commit()
        flash('modify success!')

        return render_template('homepage.html')

    tmp_form.email.data = current_user.email
    tmp_form.student_id.data = current_user.student_id
    tmp_form.student_name.data = current_user.student_name
    # flash(db_session.query(Compiler).filter(Compiler.id == current_user.compiler_id).first().repo_url)
    if current_user.compiler_id:
        tmp_form.repo_url.data = db_session.query(Compiler).filter(Compiler.id == current_user.compiler_id).first().repo_url

    return render_template('userSystem/modify_information.html', tmp_form=tmp_form)


@login_required
@app.route(settings.WEBROOT + '/modify_password', methods=['GET', 'POST'])
def modify_password():
    tmp_form = ModifyPasswordForm()

    if tmp_form.validate_on_submit():
        u = db_session.query(User).filter(User.id == current_user.id).one()
        u.hash_password = tmp_form.password.data
        db_session.commit()
        logout_user()
        flash('modify success!')
        return render_template('homepage.html')

    return render_template('userSystem/modify_password.html', tmp_form=tmp_form)


@app.route(settings.WEBROOT + '/update_repo')
@login_required
def update_repo():
    try:
        compiler_id = request.args['compiler_id']
    except:
        if not hasattr(current_user, 'compiler_id'):
            flash('Can not find user compiler')
            return render_template('homepage.html')
        compiler_id = current_user.compiler_id

    c = db_session.query(Compiler).filter(Compiler.id == compiler_id).first()
    if c:
        if do_compiler(c):
            flash("Add to pending list", category='info')
        else :
            flash("Check repo fail", category='info')
        # if do_compiler(c):
        #     flash("Add to pending list", category='info')
        # else:
        #     flash("Can't find new version")
    else:
        flash("Can't find this compiler")
    return redirect(url_for('builds'))


def copy_sqlalchemy_object_as_dict(o):
    d = dict(o.__dict__)
    del d['_sa_instance_state']
    return d


def do_compiler(compiler):
    version_sha = get_latest_remote_version(compiler.repo_url)
    compiler.last_check_time = datetime.utcnow()
    db_session.commit()
    if not version_sha:
        return False

    # if version_sha and compiler.latest_version_id:
    #     version = db_session.query(Version)\
    #                         .filter(Version.id == compiler.latest_version_id)\
    #                         .one()
    #     if version_sha == version.sha:
    #         return False

    version = Version(compiler_id=compiler.id,
                      sha=version_sha,
                      phase='build',
                      status='pending')

    db_session.add(version)
    db_session.commit()
    compiler.latest_version_id = version.id
    db_session.commit()
    return True


@app.route(settings.WEBROOT + '/', methods=['GET', 'POST'])
def homepage():
    login_form = LoginForm()
    register_form = RegistrationForm()
    # if register_form.validate_on_submit():
    #     new_user = User(
    #         username=register_form.username.data,
    #         hash_password=register_form.password.data,
    #         email=register_form.email.data,
    #         student_name=register_form.student_name.data,
    #         student_id=register_form.student_id.data,
    #         compiler_id= None, #db_session.query(Compiler).filter(Compiler.repo_url == register_form.repo_url.data)
    #     )
    if login_form.validate_on_submit():
        u = db_session.query(User).filter(User.username == login_form.username.data).first()
        if not u:
            flash("Can't Find Username")
        elif u.hash_password != login_form.password.data:
            flash("Password error")
        else:
            login_user(u)
            flash("Log in success")
    return render_template('homepage.html')


@app.route(settings.WEBROOT + '/midinfos', methods=['GET', 'POST'])
@login_required
def midinfos():
    tmp_users = db_session.query(User).all()
    users = []
    TA_reports = []
    self_reports = []
    TAs = []
    for u in tmp_users:
        m = db_session.query(MidInfo).filter(MidInfo.user_id == u.id).first()
        users.append(u)
        if m:
            TA_reports.append(m.TA_report)
            self_reports.append(m.self_report)
            TAs.append(m.TA)
        else:
            TA_reports.append(None)
            self_reports.append(None)
            TAs.append(None)
    return render_template('MidTerm/midinfos.html', users=users, TA_reports=TA_reports, self_reports=self_reports, TAs=TAs)


@app.route(settings.WEBROOT + '/edit_midinfo', methods=['GET', 'POST'])
@login_required
def edit_midinfo():
    try:
        user_id = int(request.args['user_id'])
    except:
        user_id = current_user.id
    tmp_form = MidInfoForm()
    if tmp_form.validate_on_submit():
        m = db_session.query(MidInfo).filter(MidInfo.user_id == user_id).first()
        if m:
            m.TA = tmp_form.TA.data
            m.self_report = tmp_form.self_report.data
            m.TA_report = tmp_form.TA_report.data
            db_session.commit()
        else:
            m = MidInfo(
                user_id=user_id,
                TA=tmp_form.TA.data,
                self_report=tmp_form.self_report.data,
                TA_report=tmp_form.TA_report.data
            )
            db_session.add(m)
            db_session.commit()
        flash('Submit success')
        return render_template('homepage.html')

    m = db_session.query(MidInfo).filter(MidInfo.user_id == user_id).first()
    u = db_session.query(User).filter(User.id == user_id).first()
    if m:
        tmp_form.TA.data = m.TA
        tmp_form.self_report.data = m.self_report
        tmp_form.TA_report.data = m.TA_report

    return render_template('MidTerm/edit_midinfo.html', form=tmp_form, user=u)


@app.route(settings.WEBROOT + '/edit_testcase', methods=['GET', 'POST'])
@login_required
def edit_testcase():
    try: testcase_id = int(request.args['testcase_id'])
    except: testcase_id = ''

    tmp_form = TestcaseForm()
    if tmp_form.validate_on_submit():

        t = {
            'program': tmp_form.program.data,
            'phase': tmp_form.phase.data,
            'comment': tmp_form.comment.data,
            'assert': tmp_form.assert_.data,
            'timeout': tmp_form.timeout.data,
            'exitcode': tmp_form.exitcode.data,
            'input': tmp_form.input.data,
            'output': tmp_form.output.data,
            'is_public': 'True',
        }

        if t['timeout'] == '':
            t['timeout'] = 0
        assert t['assert'] in ['success_compile', 'failure_compile', 'exitcode', 'runtime_error', 'output']
        if t['assert'] not in ['success_compile', 'failure_compile']:
            if t['assert'] == 'exitcode':
                t['timeout'] = float(t['timeout'])
                t['exitcode'] = int(t['exitcode'])
                assert 0 <= t['exitcode'] <= 255
            elif t['assert'] == 'output':
                t['timeout'] = float(t['timeout'])
                assert 'output' in t
            assert 'input' in t
        assert t['phase'] in settings.TEST_PHASES
        assert 'comment' in t
        assert t['is_public'] in ['True', 'False']

        tmp_t = db_session.query(Testcase).filter(Testcase.id == testcase_id).first()

        testcase = Testcase(enabled=tmp_t.enabled,
                            phase=t['phase'],
                            is_public=t['is_public'],
                            comment=t['comment'],
                            timeout=t.get('timeout', None),
                            cnt_run=0,
                            cnt_hack=0,
                            content=json.dumps(t))

        for run in db_session.query(TestRun).filter(TestRun.testcase_id == testcase_id):
            db_session.delete(run)
            db_session.commit()

        db_session.delete(tmp_t)

        db_session.add(testcase)
        db_session.commit()

        return redirect(url_for('testcases'))

    t = db_session.query(Testcase).filter(Testcase.id == testcase_id).first()
    tmp_form.phase.data = t.phase
    tmp_form.comment.data = t.comment
    tmp_form.timeout.data = t.timeout
    tmp_t = json.loads(t.content)
    if 'assert' in tmp_t:
        tmp_form.assert_.data = tmp_t['assert']
    if 'exitcode' in tmp_t:
        tmp_form.exitcode.data = tmp_t['exitcode']
    if 'program' in tmp_t:
        tmp_form.program.data = tmp_t['program']
    if 'input' in tmp_t:
        tmp_form.input.data = tmp_t['input']
    if 'output' in tmp_t:
        tmp_form.output.data = tmp_t['output']

    return render_template('Testcase/edit_testcase.html', testcase_id = testcase_id, form = tmp_form)


@app.route(settings.WEBROOT + '/add_testcase', methods=['GET', 'POST'])
@login_required
def add_testcase():
    tmp_form = TestcaseForm()

    if tmp_form.validate_on_submit():

        t = {
            'program': tmp_form.program.data,
            'phase': tmp_form.phase.data,
            'comment': current_user.student_name + ' ' + tmp_form.comment.data,
            'assert': tmp_form.assert_.data,
            'timeout': tmp_form.timeout.data,
            'exitcode': tmp_form.exitcode.data,
            'input': tmp_form.input.data,
            'output': tmp_form.output.data,
            'is_public': 'True',
        }

        if t['timeout'] == '':
            t['timeout'] = 0
        assert t['assert'] in ['success_compile', 'failure_compile', 'exitcode', 'runtime_error', 'output']
        if t['assert'] not in ['success_compile', 'failure_compile']:
            if t['assert'] == 'exitcode':
                t['timeout'] = float(t['timeout'])
                t['exitcode'] = int(t['exitcode'])
                assert 0 <= t['exitcode'] <= 255
            elif t['assert'] == 'output':
                t['timeout'] = float(t['timeout'])
                assert 'output' in t
            assert 'input' in t
        assert t['phase'] in settings.TEST_PHASES
        assert 'comment' in t
        assert t['is_public'] in ['True', 'False']

        testcase = Testcase(enabled=False,
                            phase=t['phase'],
                            is_public=t['is_public'],
                            comment=t['comment'],
                            timeout=t.get('timeout', None),
                            cnt_run=0,
                            cnt_hack=0,
                            content=json.dumps(t))

        db_session.add(testcase)
        db_session.commit()

        return redirect(url_for('testcases'))
        # c = Compiler(student=tmp_form.student.data, repo_url=tmp_form.repo_url.data)
        # db_session.add(c)
        # db_session.commit()
        # return redirect(url_for('compilers'))
    tmp_form.exitcode.data = '0'
    return render_template('Testcase/add_testcase.html', form=tmp_form)


@app.route(settings.WEBROOT + '/add_compiler', methods=['GET', 'POST'])
@login_required
def add_compiler():
    tmp_form = CompilerForm()
    if tmp_form.validate_on_submit():
        c = Compiler(student=tmp_form.student.data, repo_url=tmp_form.repo_url.data)
        db_session.add(c)
        db_session.commit()
        return redirect(url_for('compilers'))
    return render_template('add_compiler.html', form=tmp_form)


def get_latest_remote_version(repo_url):
    cmd = 'git ls-remote {} master | grep refs/heads/master | cut -f1'.format(repo_url)
    try:
        version = subprocess.check_output(cmd, shell=True).strip()
    except:
        return False
    if len(version) != 40:
        return False
    return version


@app.route(settings.WEBROOT + '/compilers/', methods=['GET', 'POST'])
def compilers():
    tmp_compilers = db_session.query(Compiler).order_by(Compiler.id.asc()).all()
    versions = []
    users = []
    compilers = []
    for c in tmp_compilers:
        u = db_session.query(User).filter(User.compiler_id == c.id).first()
        v = db_session.query(Version).filter(Version.id == c.latest_version_id).first()
        if u:
            if u.username == 'mushroom':
                continue
            compilers.append(c)
            users.append(u)
            versions.append(v)
    return render_template('compilers.html', compilers=compilers, versions=versions, users=users)


@app.route(settings.WEBROOT + '/final_board/', methods=['GET', 'POST'])
def final_board():
    tmp_compilers = db_session.query(Compiler).all()
    rank_list = []
    testcases = []
    stander = {}
    skiplist=['Mushroom','TA','zky','mc']
    for c in tmp_compilers:
        u = db_session.query(User).filter(User.compiler_id == c.id).first()
        if not u:
            continue
        if u.student_name in skiplist:
            continue
        v = db_session.query(Version).filter(Version.id == c.latest_version_id).first()
        if not v:
            continue
        if v.phase != 'end' and v.phase != 'optim extended' and v.phase != 'optim pretest':
            continue
        tmp_dict = {
            'c': c,
            'u': u,
            'r': {}
        }
        count_phase = ['optim extended', 'optim pretest']
        for r in db_session.query(TestRun).filter(TestRun.version_id == v.id):
            if r.phase not in count_phase:
                continue
            if r.status != 'passed':
                continue
            tmp_dict['r'][r.testcase_id] = r.running_time
            if r.testcase_id not in testcases:
                testcases.append(r.testcase_id)
            if u.student_name == 'GCC -O2':
                stander[r.testcase_id] = r.running_time

        rank_list.append(tmp_dict)

    for item in rank_list:
        tmp_sum = 0
        for t_id in item['r'].keys():
            if t_id in stander:
                item['r'][t_id] = min(round(stander[t_id]/item['r'][t_id], 2), 1.5) + 1.0
                tmp_sum += item['r'][t_id]
            else:
                item['r'][t_id] = 'NULL'
        item['sorce'] = tmp_sum

    rank_list = sorted(rank_list, key=lambda x:x['sorce'], reverse=True)
    for i, item in enumerate(rank_list):
        if item['u'].student_name == 'GCC -O2':
            flag_O2 = item['sorce']
        if item['u'].student_name == 'GCC -O1':
            flag_O1 = item['sorce']
        if item['u'].student_name == 'GCC -O0':
            flag_O0 = item['sorce']
    for i, item in enumerate(rank_list):
        if item['sorce'] >= flag_O2:
            item['real_score'] = 100.0
        elif item['sorce'] >= flag_O1:
            item['real_score'] = 95 + 5.0 * (item['sorce'] - flag_O1) / (flag_O2 - flag_O1)
        elif item['sorce'] >= flag_O0:
            item['real_score'] = 85 + 10.0 * (item['sorce'] - flag_O0) / (flag_O1 - flag_O0)
        else:
            item['real_score'] = 60 + 25.0 * (item['sorce']) / flag_O0
        item['real_score'] = round(item['real_score'], 2)
    return render_template('final_board.html', testcases=testcases, rank_list=rank_list)


def get_verion_testrun_counts(version):
    passed = {k: 0 for k in settings.TEST_PHASES}
    total = {k: 0 for k in settings.TEST_PHASES}
    for r in db_session.query(TestRun).filter(TestRun.version_id == version.id):
        total[r.phase] += 1
        if r.status == 'passed':
            passed[r.phase] += 1
    ret = {p: (passed[p], total[p]) if total[p] else None for p in settings.TEST_PHASES}
    ret['build'] = 'passed' if version.phase != 'build' else version.status
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
    cs = {c.id: c for c in db_session.query(Compiler)}
    return render_template('builds.html', versions=versions, compilers=cs, counts=counts)


@app.route(settings.WEBROOT + '/set_testcase')
@login_required
def set_testcase():
    try: testcase_id = int(request.args['testcase_id'])
    except: testcase_id = ''
    t = db_session.query(Testcase).filter(Testcase.id == testcase_id).one()
    if t.enabled:
        t.enabled = False
    else:
        t.enabled = True
    db_session.commit()
    return redirect(url_for('testcases'))


@app.route(settings.WEBROOT + '/delete_testcase')
@login_required
def delete_testcase():
    try: testcase_id = int(request.args['delete_id'])
    except: testcase_id = ''

    for run in db_session.query(TestRun).filter(TestRun.testcase_id == testcase_id):
        db_session.delete(run)
        db_session.commit()

    t = db_session.query(Testcase).filter(Testcase.id == testcase_id).one()
    db_session.delete(t)
    db_session.commit()
    return redirect(url_for('testcases'))


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
    auto_refresh = not (version_id or testcase_id or phase or status or start)
    if version_id: query = query.filter(TestRun.version_id == version_id)
    if testcase_id: query = query.filter(TestRun.testcase_id == testcase_id)
    if phase: query = query.filter(TestRun.phase == phase)
    if status: query = query.filter(TestRun.status == status)
    if start: query = query.filter(TestRun.id <= start)
    query = query.limit(settings.RUNS_PER_PAGE)
    rs = query.all()
    vids = set(r.version_id for r in rs)
    vs = {v.id: v for v in db_session.query(Version).filter(Version.id.in_(vids))}
    cs = {c.id: c for c in db_session.query(Compiler)}
    ts = {t.id: t for t in db_session.query(Testcase)}
    watch_list = [r.id for r in rs if r.status not in ['passed', 'failed', 'timeout']]
    return render_template('runs.html', testruns=rs, testcases=ts, compilers=cs, versions=vs,
        auto_refresh=auto_refresh, watch_list=watch_list)


@app.route(settings.WEBROOT + '/ajax/watch_runs.json')
def ajax_watch_runs():
    try:
        lim = 10
        stamp = int(request.args['stamp'])
        qs = request.args.get('q', '').strip()
        qs = map(lambda q: int(q.strip()), qs.split(',')) if qs else []
        qs = sorted(qs)[:lim]
        old = []
        for testrun_id in qs:
            r = db_session.query(TestRun).filter(TestRun.id == testrun_id).one()
            v = db_session.query(Version).filter(Version.id == r.version_id).one()
            c = db_session.query(Compiler).filter(Compiler.id == v.compiler_id).one()
            t = db_session.query(Testcase).filter(Testcase.id == r.testcase_id).one()
            old.append({
                'id': r.id,
                'row_html': render_template('runs_row.html', r=r, v=v, c=c, t=t),
                'finished': r.status in ['passed', 'failed', 'timeout'],
            })

        try: latest_id = int(request.args['latest_id'])
        except: latest_id = 1<<30
        query = db_session.query(TestRun).filter(TestRun.id > latest_id)\
                          .order_by(TestRun.id.asc()).limit(lim)
        new = []
        for r in query:
            v = db_session.query(Version).filter(Version.id == r.version_id).one()
            c = db_session.query(Compiler).filter(Compiler.id == v.compiler_id).one()
            t = db_session.query(Testcase).filter(Testcase.id == r.testcase_id).one()
            new.append({
                'id': r.id,
                'row_html': render_template('runs_row.html', r=r, v=v, c=c, t=t),
                'finished': r.status in ['passed', 'failed', 'timeout'],
            })
        return jsonify({'watch': old, 'new': new, 'stamp': stamp})
    except:
        return abort(400)


@app.route(settings.WEBROOT + '/testcases')
def testcases():
    try:
        sort_method = request.args['sort_method']
    except:
        sort_method = 'download'
    try:
        reverse = request.args['reverse']
    except:
        reverse = 'T'
    order_type = None

    if sort_method == 'download':
        order_type = Testcase.id.desc() if (reverse == 'T') else Testcase.id
    elif sort_method == 'enabled':
        order_type = Testcase.enabled.desc() if (reverse == 'T') else Testcase.enabled
    elif sort_method == 'phase':
        order_type = Testcase.phase.desc() if (reverse == 'T') else Testcase.phase

    ts = db_session.query(Testcase).order_by(order_type).all()

    if sort_method == 'pass':
        ts = sorted(ts, key=lambda t: (0 if t.cnt_run == 0 else 100.0 - t.cnt_hack * 100.0 / t.cnt_run), reverse=(reverse == 'T'))
    # if sort_method == 'pass':
    #     ts.so
    return render_template('testcases.html', testcases=ts, sort_method=sort_method, reverse=reverse)


def get_build_phase_count(rs):
    count = { phase: dict() for phase in settings.TEST_PHASES }
    for r in rs:
        d = count[r.phase]
        d[r.status] = d.get(r.status, 0) + 1
        d['total'] = d.get('total', 0) + 1
    return count


@app.route(settings.WEBROOT + '/build/<int:id>')
def build(id):
    v = db_session.query(Version).filter(Version.id == id).first()
    if not v:
        return abort(404)
    c = db_session.query(Compiler).filter(Compiler.id == v.compiler_id).one()
    ls = db_session.query(BuildLog).filter(BuildLog.version_id == id).order_by(BuildLog.id.desc()).all()
    rs = db_session.query(TestRun).filter(TestRun.version_id == id).order_by(TestRun.id.desc()).all()
    ts = {t.id: t for t in db_session.query(Testcase)}
    count = get_build_phase_count(rs)
    watch_list = [r.id for r in rs if r.status not in ['passed', 'failed', 'timeout']]
    auto_refresh = v.status not in ['passed', 'failed']
    return render_template('build.html', compiler=c, version=v, build_logs=ls, 
        testruns=rs, testcases=ts, phase_count=count, auto_refresh=auto_refresh,
        watch_list=watch_list)


@app.route(settings.WEBROOT + '/ajax/build.json')
def ajax_build():
    try:
        stamp = int(request.args['stamp'])
        latest_id = int(request.args['latest_id'])
        id = int(request.args['build_id'])
        v = db_session.query(Version).filter(Version.id == id).first()
        if not v:
            return abort(404)

        lim = 10
        stamp = int(request.args['stamp'])
        qs = request.args.get('q', '').strip()
        qs = map(lambda q: int(q.strip()), qs.split(',')) if qs else []
        qs = sorted(qs)[:lim]
        watch = []
        for testrun_id in qs:
            r = db_session.query(TestRun).filter(TestRun.id == testrun_id).one()
            v = db_session.query(Version).filter(Version.id == r.version_id).one()
            c = db_session.query(Compiler).filter(Compiler.id == v.compiler_id).one()
            t = db_session.query(Testcase).filter(Testcase.id == r.testcase_id).one()
            watch.append({
                'id': r.id,
                'row_html': render_template('build_row.html', r=r, v=v, c=c, t=t),
                'finished': r.status in ['passed', 'failed', 'timeout'],
            })

        c = db_session.query(Compiler).filter(Compiler.id == v.compiler_id).one()
        ls = db_session.query(BuildLog).filter(BuildLog.version_id == id).order_by(BuildLog.id.desc()).all()
        rs = db_session.query(TestRun).filter(TestRun.version_id == id).order_by(TestRun.id.asc()).all()
        ts = {t.id: t for t in db_session.query(Testcase)}
        count = get_build_phase_count(rs)
        runs = []
        for r in rs:
            if r.id > latest_id:
                runs.append({
                    'html': render_template('build_row.html', r=r, t=ts[r.testcase_id]),
                    'id': r.id,
                    'finished': r.status in ['passed', 'failed', 'timeout'],
                })
        if rs: latest_id = rs[-1].id
        return  ({
            'stamp': stamp,
            'latest_id': latest_id,
            'bar': render_template('build_bar.html', version=v, phase_count=count),
            'runs': runs ,
            'watch': watch,
            'auto_refresh': v.status not in ['passed', 'failed']
        })
    except:
        return abort(400)


@app.route(settings.WEBROOT + '/show/buildlog_<int:id>.html')
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


@app.route(settings.WEBROOT + '/show/runlog_<int:id>.html')
def download_runlog(id):
    r = db_session.query(TestRun).filter(TestRun.id == id).first()
    if not r:
        return abort(404)
    path = os.path.join(settings.CORE_TESTRUN_STDERR_PATH, '{:d}.txt'.format(r.id))
    if not os.path.exists(path):
        return abort(404)
    with open(path) as f:
        text = f.read()
    html = ansi2html(text, palette='console')
    return render_template('runlog.html', log=html, testrun=r)


@app.route(settings.WEBROOT + '/download/testcase_<int:id>.txt')
def download_testcase(id):
    t = db_session.query(Testcase).filter(Testcase.id == id).first()
    if not t:
        return abort(404)
    if not t.is_public:
        return abort(401)
    text = utils.testcase_to_text(json.loads(t.content))
    return Response(text, content_type='text/plain; charset=utf-8')


@app.route(settings.WEBROOT + '/judges')
def judges():
    judges = sorted(judge_status.itervalues(), key=lambda x: x.time, reverse=True)
    return render_template('judges.html', judges=judges, now=datetime.utcnow())


def token_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.form.get('token', None)
        if token != settings.JUDGE_TOKEN:
            return abort(401)
        return f(*args, **kwargs)
    return decorated_function

# def admin_required(f):
#     @functools.wraps(f)
#     def decorated_function(*args, **kwargs):
#         if current_user.activate
#             return abort(401)
#         return f(*args, **kwargs)
#     return decorated_function


@app.route(settings.WEBROOT + '/backend/dispatch/build', methods=['POST'])
@token_required
def backend_dispatch_build():
    judge = request.form['judge']
    version = db_session.query(Version)\
                        .filter(Version.phase == 'build', Version.status == 'pending')\
                        .order_by(Version.id.asc())\
                        .first()
    if not version:
        message = 'ask for build tasks, but not found'
        judge_status[judge] = JudgeStatus(name=judge, action=message, time=datetime.utcnow())
        return jsonify({'found': False})
    compiler = db_session.query(Compiler).filter(Compiler.id == version.compiler_id).one()
    ret = {
        'found': True,
        'compiler': copy_sqlalchemy_object_as_dict(compiler),
        'version': copy_sqlalchemy_object_as_dict(version)
    }
    version.status = 'building'
    db_session.commit()

    message = 'ask for build tasks. assigned build task for <a href="{url_version}">build {version_id}</a>'.format(
        url_version=url_for('build', id=version.id),
        version_id=version.id)
    judge_status[judge] = JudgeStatus(name=judge, action=message, time=datetime.utcnow())
    return jsonify(ret)


@app.route(settings.WEBROOT + '/backend/submit/build_log', methods=['POST'])
@token_required
def backend_submit_build_log():
    id = int(request.form['id'])
    judge = request.form['judge']
    message = request.form['message']
    committed_at = utils.parse_to_utc(request.form['committed_at'])
    status = request.form['status']
    build_time = float(request.form['build_time'])
    log = request.form['log']

    version = db_session.query(Version).filter(Version.id == id).one()
    build_log = BuildLog(version_id=version.id,
                         build_time=build_time,
                         builder=judge,
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

    message = 'submit <a href="{url_log}">build log {log_id}</a> for <a href="{url_version}">build {version_id}</a>'.format(
        url_log=url_for('download_runlog', id=build_log.id),
        log_id=build_log.id,
        url_version=url_for('build', id=version.id),
        version_id=version.id)
    judge_status[judge] = JudgeStatus(name=judge, action=message, time=datetime.utcnow())
    return jsonify({'ack': True})


@app.route(settings.WEBROOT + '/backend/dispatch/testrun', methods=['POST'])
@token_required
def backend_dispatch_testrun():
    judge = request.form['judge']
    t = db_session.query(TestRun)\
                  .filter(TestRun.status == 'pending')\
                  .order_by(TestRun.id.asc())\
                  .first()
    if not t:
        message = 'ask for run tasks, but not found'
        judge_status[judge] = JudgeStatus(name=judge, action=message, time=datetime.utcnow())
        return jsonify({'found': False})
    print(t)
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

    message = 'ask for run tasks. assigned run task for run {run_id}'.format(
        run_id=t.id)
    judge_status[judge] = JudgeStatus(name=judge, action=message, time=datetime.utcnow())
    return jsonify(ret)


@app.route(settings.WEBROOT + '/backend/submit/testrun', methods=['POST'])
@token_required
def backend_submit_testrun():
    id = int(request.form['id'])
    judge = request.form['judge']
    status = request.form['status']
    running_time = float(request.form['running_time'])
    compile_time = float(request.form['compile_time'])
    stderr = request.form['stderr']

    r = db_session.query(TestRun).filter(TestRun.id == id).one()
    t = db_session.query(Testcase).filter(Testcase.id == r.testcase_id).one()
    r.finished_at = datetime.utcnow()
    r.running_time = running_time
    r.compile_time = compile_time
    r.status = status
    t.cnt_run = Testcase.cnt_run + 1
    if status != 'passed':
        t.cnt_hack = Testcase.cnt_hack + 1
    db_session.commit()
    path = os.path.join(settings.CORE_TESTRUN_STDERR_PATH, '{:d}.txt'.format(id))
    with open(path, 'w') as f:
        f.write(stderr)

    message = 'submit run result for <a href="{url_run}">run {run_id}</a>'.format(
        url_run=url_for('download_runlog', id=r.id),
        run_id=r.id)
    judge_status[judge] = JudgeStatus(name=judge, action=message, time=datetime.utcnow())
    return jsonify({'ack': True})


@app.route(settings.WEBROOT + '/backend/download/testcase/<int:id>.json', methods=['POST'])
@token_required
def backend_download_testcase(id):
    t = db_session.query(Testcase).filter(Testcase.id == id).one()
    return Response(t.content, mimetype='application/json')
