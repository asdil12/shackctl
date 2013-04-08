#!/usr/bin/python2

import devices
import sys

devices.power(sys.argv[1], bool(int(sys.argv[2])), 'api')
