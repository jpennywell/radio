#!/usr/bin/env python
"""
Network Radio

This connects to an mpd server and plays configured playlists using 
some hardware knobs (volume & tuning).

Turning the volume below a set tolerance for a set amount of time
will shut down the RPi. (Values set in radio_config.py)

Todo:

	> Use Led's to indicate errors, shutdown process, etc.

	> Error-test tuning.

"""

try:
	import logging, os, sys, time, signal, math, random, socket, sqlite3

	from multiprocessing.connection import Client

	import service.option_loader as OL
	import service.pots as pots
	import radio.rmpd as rmpd
	import radio.dialview as dialview

except RuntimeError as e:
	logging.critical("[ Radio ] Error loading an import: " + str(e))
	sys.exit(0)

if (os.getuid() != 0):
	logging.critical("[ Radio ] This process must be run as root. Exiting.")
	sys.exit(0)

opt_ldr = OL.OptionLoader('config.db')

try:
	# Reset/truncate the log file
	with open('radio.log', 'w'):
		pass

	logging.basicConfig(level=getattr(logging, opt_ldr.fetch(LOG_LEVEL)))
except IOError as e:
	logging.critical("[ Radio ] Can't open log file for write: " + str(e))



class RadioCleanup(Exception):
	pass



	
def main(argv):
	"""
	Main loop.

	Setup pins, turn on LEDs, watch pots.
	"""

	do_system_shutdown = False

	try:
		"""
		Setup the radio object, and begin startup routine.
		"""
#		signal.signal(signal.SIGTERM, radio_cleanup)

		logging.debug('[ Radio ] Startup begun')

		logging.debug('[ Radio ] DialView started.')
		text_dial = dialview.DialView()


		try:
			logging.debug('[ Radio ] Connecting to dial Led service')
			cl_dial_led = Client( (opt_ldr.fetch('LED_HOST'), opt_ldr.fetch('LED_DIAL_PORT')) )
			logging.debug('[ Radio ] Connecting to power Led service')
			cl_power_led = Client( (opt_ldr.fetch('LED_HOST'), opt_ldr.fetch('LED_POWER_PORT')) )
			logging.debug('[ Radio ] Connecting to web service')
			cl_web_server = Client( (opt_ldr.fetch('WEB_LISTEN_HOST'), opt_ldr.fetch('WEB_LISTEN_PORT')) )
		except socket.error as e:
			logging.warning("[ Radio ] Can't connect to a service: " + str(e))

		logging.debug('[ Radio ] Creating volume knob')
		vol_knob = pots.VolumePotReader(opt_ldr.fetch('VOL_POT_ADC'))
		vol_knob.smooth_fac = 0.9

		logging.debug('[ Radio ] Creating tuning knob')
		con = sqlite3.connect('config.db')
		with con:
			cur = con.cursor()
			cur.execute("SELECT * FROM playlists")
			station_set = cur.fetchall()
		tuner_knob = pots.TunerPotReader(opt_ldr.fetch('TUNE_POT_ADC'), station_set)

		logging.debug('[ Radio ] Starting MPD client')
		player = rmpd.RadioMPDClient(opt_ldr.fetch('MPD_HOST'), opt_ldr.fetch('MPD_PORT'))

		logging.debug("[ Radio ] Startup Ok")

		logging.debug("[ Radio ] DialLed fade in.")
		cl_dial_led.send('fade_up')

		logging.debug("[ Radio ] PowerLed flicker on.")
		cl_power_led.send('flicker')

		logging.debug(tuner_knob.freq_list)
		logging.debug(tuner_knob.station_list)

		logging.debug("[ Radio ] Waiting for dial led to finish...")
		cl_dial_led.send('wait_for_done')

		player.ready()

		logging.debug("[ Radio ] Main loop.")

		while True:
			"""
			1.	Read the volume pot.
				Adjust the volume cap and dial brightness
				based on tuning distance.
				Start a shutdown timer if the volume is set low enough.
			"""
			try:
				vol_knob.read_pot()
			except pots.PotChange:
				"""
				If the volume is low enough, start a timer
				Otherwise, reset it.
				If it's running, see for how long, and
				shutdown if it's past the cutoff.
				"""
				if (vol_knob.volume <= opt_ldr.fetch('LOW_VOL_TOLERANCE')):
					if (low_vol_start == -1):
						logging.info("[ Radio ] Shutdown timer started.")
						low_vol_start = time.time()
					else:
						low_vol_delta = time.time() - low_vol_start

						if low_vol_delta >= opt_ldr.fetch('TIME_FOR_POWER_OFF'):
							logging.info("[ Radio ]  Volume low - Shutting down...")
							do_system_shutdown = True
							raise RadioCleanup
							return 0
							break
				else:
					low_vol_start = -1

			"""
			2.	Read the tuner knob pot.
				Adjust the volume scaling.
				Update the MPD server.
			"""
			try:
				tuner_knob.read_pot()
			except pots.PotChange as pot_notif:
				"""
				Update volume scaling based on tuning distance.
				Adjust dial brightness.
				"""
				if tuner_knob.is_tuned():
					try:
						"""
						vol_adj = round(0.5 * (1 + math.erf( \
							((self.cfg_st_radius/1.1) - \
							abs(self.tuning-self.tuned_to()) \
							)/(0.25*self.cfg_st_radius) ) ), 2)
						"""
						r = tuner_knob.cfg_st_radius
						d = abs(tuner_knob.tuning - tuner_knob.tuned_to())
						vol_adj = round(0.5 * (1 + math.erf(3.64 - 4*d/r)), 2)
					except (ArithmeticError, FloatingPointError, ZeroDivisionError) as e:
						logging.error("[ Radio ] Math error: " + str(e))
						vol_adj = 1.0
				else:
					vol_adj = 0

				vol_knob.volume_cap = vol_adj * vol_knob.volume
				vol_knob.volumize(vol_knob.volume_cap)

				if cl_dial_led is not None:
					cl_dial_led.send(['adjust_brightness', vol_adj])

				"""
				Update the MPD server.
				"""
				if pot_notif.is_new_station:
					try:
						(st_name, st_random, st_play_func) = tuner_knob.station_list[tuner_knob.SID]

						player.ready()
						player.clear()

						logging.info("[ Radio ] Load " + st_name)
						player.load(st_name)
						player.random(1 if st_random else 0)

						if (st_random):
							sid = random.randrange(0,
									len(player.playlist()) - 1,
									1)
						else:
							sid = 0

						logging.info("[ Radio ] Playing " + str(sid))

						if (callable(st_play_func)):
							st_play_func(player)
						else:
							player.play(sid)

						"""
						Update the web server
						"""
						if cl_web_server is not None:
							songdata = player.currentsong()
							status = player.status()
							senddata = dict()
							senddata['artist'] = songdata['artist']
							senddata['album'] = songdata['album']
							senddata['title'] = songdata['title']
							senddata['file'] = songdata['file']
							senddata['elapsed'] = status['elapsed']
							senddata['time'] = songdata['time']
							cl_web_server.send(['indexhtml', senddata])

					except rmpd.CommandError as e:
						logging.error("[ Radio ] mpd:Error load " + st_name + ":" + str(e))
					except ValueError as e:
						logging.error("[ Radio ]  ValueError on play " + st_name + ": " + str(e))
					except IOError as e:
						logging.error("[ Radio ] Can't send data to web server")
				#endif
			#End of TunerKnob.read_pot()


			"""
			3.	Finish the loop with a delay, and print any debug.
			"""
			if opt_ldr.fetch('SHOW_DIAL'):
				text_dial.display(vol_knob, tuner_knob)
			time.sleep(0.25)
		#end while
	except IOError as e:
		logging.error("[ Radio ] Can't send data to listener: " + str(e))
	except (KeyboardInterrupt, RadioCleanup):
		"""
		Do a cleanup of services and hardware.
		"""
		logging.debug("[ Radio ] Cleaning up...")

		try:
			logging.debug("[ Radio ] Show info on leds.")
			if cl_power_led is not None:
				cl_power_led.send('blink')

			if cl_dial_led is not None:
				cl_dial_led.send('off')

			logging.debug("[ Radio ] Stop MPD client")
			player.ready()
			player.stop() 
			player.close()
			player.disconnect()
		except Exception as e:
			logging.critical("[ Radio ] ERROR! Can't stop a service: " + str(e))
		finally:
			logging.debug("[ Radio ] All cleanup done.")

		if do_system_shutdown:
			os.system(SHUTDOWN_CMD)

		return 0

#	except OSError as e:
#		"""
#		This is probably because we can't read the music directory?"
#		"""
#		logging.critical("main()> OSError: " + str(e)) 
#	except RuntimeError as e:
#		logging.critical("main()> RuntimeError: " + str(e))
#	except Exception as e:
#		print(str(e))
	finally:
		logging.debug("[ Radio ] main() Finished. Return 0")
		return 0

#End of main()


"""
Run the program.
"""
if __name__ == "__main__":
	logging.info("[ Radio ] Calling main()")
	status = main(sys.argv)
	os._exit(status)
