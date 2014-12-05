#!/usr/bin/env python

import www.server
import www.config

from . import cfg_ports

server = RadioWebServer(www.config.host, www.config.port)
