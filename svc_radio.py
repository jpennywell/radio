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
	import logging, os, sys, time, signal, math, random, socket

	import radio_config as config

	from multiprocessing.connection import Client

	from hw import pots
	from radio import rmpd
	from radio import dialview

	from service import led_cfg
	from service import www_cfg

except RuntimeError as e:
	logging.critical("Error loading an import: " + str(e))
	sys.exit(0)

if (os.getuid() != 0):
	logging.critical("This process must be run as root. Exiting.")
	sys.exit(0)

try:
	# Reset/truncate the log file
	with open('radio.log', 'w'):
		pass

#	logging.basicConfig(filename='radio.log', level=getattr(logging, config.LOG_LEVEL))
	logging.basicConfig(level=getattr(logging, config.LOG_LEVEL))
except IOError as e:
	logging.critical("Can't open log file for write: " + str(e))



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

		logging.debug('Startup begun')

		logging.debug('DialView started.')
		text_dial = dialview.DialView()


		try:
			logging.debug('Connecting to dial Led service')
			cl_dial_led = Client( (led_cfg.LED_HOST, led_cfg.LED_DIAL_PORT) )
			logging.debug('Connecting to power Led service')
			cl_power_led = Client( (led_cfg.LED_HOST, led_cfg.LED_POWER_PORT) )
			logging.debug('Connecting to web service')
			cl_web_server = Client( (www_cfg.WEB_HOST, www_cfg.WEB_LISTEN_PORT) )
		except socket.error as e:
			logging.warning("Can't connect to a service: " + str(e))

		logging.debug('Creating volume knob')
		vol_knob = pots.VolumePotReader(config.VOL_POT_ADC)
		vol_knob.smooth_fac = 0.9

		logging.debug('Creating tuning knob')
		tuner_knob = pots.TunerPotReader(config.TUNE_POT_ADC, config.STATION_SET)

		logging.debug('Starting MPD client')
		player = rmpd.RadioMPDClient(config.MPD_HOST, config.MPD_PORT)

		logging.debug("main()> Startup Ok")

		logging.debug("main()> DialLed fade in.")
		cl_dial_led.send('fade_up')

		logging.debug("main()> PowerLed flicker on.")
		cl_power_led.send('flicker')

		logging.debug(tuner_knob.freq_list)
		logging.debug(tuner_knob.station_list)

		logging.debug("main()> Waiting for dial led to finish...")
		cl_dial_led.send('wait_for_done')

		player.ready()

		logging.debug("main()> Main loop.")

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
				if (vol_knob.volume <= config.LOW_VOL_TOLERANCE):
					if (low_vol_start == -1):
						logging.info("> Shutdown timer started.")
						low_vol_start = time.time()
					else:
						low_vol_delta = time.time() - low_vol_start

						if low_vol_delta >= config.TIME_FOR_POWER_OFF:
							logging.info("> Volume low - Shutting down...")
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
			except pots.PotChange as change:
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
						logging.info("Math: r="+str(r)+", d="+str(d)+",adj="+str(vol_adj))
					except (ArithmeticError, FloatingPointError, ZeroDivisionError) as e:
						logging.error("Math error: " + str(e))
						vol_adj = 1.0
				else:
					vol_adj = 0

				vol_knob.volume_cap = vol_adj * vol_knob.volume
				vol_knob.volumize(vol_knob.volume_cap)
				logging.debug("Readjusting volume to " + str(vol_adj) + " of " + str(vol_knob.volume) + ": " + str(vol_knob.volume_cap))

				if cl_dial_led is not None:
					cl_dial_led.send(['adjust_brightness', vol_adj])

				"""
				Update the MPD server.
				"""
				if change.is_new_station:
					try:
						(st_name, st_random, st_play_func) = tuner_knob.station_list[tuner_knob.SID]

						if (st_random):
							sid = random.randrange(0,
									len(player.playlist()) - 1,
									1)
						else:
							sid = 0

						logging.info("> Load " + st_name)
						logging.info("> Playing " + str(sid))

						player.ready()
						player.clear()
						player.load(st_name)
						player.random(1 if st_random else 0)

						if (callable(st_play_func)):
							st_play_func(player)
						else:
							player.play(sid)

						"""
						Update the web server
						"""
						if cl_web_server is not None:
							cl_web_server.send(['html', player.currentsong()])

					except rmpd.CommandError as e:
						logging.error("> mpd:Error load " + st_name + ":" + str(e))
					except ValueError as e:
						logging.error("> ValueError on play " + st_name + ": " + str(e))
				#endif
			#End of TunerKnob.read_pot()


			"""
			3.	Finish the loop with a delay, and print any debug.
			"""
			if config.SHOW_DIAL:
				text_dial.display(vol_knob, tuner_knob)
			time.sleep(0.25)
		#end while

	except (KeyboardInterrupt, RadioCleanup):
		"""
		Do a cleanup of services and hardware.
		"""
		logging.debug("> Cleaning up...")

		try:
			logging.debug("> Show info on leds.")
			if cl_power_led is not None:
				cl_power_led.send('blink')

			if cl_dial_led is not None:
				cl_dial_led.send('off')

			logging.debug("> Stop MPD client")
			player.ready()
			player.stop() 
			player.close()
			player.disconnect()
		except Exception as e:
			logging.critical("> ERROR! Can't stop a service: " + str(e))
		finally:
			logging.debug("> All cleanup done.")

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
#	finally:
#		logging.debug("main()> Finished. Return 0")
#		return 0

#End of main()


"""
Run the program.
"""
if __name__ == "__main__":
	logging.info("Calling main()")
	status = main(sys.argv)
	os._exit(status)
