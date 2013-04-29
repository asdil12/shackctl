#!/usr/bin/python2

import sys
import os
from pysqlite2 import dbapi2 as sqlite3
from time import time
import psutil
import shutil
import json

config = json.load(open('chartdb.json'))
conn = sqlite3.connect('database/chart.db')
c = conn.cursor()

def sql(statement):
	if len(sys.argv) > 2 and sys.argv[2] == 'dryrun':
		print statement
		print "---"
	else:
		c.execute(statement)

if len(sys.argv) > 1 and sys.argv[1] == 'init':
	sql("""
		CREATE TABLE temperature
		(timestamp INTEGER, cpu REAL, indoor REAL, outdoor REAL)
	""")
	sql("""
		CREATE TABLE load
		(timestamp INTEGER, cpu INTEGER)
	""")
	sql("""
		CREATE TABLE memory
		(timestamp INTEGER, ram INTEGER, swap INTEGER)
	""")
	sql("""
		CREATE TABLE power
		(timestamp INTEGER, powersupply_12v REAL)
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
	for sensor in ['indoor', 'outdoor']:
		if config['w1']['sensors'].get(sensor, False):
			sensor_id = config['w1']['sensors'][sensor]
			sensor_file = os.path.join("/sys/bus/w1/devices", sensor_id, "w1_slave")
			for i in range(0, 3):
				try:
					content = open(sensor_file).read()
					valid_crc = (content.split("\n")[0].split()[-1] == 'YES')
					assert valid_crc
					value = float(content.split("\n")[1].split()[-1][2:])
					value /= 1000
					sensorvals[sensor] = value
					break
				except:
					sensorvals[sensor] = 0
		else:
			sensorvals[sensor] = 0
	sql("INSERT INTO temperature VALUES (%i, %f, %f, %f)" %
		(timestamp, sensorvals['cpu'], sensorvals['indoor'], sensorvals['outdoor'])
	)

	# Load
	cpu = psutil.cpu_percent()
	sql("INSERT INTO load VALUES (%i, %d)" % (timestamp, cpu))

	# Memory
	ram = int(psutil.used_phymem() / 1024 / 1024)
	swap = int(psutil.used_virtmem() / 1024 / 1024)
	sql("INSERT INTO memory VALUES (%i, %d, %d)" % (timestamp, ram, swap))

	# Power
	sensorvals = {}
	got_data = False
	ec3k_cache_dir = os.path.join(config['cache_dir'], 'ec3k')
	if not os.path.exists(ec3k_cache_dir):
		os.makedirs(ec3k_cache_dir)
	for sensor in ['powersupply_12v']:
		if config['ec3k']['sensors'].get(sensor, False):
			sensorid = config['ec3k']['sensors'][sensor].upper()
			filename = "%s.json" % sensorid
			sensor_file = os.path.join(config['ec3k']['fs_dir'], filename)
			sensor_cache = os.path.join(ec3k_cache_dir, filename)
			if not os.path.exists(sensor_file):
				sensorvals[sensor] = 0
				continue
			sensor_file_timestamp = int(os.stat(sensor_file).st_mtime)
			if os.path.exists(sensor_cache):
				sensor_cache_timestamp = int(os.stat(sensor_cache).st_mtime)
				time_delta = sensor_file_timestamp - sensor_cache_timestamp
				if time_delta > 0:
					new_values = json.load(open(sensor_file))
					old_values = json.load(open(sensor_cache))
					energy_delta = new_values['energy'] - old_values['energy']
					# use time delta from sensors for higher accuracy
					time_delta = new_values['uptime'] - old_values['uptime']
					power = float(energy_delta) / time_delta
					sensorvals[sensor] = power
					got_data = True
			shutil.copyfile(sensor_file, sensor_cache)
		else:
			sensorvals[sensor] = 0
	if got_data:
		sql("INSERT INTO power VALUES (%i, %f)" %
			(timestamp, sensorvals['powersupply_12v'])
		)

conn.commit()
conn.close()
