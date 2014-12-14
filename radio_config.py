"""
Configuration constants
"""
''' Debug level '''
LOG_LEVEL='DEBUG' 	# Can be any of INFO, DEBUG, WARNING, ERROR, CRITICAL
SHOW_DIAL=True		# Print out a live dial view to the console.

''' Command used for shutting down the system '''
SHUTDOWN_CMD = "sudo shutdown -h now"

''' The pin numbers on the ADC for the pots '''
VOL_POT_ADC = 2
TUNE_POT_ADC = 1

''' MPD Client Information '''
MPD_HOST = 'localhost'	# MPD host connection info
MPD_PORT = 6600			# (default = localhost, 6600)

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
	cur_time = time.localtime()[4]*60
	mpd.play(cur_hour)
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
