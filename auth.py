#!/usr/bin/python2

import database
import hashlib

db = database.table('users')

def _hash(string):
	return hashlib.sha1(string.encode('UTF-8')).hexdigest()

def get(name=None):
	if name:
		return db.get(name)
	else:
		return db.get()

def set(name, password, admin=False):
	users = db.get()
	if name in users and not password:
		passwd = users[name]['pass']
	else:
		passwd = _hash(password)
	users[name] = {
		'pass': passwd,
		'admin': admin
	}
	db.update(users)

def remove(name):
	users = db.get()
	if name not in users:
		return False
	else:
		del users[name]
		db.update(users)
		return True

def list():
	return [i for i in db.get().keys()]

def auth(name, password):
	users = db.get()
	if name in users:
		if users[name].get('pass', '') == _hash(password):
			return True
	return False

def is_admin(name):
	users = db.get()
	return users.get(name, {}).get('admin', False)
