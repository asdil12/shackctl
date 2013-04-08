#!/usr/bin/python2
from flup.server.fcgi import WSGIServer
from application import app

if __name__ == '__main__':
	WSGIServer(app).run()
