#!/usr/bin/python2

import os
import json

table_defaults = {
	'users': {
		'admin': {
			'pass': '5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8',
			'admin': True
		}
	}
}

class Database:
	instances = {}

	@classmethod
	def instance(cls, table):
		if table not in cls.instances:
			cls.instances[table] = cls(table)
		return cls.instances[table]

	def __init__(self, table):
		self.default = table_defaults.get(table, {}).copy()
		self.filename = os.path.join('database', '%s.json' % table)

	def get(self, key=None):
		try:
			data = json.load(open(self.filename))
		except:
			data = self.default
		if key:
			return data[key]
		return data

	def set(self, content):
		json.dump(content, open(self.filename, 'w'))

	def update(self, data):
		upcfg = self.get()
		upcfg.update(data)
		self.set(upcfg)

def table(table):
	return Database.instance(table)
