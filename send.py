#!/usr/bin/python

import sys
from multiprocessing.connection import Client

if len(sys.argv) < 3:
	print("send.py <port> <msg>")
	sys.exit(0)

port = sys.argv[1]
msg = sys.argv[2]

cl = Client(address=('localhost', int(port)))

cl.send(msg)

cl.close()
