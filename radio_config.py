"""
Configuration constants
"""
''' Debug level '''
LOG_LEVEL='DEBUG' 	# Can be any of INFO, DEBUG, WARNING, ERROR, CRITICAL
SHOW_DIAL=True

''' Command used for shutting down the system '''
SHUTDOWN_CMD = "sudo shutdown -h now"

''' Hardware flags '''
ENABLE_SPI = False	# Enable SPI access to pots

''' Pins (BCM mode) '''
LED_PIN_POWER = 17	# GPIO pin numbers for led access
LED_PIN_DIAL = 27	# NOTE: This uses the BCM numbering

VOL_POT_ADC = 2 	# Pins for the pots on the ADC chip
TUNE_POT_ADC = 1 

SPICLK = 18		# MCP3008 pins on the RPi
SPIMISO = 23	# This IC does the ADC conversion for reading from the pots
SPIMOSI = 24
SPICS = 25

''' Web serving '''
ENABLE_WEB = True
WEB_HOST = '192.168.0.12'
WEB_PORT = 80

''' MPD Client Information '''
MPD_HOST = 'localhost'	# MPD host connection info
MPD_PORT = 6600			# (default = localhost, 6600)

''' Tuning config '''
GAP_FACTOR = 1.18	# Factor by which the tuning gaps should be larger than
					# the station radii. Default = 1.18 (18% larger)

''' LED Settings '''
PWM_FREQ = 50 # Frequency for LED PWM
LED_MIN_DUTY = 1.		# Minimum duty cycle (default = 1.)
LED_DUTY_CYCLE = 30.	# Default duty cycle for an led (default = 30.)

LED_RAMP_START = 8. # Starting ramp value (larger = slower, default = 9)
LED_RAMP_RATE = 12. # Rate to fade by (larger = slower, default = 20)
LED_RAMP_CUTOFF = 1.1 # Breakpoint to stop fading (larger=sooner, default=1.1)

POWER_FLICKER_FREQ = 1	# At what frequency the power led is flickered.
						# (Between 1 and 10, default = 1.)

''' Volume Settings for shutdown '''
LOW_VOL_TOLERANCE = 10	# If the volume is below this tolerance (default = 10), 
TIME_FOR_POWER_OFF = 10	# for this amount of time (seconds, default = 10), 
						# then the system is shutdown.




"""
Radio Definitions

Each line in STATION_SET is in the format
	[ playlist_name (str), randomize (bool), station play function (func) ]

The station play function can be set to customize queueing or selection
of a playlist. Play functions must be defined *before* STATION_SET.

The play function will be passed an mpd client object to be used.

Play function example:

def my_station_play(mpd):
	mpd.play()

"""
def wjsv_queue(mpd):
	import time
	cur_hour = time.localtime()[3] - 6
	mpd.play(cur_hour)
	cur_time = time.localtime()[4]*60
	mpd.seekcur(cur_time)


STATION_SET = [
	# playlist name, 	randomize,	station play function
	# (required)		(boolean)	(False for default)
	['itunes', 			True, 		False ],
	['oldmusic',		True,		False ],
	['wjsv',			False,		wjsv_queue ],
	['jazzfm',			False,		False ]
]

#
#
# EOF
