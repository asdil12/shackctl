#!/usr/bin/python2

import sys
import os
from pysqlite2 import dbapi2 as sqlite3
from time import time
import psutil
import shutil
import json

conn = sqlite3.connect('database/chart.db')
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
	sensorvals = {}
	try:
		cpu = int(open('/sys/class/thermal/thermal_zone0/temp').read())
		sensorvals['cpu'] = round(float(cpu) / 1000, 1)
	except:
		sensorvals['cpu'] = 0
	try:
		sensors = json.load(open('sensors.json'))
		for sensor in ['indoor', 'outdoor']:
			if sensors.get(sensor, False):
				sensor_id = sensors[sensor]
				sensor_file = os.path.join("/sys/bus/w1/devices", sensor_id, "w1_slave")
				value = float(open(sensor_file).read().split("\n")[1].split()[-1][2:])
				value /= 1000
				sensorvals[sensor] = value
			else:
				sensorvals[sensor] = 0
	except:
		raise
		sensorvals['indoor'] = 0
		sensorvals['outdoor'] = 0
	c.execute("INSERT INTO temperature VALUES (%i, %f, %f, %f)" %
		(timestamp, sensorvals['cpu'], sensorvals['indoor'], sensorvals['outdoor'])
	)

	# Load
	cpu = psutil.cpu_percent()
	c.execute("INSERT INTO load VALUES (%i, %d)" % (timestamp, cpu))

	# Memory
	ram = int(psutil.used_phymem() / 1024 / 1024)
	swap = int(psutil.used_virtmem() / 1024 / 1024)
	c.execute("INSERT INTO memory VALUES (%i, %d, %d)" % (timestamp, ram, swap))

conn.commit()
conn.close()
