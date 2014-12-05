#!/usr/bin/env python

import service.www as www

host = '192.168.0.12'
port = 80

server = www.RadioWebServer(host, port)

