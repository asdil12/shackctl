#!/usr/bin/python3

import sys
import os
import sqlite3
from hashlib import sha256

#from passlib.hash import argon2
from flask import Flask, render_template, request, redirect, url_for, Response
from flask_httpauth import HTTPBasicAuth

import lib8relind
import wakeonlan

db_file = 'shackctl.db'

app = Flask(__name__)
auth = HTTPBasicAuth(realm='SHACK')


class AuthError(Exception):
	pass


def pw_hash(pw):
	return sha256(pw.encode()).hexdigest()


def get_user(user):
	conn = sql_connection()
	c = conn.cursor()
	c.execute('SELECT * FROM users WHERE name=?', (user,))
	try:
		name, passwd, admin = c.fetchone()
		conn.close()
		return {
			'name': name,
			'passwd': passwd,
			'isadmin': bool(admin),
		}
	except:
		conn.close()
		raise AuthError('Username or Password wrong')


@auth.verify_password
def check_user_password(user, password):
	try:
		u = get_user(user)
		if pw_hash(password) != u['passwd']:
			raise AuthError('Username or Password wrong')
		return True
	except AuthError:
		return False


def sql_connection():
	do_init = not os.path.exists(db_file)
	conn = sqlite3.connect(db_file)
	c = conn.cursor()
	if do_init:
		c.execute("CREATE TABLE relais (board INTEGER, relais INTEGER, name TEXT, power INTEGER)")
		c.execute("CREATE TABLE users (name TEXT, pass TEXT, admin INTEGER)")
		c.execute("CREATE TABLE wol (name TEXT, mac TEXT)")
		conn.commit()
		c.execute("INSERT INTO users VALUES (?,?,?)", ('admin', pw_hash('admin'), int(True)))
		conn.commit()
	return conn


def del_user(name: str):
	conn = sql_connection()
	c = conn.cursor()
	c.execute("DELETE FROM users WHERE name=?", (name,))
	conn.commit()
	conn.close()


def set_user(name: str, password: str, isadmin: bool):
	try:
		u = get_user(name)
		oldpass = u['passwd']
	except AuthError:
		oldpass = None
	if password:
		password = pw_hash(password)
	else:
		password = oldpass
	del_user(name)
	conn = sql_connection()
	c = conn.cursor()
	c.execute('INSERT INTO users VALUES (?,?,?)', (name, password, int(isadmin)))
	conn.commit()
	conn.close()


def get_all_users():
	conn = sql_connection()
	c = conn.cursor()
	c.execute('SELECT * FROM users ORDER BY name')
	for name, passwd, isadmin in c.fetchall():
		yield {
			'name': name,
			'passwd': passwd,
			'isadmin': bool(isadmin),
		}
	conn.close()


def set_relais(board: int, relais: int, name: str, power: bool):
	del_relais(board, relais)
	conn = sql_connection()
	c = conn.cursor()
	c.execute('INSERT INTO relais VALUES (?,?,?,?)', (board, relais, name, int(power)))
	conn.commit()
	conn.close()

def set_relais_power(board: int, relais: int, power: bool):
	name = get_relais(board, relais)['name']
	print("-> Setting relais %i on board %i to status %s - name: %s" % (relais, board, power, name))
	lib8relind.set(board, relais, int(power))
	conn = sql_connection()
	c = conn.cursor()
	c.execute('UPDATE relais SET power=? WHERE board=? AND relais=?', (int(power), board, relais))
	conn.commit()
	conn.close()

def del_relais(board: int, relais: int):
	conn = sql_connection()
	c = conn.cursor()
	c.execute("DELETE FROM relais WHERE board=? AND relais=?", (board, relais))
	conn.commit()
	conn.close()

def get_relais(board: int, relais: int):
	conn = sql_connection()
	c = conn.cursor()
	c.execute('SELECT * FROM relais WHERE board=? AND relais=?', (board, relais))
	board, relais, name, power = c.fetchone()
	conn.close()
	return {
		'board': board,
		'relais': relais,
		'name': name,
		'power': bool(power),
	}

def get_all_relais():
	conn = sql_connection()
	c = conn.cursor()
	c.execute('SELECT * FROM relais ORDER BY board, relais')
	for board, relais, name, power in c.fetchall():
		yield {
			'board': board,
			'relais': relais,
			'name': name,
			'power': bool(power),
		}
	conn.close()

def set_wol(name: str, mac: str):
	del_wol(mac)
	conn = sql_connection()
	c = conn.cursor()
	c.execute('INSERT INTO wol VALUES (?,?)', (name, mac))
	conn.commit()
	conn.close()

def set_wol_power(mac: str):
	conn = sql_connection()
	print("-> Sending Magic Packet to %s" % mac)
	wakeonlan.send_magic_packet(mac)

def del_wol(mac: str):
	conn = sql_connection()
	c = conn.cursor()
	c.execute("DELETE FROM wol WHERE mac=?", (mac,))
	conn.commit()
	conn.close()

def get_wol(mac: str):
	conn = sql_connection()
	c = conn.cursor()
	c.execute('SELECT * FROM wol WHERE mac=?', (mac,))
	name, mac = c.fetchone()
	conn.close()
	return {
		'name': name,
		'mac': mac,
	}

def get_all_wol_devices():
	conn = sql_connection()
	c = conn.cursor()
	c.execute('SELECT * FROM wol ORDER BY mac')
	for name, mac in c.fetchall():
		yield {
			'name': name,
			'mac': mac,
		}
	conn.close()


@app.route('/wol/new', methods=['GET', 'POST'])
@auth.login_required
def new_wol():
	if not get_user(auth.username())['isadmin']:
		return Response("Admin erforderlich", status=403)
	if request.method == 'GET':
		return render_template('wol.html', name='', mac='')
	elif request.method == 'POST':
		set_wol(
			request.form['name'],
			request.form['mac'],
		)
		return redirect(url_for('wol_admin'))

@app.route('/wol/<string:mac>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@auth.login_required
def edit_wol(mac):
	if not get_user(auth.username())['isadmin'] and request.method != 'PUT':
		return Response("Admin erforderlich", status=403)
	if request.method == 'GET':
		return render_template('wol.html', **get_wol(mac))
	elif request.method == 'POST':
		del_wol(mac)
		set_wol(
			request.form['name'],
			request.form['mac'],
		)
		return redirect(url_for('wol_admin'))
	elif request.method == 'PUT':
		set_wol_power(mac)
		return 'ok'
	elif request.method == 'DELETE':
		del_wol(mac)
		return 'ok'


@app.route('/relais/new', methods=['GET', 'POST'])
@auth.login_required
def new_relais():
	if not get_user(auth.username())['isadmin']:
		return Response("Admin erforderlich", status=403)
	if request.method == 'GET':
		return render_template('relais.html', board='', relais='', name='', power=False)
	elif request.method == 'POST':
		set_relais(
			int(request.form['board']),
			int(request.form['relais']),
			request.form['name'],
			bool(int(request.form['power'])),
		)
		return redirect(url_for('relais_admin'))


@app.route('/relais/<int:board>/<int:relais>', methods=['GET', 'POST', 'PUT', 'DELETE'])
@auth.login_required
def edit_relais(board, relais):
	if not get_user(auth.username())['isadmin'] and request.method != 'PUT':
		return Response("Admin erforderlich", status=403)
	if request.method == 'GET':
		return render_template('relais.html', **get_relais(board, relais))
	elif request.method == 'POST':
		del_relais(board, relais)
		set_relais(
			int(request.form['board']),
			int(request.form['relais']),
			request.form['name'],
			bool(request.form['power']),
		)
		return redirect(url_for('relais_admin'))
	elif request.method == 'PUT':
		set_relais_power(board,	relais,	bool(int(request.form['power'])))
		return 'ok'
	elif request.method == 'DELETE':
		del_relais(board, relais)
		return 'ok'


@app.route('/user/new', methods=['GET', 'POST'])
@auth.login_required
def new_user():
	if not get_user(auth.username())['isadmin']:
		return Response("Admin erforderlich", status=403)
	if request.method == 'GET':
		return render_template('user.html', name='', passwd='', isadmin=False)
	elif request.method == 'POST':
		set_user(
			request.form['name'],
			request.form['passwd'],
			bool(int(request.form.get('isadmin', '0'))),
		)
		return redirect(url_for('user_admin'))

@app.route('/user/<string:name>', methods=['GET', 'POST', 'DELETE'])
@auth.login_required
def edit_user(name):
	if not get_user(auth.username())['isadmin']:
		return Response("Admin erforderlich", status=403)
	if request.method == 'GET':
		return render_template('user.html', **get_user(name))
	elif request.method == 'POST':
		set_user(
			request.form['name'],
			request.form['passwd'],
			bool(int(request.form.get('isadmin', '0'))),
		)
		return redirect(url_for('user_admin'))
	elif request.method == 'DELETE':
		del_user(name)
		return 'ok'

@app.route('/user')
@auth.login_required
def user_admin():
	if not get_user(auth.username())['isadmin']:
		return Response("Admin erforderlich", status=403)
	return render_template('all_users_admin.html', all_users=[i for i in get_all_users()])

@app.route('/relais')
@auth.login_required
def relais_admin():
	if not get_user(auth.username())['isadmin']:
		return Response("Admin erforderlich", status=403)
	return render_template('all_relais_admin.html', all_relais=get_all_relais())


@app.route('/wol')
@auth.login_required
def wol_admin():
	if not get_user(auth.username())['isadmin']:
		return Response("Admin erforderlich", status=403)
	return render_template('wol_admin.html', all_wol=get_all_wol_devices())


@app.route('/')
@auth.login_required
def index():
	return render_template('index.html', all_relais=get_all_relais(), all_wol=get_all_wol_devices())

print("Initially setting relais according to database")
for r in get_all_relais():
	print("-> Setting relais %(relais)i on board %(board)i to status %(power)s - name: %(name)s" % r)
	try:
		lib8relind.set(r['board'], r['relais'], int(r['power']))
	except FileNotFoundError:
		print("smbus error")

if len(sys.argv) > 1 and sys.argv[1] == "generate":
	for instance in instances.keys():
		print("Updating config for %s ..." % instance, end='')
		update_config(instance)
		print(" DONE")
elif __name__ == '__main__':
	app.run(host='', debug=True)
