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
	import logging, datetime, time, os, signal, sys, math, random, threading

	import RPi.GPIO as GPIO

	import mpd

	from multiprocessing.connection import Client

	import radio_config as config

	from hw import pots
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

	logging.basicConfig(filename='radio.log', level=getattr(logging, config.LOG_LEVEL))
except IOError as e:
	logging.critical("Can't open log file for write: " + str(e))


"""
RadioObjectCollection

This class is the parent radio class. It contains instances
of all other classes.
"""
class RadioObjectCollection:
	Player = False		# instance of MPD client class
	TunerKnob = False 	# instance of TunerPotReader class
	VolumeKnob = False	# instance of VolumePotReader class
	DialView = False	# instance of DialView class
	WebClient = False
	DialLedClient = None
	PowerLedClient = None

	def __init__(self):
		signal.signal(signal.SIGTERM, self._signal_term_handler)

		self.DialView = DialView()

		self.DialLedClient = Client(led_cfg.LED_HOST, led_cfg.LED_PORT_DIAL, led_cfg.LED_AUTH_KEY)
		self.PowerLedClient = Client(led_cfg.LED_HOST, led_cfg.LED_PORT_POWER, led_cfg.LED_AUTH_KEY)

		self.VolumeKnob = pots.VolumePotReader(config.VOL_POT_ADC)
		self.VolumeKnob.smooth_fac = 0.9

		self.TunerKnob = pots.TunerPotReader(config.TUNE_POT_ADC, config.STATION_SET)

		self.Player = RadioMPDClient()

		self.WebClient = Client(www_cfg.WEB_HOST, www_cfg.WEB_LISTEN_PORT, www_cfg.WEB_AUTH_KEY)


	def _signal_term_handler(self, signal, frame):
		"""
		Register a SIGTERM handler function.
		"""
		logging.info(self.__class__.__name__ + "> SIGTERM. Exiting...")
		self.shutdown()


	def loop(self):
		while True:
			"""
			1.	Read the volume pot.
				Adjust the volume cap and dial brightness
				based on tuning distance.
				Start a shutdown timer if the volume is set low enough.
			"""
			try:
				self.VolumeKnob.read_pot()
			except PotChange:
				"""
				If the volume is low enough, start a timer
				Otherwise, reset it.
				If it's running, see for how long, and
				shutdown if it's past the cutoff.
				"""
				if (self.VolumeKnob.volume <= config.LOW_VOL_TOLERANCE):
					if (low_vol_start == -1):
						logging.info(self.__class__.__name__ + "> Shutdown timer started.")
						low_vol_start = time.time()
					else:
						low_vol_delta = time.time() - low_vol_start

						if low_vol_delta >= config.TIME_FOR_POWER_OFF:
							logging.info(self.__class__.__name__ + "> Volume low - Shutting down...")
							self.shutdown(True)
							return 0
							break
				else:
					low_vol_start = -1
			#End of VolumeKnob.read_pot()

			"""
			2.	Read the tuner knob pot.
				Adjust the volume scaling.
				Update the MPD server.
			"""
			try:
				self.TunerKnob.read_pot()
			except PotChange:
				"""
				Update volume scaling based on tuning distance.
				Adjust dial brightness.
				"""
				if self.TunerKnob.is_tuned():
					try:
						"""
						vol_adj = round(0.5 * (1 + math.erf( \
							((self.cfg_st_radius/1.1) - \
							abs(self.tuning-self.tuned_to()) \
							)/(0.25*self.cfg_st_radius) ) ), 2)
						"""
						r = self.TunerKnob.cfg_st_radius
						d = abs(self.TunerKnob.tuning - self.TunerKnob.tuned_to())
						vol_adj = round(0.5 * (1 + math.erf(3.64 - 4*d/r)), 2)
					except (ArithmeticError, FloatingPointError, ZeroDivisionError):
						vol_adj = 1.0
				else:
					vol_adj = 0

				self.VolumeKnob.volume_cap = vol_adj * self.VolumeKnob.volume
				self.VolumeKnob.volumize(self.VolumeKnob.volume_cap)

				br = led_cfg.LED_MIN_DUTY if vol_adj == 0 else vol_adj * led_cfg.LED_DUTY_CYCLE
				self.DialLedClient.send(['adjust_brightness', br])


				"""
				Update the MPD server.
				"""
				try:
					# Make sure we're connected
					(st_name, st_random, st_play_func) = self.TunerKnob.station_list[self.TunerKnob.SID]

					if (st_random):
						sid = random.randrange(0,
								len(self.Player.playlist()) - 1,
								1)
					else:
						sid = 0

					logging.info(self.__class__.__name__ + "> Load " + st_name)
					logging.info(self.__class__.__name__ + "> Playing " + str(sid))

					self.Player.ready()
					self.Player.clear()
					self.Player.load(st_name)
					self.Player.random(1 if st_random else 0)

					if (callable(st_play_func)):
						st_play_func(self.Player)
					else:
						self.Player.play(sid)

					"""
					Update the web server
					"""
					self.WebClient.send(['html', self.Player.currentsong()])

				except mpd.CommandError as e:
					logging.error(self.__class__.__name__ + "> mpd:Error load " + st_name + ":" + str(e))
				except ValueError as e:
					logging.error(self.__class__.__name__ + "> ValueError on play " + st_name + ": " + str(e))
			#End of TunerKnob.read_pot()


			"""
			3.	Finish the loop with a delay, and print any debug.
			"""
			if SHOW_DIAL:
				self.DialView.display(self.VolumeKnob, self.TunerKnob)
			time.sleep(0.25)
		#end while
		return


	def shutdown(self, shutdown_system=False):
		"""
		Do a cleanup of services and hardware.
		"""
		logging.debug(self.__class__.__name__ + "> Cleaning up...")

		try:
			logging.debug(self.__class__.__name__ + "> Show info on leds.")
			self.PowerLedClient.send('blink')
			self.DialLedClient.send('off')

			logging.debug(self.__class__.__name__ + "> Stop MPD client")
			self.Player.ready()
			self.Player.stop() 
			self.Player.close()
			self.Player.disconnect()

			logging.debug(self.__class__.__name__ + "> Stop Web Server")

		except Exception as e:
			logging.critical(self.__class__.__name__ + "> ERROR! Can't stop a service: " + str(e))
		finally:
			logging.debug(self.__class__.__name__ + "> GPIO cleanup")
			try:
				GPIO.cleanup()
			except RuntimeWarning:
				pass
			logging.debug(self.__class__.__name__ + "> All cleanup done.")

		if shutdown_system:
			os.system(SHUTDOWN_CMD)

		return 0

# End of RadioObjectCollection


"""
RadioMPDClient

This extends the mpd.MPDClient class.

Adds a 'ready' method that ensures that the client is still connected.
"""
class RadioMPDClient(mpd.MPDClient):

	def ready(self):
		"""
		Ensures that the client is still connected.
		Call this before executing other client commands.
		"""
		while True:
			try:
				status = self.status()
				break
			except mpd.ConnectionError:
				try:
					self.connect(config.MPD_HOST, config.MPD_PORT)
					time.sleep(1)
				except TypeError:
					print("ERROR: Still can't connect.")
					sys.exit(0)

# End of class RadioMPDClient




"""
DialView

"""
class DialView:
	def __init__(self):
		pass

	def display(self, Volume, Tuner):
		"""
		Prints out a view of the radio dial and tuning,
		as well as volume/volume_cap and any other message
		"""
		destr = "SetVol[%s] LimVol[%s] " % ( \
					int(round(Volume.volume / 10.24)), \
					int(round(Volume.volume_cap / 10.24)) \
				)
		(st_L, st_R) = Tuner.get_closest_freqs()
		tuned_freq = Tuner.tuned_to()
		fr_list = [0]
		new_list = []
		new_list.extend(Tuner.freq_list)
		new_list.append(1023)
		for fr in new_list:
			l_mark = ""
			r_mark = ""
			if (fr == st_R):
				if (st_L == tuned_freq):
					l_mark = "<"
				elif (st_R == tuned_freq):
					r_mark = ">"

				fr_list.append(l_mark + \
								str(Tuner.tuning) + \
								r_mark)
			else:
				fr_list.append('---')
			fr_list.append(fr)
		dial_string = ' '.join(str(x) for x in fr_list)
		debug_string = destr + '[' + dial_string + ' ] '
		sys.stdout.write(debug_string + "\r")
		sys.stdout.flush()


	
def main(argv):
	"""
	Main loop.

	Setup pins, turn on LEDs, watch pots.
	"""

	try:
		"""
		Setup the radio object, and begin startup routine.
		"""
		Radio = RadioObjectCollection()
		logging.debug("main()> Startup Ok")

		logging.debug("main()> DialLed fade in.")
		Radio.DialLedClient.send('fade_up')

		logging.debug("main()> PowerLed flicker on.")
		Radio.PowerLedClient.send('flicker')

		logging.debug(Radio.TunerKnob.freq_list)
		logging.debug(Radio.TunerKnob.station_list)

		logging.debug("main()> Waiting for dial led to finish...")
		Radio.DialLedClient.send('wait_for_done')

		Radio.Player.ready()

		logging.debug("main()> Main loop.")

		Radio.loop()

	except KeyboardInterrupt:
		"""
		On a Ctrl-C, shutdown the radio program.
		The Pi stays running.
		"""
		logging.debug("main()> Ctrl-C. Quitting.")
		Radio.shutdown()
		logging.debug("main()> Shutdown complete.")
		return 0
	except OSError as e:
		"""
		This is probably because we can't read the music directory?"
		"""
		logging.critical("main()> OSError: " + str(e)) 
	except IOError as e:
		"""
		import stations probably failed.
		"""
		logging.critical("main()> IOError: " + str(e))
	except RuntimeError as e:
		logging.critical("main()> RuntimeError: " + str(e))
	except Exception as e:
		print(str(e))
	finally:
		logging.debug("main()> Finished. Return 0")
		return 0

#End of main()


"""
Run the program.
"""
if __name__ == "__main__":
	status = main(sys.argv)
	os._exit(status)
