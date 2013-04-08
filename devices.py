#!/usr/bin/python2

import database
import hashlib
import subprocess

db = database.table('devices')

def get(name=None):
	if name:
		return db.get(name)
	else:
		return db.get()

def set(name, title, site_code='00000', device_code='0', writeable=True, power=False):
	devices = db.get()
	devices[name] = {
		'title': title,
		'site_code': site_code,
		'device_code': device_code,
		'writeable': writeable,
		'power': power
	}
	db.update(devices)

def remove(name):
	devices = db.get()
	if name not in devices:
		return False
	else:
		del devices[name]
		db.set(devices)
		return True

def list():
	return [i for i in db.get().keys()]


def power(name, power=False, comment=''):
	device = get(name)
	cmd = ['sudo', 'rcswitch-pi', device['site_code'], device['device_code'], str(int(power))]
	subprocess.Popen(cmd,
		stderr=subprocess.STDOUT,
		stdout=open('/dev/null', 'w'),
		stdin=subprocess.PIPE
	)
	device['power'] = power
	set(name, **device)
	#FIXME: log(comment)
