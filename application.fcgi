#!/usr/bin/python2
from flup.server.fcgi import WSGIServer
from application import app
import os

cwd = os.path.abspath(os.path.dirname(__file__))
os.chdir(cwd)

if __name__ == '__main__':
	app.debug = True
	WSGIServer(app).run()
