#!/usr/bin/env python

import radio.rmpd as rmpd
import sys, time

sm = rmpd.StreamManager()

one = sm.add_stream('localhost', 6600)
two = sm.add_stream('localhost', 6601)

if one == False or two == False:
	print("Can't create streams")
	sys.exit(0)

print("Starting one stream:")
sm.load_playlist(0, 'oldmusic')
sm.start_stream(0)

try:
	stream_id = 0
	while True:
		print("Playing stream " + str(stream_id))
		sm.switch_stream(stream_id)
		print("Sleeping for 5s")
		time.sleep(5)
		stream_id += 1
		if stream_id == 2:
			stream_id = 0
except KeyboardInterrupt:
	sys.exit(0)
