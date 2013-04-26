shackctl
========

Raspberry Pi WebUI

Installation:
-------------

- install rcswitch-pi
- install sudo
- Add this line to `/etc/sudoers`: `ALL ALL=(ALL) NOPASSWD: /usr/bin/rcswitch-pi`
- pip install Flask-Bootstrap psutil pysqlite
- Make the main directory writeable by webuser
- Make the database directory writeable by webuser
- Copy and edit chartdb.json for 1-Wire / EC3K logging
- Run ./application.py (or use wsgi/fcgi)
- Run `./chartdb init` to create sqlite tables for logging
- Add something like `cd shackctl ; ./chartdb insert` to cron
