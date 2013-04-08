shackctl
========

Raspberry Pi WebUI

Installation:
-------------

- install rcswitch-pi
- install sudo
- Add this line to `/etc/sudoers`: `ALL ALL=(ALL) NOPASSWD: /usr/bin/rcswitch-pi`
- pip install Flask-Bootstrap
- Make the main directory writeable by webuser
- Make the database directory writeable by webuser
- Run ./application.py (or use wsgi/fcgi)
