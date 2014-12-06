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
	import logging, os, sys

	import radio_config as config

	from hw import pots
	from service import led_cfg
	from service import www_cfg
	from radio import rmpd
	from radio import dialview

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
	status = main(sys.argv)
	os._exit(status)
