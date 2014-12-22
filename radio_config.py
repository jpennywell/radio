"""
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

