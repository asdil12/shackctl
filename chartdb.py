#!/usr/bin/python2

import sys
from pysqlite2 import dbapi2 as sqlite3

conn = sqlite3.connect('chart.db')
c = conn.cursor()

if len(sys.argv) > 1 and sys.argv[1] == 'init':
	c.execute("""
		CREATE TABLE temperature
		(timestamp INTEGER, cpu REAL, indoor REAL, outdoor REAL)
	""")
	c.execute("""
		CREATE TABLE load
		(timestamp INTEGER, cpu INTEGER)
	""")
	c.execute("""
		CREATE TABLE memory
		(timestamp INTEGER, ram INTEGER, swap INTEGER)
	""")

conn.commit()
conn.close()
