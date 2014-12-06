import sys

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

