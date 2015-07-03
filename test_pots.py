#!/usr/bin/env python3

import sys
import time

import service.pots as pots
import service.option_loader as OL
opt_ldr = OL.OptionLoader('config.db')

lrg_pot = pots.PotReader(opt_ldr.fetch('TUNE_POT_ADC'))
lrg_pot.smooth_fac = 1

ct=0
slp=0.1

f=open('potlog.txt', 'w')

def progress(pot):
	global ct
	val = pot.last_read
	perc = int(val / 10.23)
#	sys.stdout.write("\r[{0}] {1}%" .format('#'*int(perc/2), perc))
	sys.stdout.write("\r%d%%" % int(val))
	sys.stdout.flush()
	f.write(str(ct) + ',' + str(val) + "\n")
	time.sleep(slp)
	ct += slp

try:
	while True:
		try:
			val = lrg_pot.read_pot()
		except pots.PotChange:
			pass
		finally:
			progress(lrg_pot)
except KeyboardInterrupt:
	f.close()
	sys.exit(0)
