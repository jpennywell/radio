#!/usr/bin/env python

import radio.rmpd as rmpd
import service.option_loader as OL
import sys, time
import logging

logging.basicConfig(level=logging.DEBUG)

opt_ldr = OL.OptionLoader('config.db')
host = opt_ldr.fetch('MPD_HOST')
port = opt_ldr.fetch('MPD_PORT')
print("Servers starting at " + host + ":" + str(port))

sm = rmpd.StreamManager(host, port)

sm.add_stream('iTunes', 'itunes', True)
sm.add_stream('Archive Radio', 'archiveradio')
sm.add_stream('WJSV Full-Day', 'wjsv', False, 'play_by_seek')
sm.add_stream('JAZZ FM', 'jazzfm')

print("Playing streams")
for i in range(0, len(sm.streams)):
	logging.debug("[ StreamManager ] : Playing stream " + str(i))
	sm.switch_stream(i)
	if i+1 < len(sm.streams): 
		logging.debug("[ StreamManager ] : Preloading stream " + str(i+1))
		sm.load_stream(i+1)
	time.sleep(10)
