import signal, logging, os, time, math, random
from . import dialview
from . import rmpd

from multiprocessing.connection import Client

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

		self.DialView = dialview.DialView()

		self.DialLedClient = Client(address=(led_cfg.LED_HOST, led_cfg.LED_DIAL_PORT))
		self.PowerLedClient = Client(address=(led_cfg.LED_HOST, led_cfg.LED_POWER_PORT))

		self.VolumeKnob = pots.VolumePotReader(config.VOL_POT_ADC)
		self.VolumeKnob.smooth_fac = 0.9

		self.TunerKnob = pots.TunerPotReader(config.TUNE_POT_ADC, config.STATION_SET)

		self.Player = rmpd.RadioMPDClient()

		self.WebClient = Client(address=(www_cfg.WEB_HOST, www_cfg.WEB_LISTEN_PORT))


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

				except rmpd.CommandError as e:
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

#			logging.debug(self.__class__.__name__ + "> Stop Web Server")

		except Exception as e:
			logging.critical(self.__class__.__name__ + "> ERROR! Can't stop a service: " + str(e))
		finally:
#			logging.debug(self.__class__.__name__ + "> GPIO cleanup")
#			try:
#				GPIO.cleanup()
#			except RuntimeWarning:
#				pass
			logging.debug(self.__class__.__name__ + "> All cleanup done.")

		if shutdown_system:
			os.system(SHUTDOWN_CMD)

		return 0

# End of RadioObjectCollection


