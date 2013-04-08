#!/usr/bin/python2
# -*- coding: utf-8 -*-

import os
from flask import Flask, render_template
from flask.ext.bootstrap import Bootstrap
from flask import url_for
from flask import session
from flask import redirect
from flask import request
from flask import flash
from flask import make_response
import auth
import devices as dev

app = Flask(__name__)
Bootstrap(app)
try:
	app.secret_key = open('secret.key').read()
except:
	app.secret_key = os.urandom(24)
	open('secret.key', 'w').write(app.secret_key)

@app.route('/')
def index():
	return render_template('base.html')

@app.route('/devices', methods=['GET', 'POST'])
def devices():
	if request.method == 'GET':
		return render_template('devices.html', devices=dev.get())
	else:
		if 'username' in session:
			if 'on' in request.form or 'off' in request.form:
				device = request.form.get('on', request.form.get('off'))
				target_state = True if 'on' in request.form else False
				if dev.get(device).get('writeable') or session['admin']:
					dev.power(device, target_state)
					target_str = 'up' if target_state else 'down'
					flash('Device "%s" powered %s.' % (device, target_str), 'success')
			elif 'delete' in request.form:
				#FIXME: log
				if session.get('admin'):
					device = request.form.get('delete')
					dev.remove(device)
					flash('Device "%s" deleted.' % device, 'success')
			elif 'add' in request.form:
				return redirect(url_for('device_new'))
			elif 'edit' in request.form:
				return redirect(url_for('device_edit', device=request.form.get('edit')))
			elif 'set' in request.form:
				name = request.form.get('set')
				title = request.form.get('title')
				action = request.form.get('action')
				site_code = request.form.get('site_code')
				device_code = request.form.get('device_code')
				writeable = True if request.form.get('writeable') == 'on' else False
				#FIXME: log
				dev.set(name=name, title=title, site_code=site_code, device_code=device_code, writeable=writeable)
				if action == 'add':
					flash('Device "%s" created.' % (name), 'success')
				else:
					flash('Device "%s" updated.' % (name), 'success')
		return redirect(url_for('devices'))

@app.route('/devices/new')
def device_new():
	if not session.get('admin'):
		flash("You don't have permission to do that.", 'error')
		return redirect(url_for('devices'))
	return render_template('device_form.html', device=None, name=None)

@app.route('/devices/edit/<device>')
def device_edit(device):
	if not session.get('admin'):
		flash("You don't have permission to do that.", 'error')
		return redirect(url_for('devices'))
	return render_template('device_form.html', device=dev.get(device), name=device)

@app.route('/users', methods=['GET', 'POST'])
def users():
	if not session.get('admin'):
		return redirect(url_for('index'))
	if request.method == 'GET':
		return render_template('users.html', users=auth.get())
	else:
		if 'delete' in request.form:
			user = request.form.get('delete')
			auth.remove(user)
			flash('User "%s" deleted.' % user, 'success')
		elif 'add' in request.form:
			return redirect(url_for('user_new'))
		elif 'edit' in request.form:
			return redirect(url_for('user_edit', user=request.form.get('edit')))
		elif 'set' in request.form:
			name = request.form.get('set')
			password = request.form.get('pass')
			if not password:
				password = False
			admin = True if request.form.get('admin') == 'on' else False
			action = request.form.get('action')
			#FIXME: log
			auth.set(name=name, password=password, admin=admin)
			if action == 'add':
				flash('User "%s" created.' % (name), 'success')
			else:
				flash('User "%s" updated.' % (name), 'success')
		return redirect(url_for('users'))

@app.route('/users/new')
def user_new():
	if not session.get('admin'):
		flash("You don't have permission to do that.", 'error')
		return redirect(url_for('index'))
	return render_template('user_form.html', user=None, name=None)

@app.route('/users/edit/<user>')
def user_edit(user):
	if not session.get('admin'):
		flash("You don't have permission to do that.", 'error')
		return redirect(url_for('index'))
	return render_template('user_form.html', user=auth.get(user), name=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		username = request.form.get('user')
		password = request.form.get('pass')
		endpoint = request.form.get('endpoint')
		if auth.auth(username, password):
			session['username'] = username
			session['admin'] = auth.is_admin(username)
			flash('Login successfull.', 'success')
		else:
			flash('Login failed.', 'error')
		return redirect(url_for(endpoint))
	return redirect(url_for('index'))

@app.route('/logout')
def logout():
	session.pop('username', None)
	session.pop('admin', None)
	flash('Logout successfull.', 'success')
	return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
