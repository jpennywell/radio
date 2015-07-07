#!/usr/bin/env python3
"""
Network Radio

This connects to an mpd server and plays configured playlists using 
some hardware knobs (volume & tuning).

Turning the volume below a set tolerance for a set amount of time
will shut down the RPi.
"""

"""
Local defines
"""
# Time tick for the main loop
TICK = 0.2

"""
Imports
"""
try:
	import fcntl, logging, os, sys, time, signal, math, queue, random, socket, sqlite3, struct

	import service.led
	import service.www
	import service.option_loader
	import service.pots
	import radio.rmpd
	import radio.dialview

except RuntimeError as e:
	logging.critical("[ Radio ] Error loading an import: " + str(e))
	sys.exit(0)

"""
Ensure run as root.
"""
if (! hasattr(os, 'getuid')) or (os.getuid() != 0):
	logging.critical("[ Radio ] This process must be run as root. Exiting.")
	sys.exit(0)

"""
Open config database.
"""
opt_ldr = service.option_loader.OptionLoader('config.db')

try:
	# Reset/truncate the log file
	with open('main.log', 'w'):
		pass
	logging.basicConfig(level=getattr(logging, opt_ldr.fetch('LOG_LEVEL')))
except IOError as e:
	logging.critical("[ Radio ] Can't open log file for write: " + str(e))


"""
Miscellaneous classes and functions
"""
class RadioCleanup(Exception):
	pass

def get_ip_address(ifname):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(
                s.fileno(),
                0x8915,  # SIOCGIFADDR
                struct.pack('256s', bytes(ifname[:15], 'UTF-8'))
                )[20:24])


def main(argv):
	"""
	Main loop.

	Setup pins, turn on LEDs, watch pots.
	"""

	do_system_shutdown = False
	low_vol_start = -1

	try:
		"""
		Setup the radio object, and begin startup routine.
		"""
		logging.debug('[ Radio ] Startup begun')

		logging.debug('[ Radio ] Starting LED service')
		dial_led_queue = queue.Queue()
		pwr_led_queue = queue.Queue()

		dial_led = service.led.Led(dial_led_queue, opt_ldr.fetch('LED_DIAL_PIN'))
		pwr_led = service.led.Led(pwr_led_queue, opt_ldr.fetch('LED_POWER_PIN'))

		dial_led.start()
		pwr_led.start()

		logging.debug("[ Radio ] PowerLed flicker on.")
		pwr_led_queue.put('flicker')

		logging.debug("[ Radio ] DialLed fade in.")
		dial_led_queue.put('fade_up')
		# This doesn't work, b/c dial_led is it's own thread.
		# dial_led_queue.join()
		while dial_led_queue.empty() == False:
			time.sleep(TICK)
		logging.debug('[ Radio ] Fade up done. Continuing.')

		if opt_ldr.fetch('SHOW_DIAL'):
			logging.debug('[ Radio ] DialView started.')
			text_dial = radio.dialview.DialView()

		logging.debug('[ Radio ] Starting WWW service')
		web_svr_queue = queue.Queue()
		web_svr = service.www.RadioWebServer(
				web_svr_queue,
				get_ip_address(opt_ldr.fetch('WEB_INTERFACE')),
				opt_ldr.fetch('WEB_HTTP_PORT'))
		web_svr.start()

		logging.debug('[ Radio ] Creating volume knob')
		vol_knob = service.pots.VolumePotReader(opt_ldr.fetch('VOL_POT_ADC'))
		vol_knob.smooth_fac = 0.9

		logging.debug('[ Radio ] Creating tuning knob')
		con = sqlite3.connect('config.db')
		with con:
			cur = con.cursor()
			cur.execute("SELECT * FROM playlists")
			station_set = cur.fetchall()
		tuner_knob = service.pots.TunerPotReader(opt_ldr.fetch('TUNE_POT_ADC'), len(station_set))

		logging.debug('[ Radio ] Starting MPD stream manager')
		str_host = opt_ldr.fetch('MPD_HOST')
		str_port = opt_ldr.fetch('MPD_PORT')
		str_man = radio.rmpd.StreamManager(str_host, str_port, 2)
		for st in station_set:
			(name, playlist, random, play_func) = st[1:]
			str_man.register_stream(str(name), str(playlist), bool(random), str(play_func))

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
			except service.pots.PotChange:
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
			except service.pots.PotChange as pot_notif:
				"""
				Update volume scaling based on tuning distance.
				Adjust dial brightness.
				"""
				if tuner_knob.is_tuned():
					try:
						r = tuner_knob.cfg_st_radius
						g = tuner_knob.cfg_st_gap
						fac = opt_ldr.fetch('GAP_FACTOR')
						num_st = len(str_man.streams)
						d = abs(tuner_knob.tuning - tuner_knob.tuned_to())
						vol_adj = 0.5 * (1 + math.erf((r - d)/(0.4*r)))
					except (ArithmeticError, FloatingPointError, ZeroDivisionError) as e:
						logging.error("[ Radio ] Math error: " + str(e))
						vol_adj = 1.0
				else:
					vol_adj = 0

				if vol_adj > 1:
					vol_adj = 1
				if vol_adj < 0:
					vol_adj = 0

				d_vol = abs(int(vol_knob.volume_cap) - int(vol_adj * vol_knob.volume))
				if d_vol > 3:
					vol_knob.volume_cap = vol_adj * vol_knob.volume
					vol_knob.volumize(vol_knob.volume_cap)
#					dial_led_queue.put(['adjust_brightness', vol_adj])


				"""
				Update the MPD server.
				"""
				if pot_notif.is_new_station:
					try:
						"""
						Prepare backup stream.
						If tuned to the left, pre-load the right-most station,
						and vice-versa.
						If tuned to the first station (L or R of it),
						then pre-load station #2.
						If tuned to the last station (L or R of it),
						then pre-load station before it.
						"""
						station_id = tuner_knob.SID
						str_man.activate_stream(tuner_knob.SID)

						st_id_L = station_id - 1
						if st_id_L < 0:
							st_id_L = station_id + 1

						st_id_R = station_id + 1
						if st_id_R > len(str_man.streams):
							st_id_L = station_id - 1

						(st_L, st_R) = tuner_knob.get_closest_freqs()
						if st_L == tuner_knob.tuned_to():
							str_man.preload(st_id_R)
						elif st_R == tuner_knob.tuned_to():
							str_man.preload(st_id_R)

						"""
						Update the web server
						"""
						songdata = str_man.query_server('currentsong')
						status = str_man.query_server('status')
						senddata = dict()
						keys = ('artist','album','title','file','elapsed','time')
						senddata = [songdata for k in keys]
						web_svr_queue.put(['html', senddata])

					except radio.rmpd.CommandError as e:
						logging.error("[ Radio ] mpd:Error load " + st_name + ":" + str(e))
						pass
					except ValueError as e:
						logging.error("[ Radio ]  ValueError on play " + st_name + ": " + str(e))
					except IOError as e:
						logging.error("[ Radio ] Can't send data to web server")
				#endif
			#End of TunerKnob.read_pot()


			"""
			3.	Show a tuning dial if configured to do so; finish the loop with a delay.
			"""
			if opt_ldr.fetch('SHOW_DIAL'):
				text_dial.display(vol_knob, tuner_knob)

			time.sleep(TICK)
		#end while
	except (KeyboardInterrupt, RadioCleanup):
		"""
		Do a cleanup of services and hardware.
		"""
		logging.debug("[ Radio ] Cleaning up...")

		pwr_led_queue.put('quit')
		dial_led_queue.put('quit')
		web_svr_queue.put('quit')
#		pwr_led_queue.join()
#		dial_led_queue.join()
#		web_svr_queue.join()

		if do_system_shutdown:
			play_mp3('beep.mp3')
			os.system(SHUTDOWN_CMD)

		return 0

	except OSError as e:
		"""
		This is probably because we can't read the music directory?"
		"""
		logging.critical("[ main() ] OSError: " + str(e)) 
	except RuntimeError as e:
		logging.critical("[ main() ] RuntimeError: " + str(e))

#End of main()


"""
Run the program.
"""
if __name__ == "__main__":
	logging.info("[ Radio ] Calling main()")
	status = main(sys.argv)
	os._exit(status)
