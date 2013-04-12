#!/usr/bin/python2

import sys
from pysqlite2 import dbapi2 as sqlite3
from time import time
import subprocess
import psutil

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
elif len(sys.argv) > 1 and sys.argv[1] == 'insert':
	timestamp = time()

	# Temperature
	try:
		cpu = int(open('/sys/class/thermal/thermal_zone0/temp').read())
		cpu = round(float(cpu) / 1000, 1)
	except:
		cpu = 0
	indoor = 0
	outdoor = 0
	c.execute("INSERT INTO temperature VALUES (%i, %f, %f, %f)" % (timestamp, cpu, indoor, outdoor))

	# Load
	cpu = psutil.cpu_percent()
	c.execute("INSERT INTO load VALUES (%i, %d)" % (timestamp, cpu))

	# Memory
	s = subprocess.Popen(['free', '-om'], stdout=subprocess.PIPE, stderr=open('/dev/null', 'w'), stdin=subprocess.PIPE)
	sout = s.stdout.read().split('\n')
	ram = int(filter(None, sout[1].split(' '))[2])
	swap = int(filter(None, sout[2].split(' '))[2])
	c.execute("INSERT INTO memory VALUES (%i, %d, %d)" % (timestamp, ram, swap))

conn.commit()
conn.close()
