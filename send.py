#!/usr/bin/python

import sys
from multiprocessing.connection import Client

port = sys.argv[1]
msg = sys.argv[2]

cl = Client(address=('localhost', int(port)))

cl.send(msg)

cl.close()
