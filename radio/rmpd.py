import mpd, logging, time

"""
CommandError

Pull in the mpd.CommandError exception.
"""
class CommandError(mpd.CommandError):
	pass


"""
RadioStream

This extends the mpd.MPDClient class.

Adds a 'ready' method that ensures that the client is still connected.
"""
class RadioStream(mpd.MPDClient):

	rmpd_host = ''
	rmpd_port = 0

	active = 0

	snd_output_id = 0

	stream_id = -1

	def __init__(self, host, port):
		self.rmpd_host = host
		self.rmpd_port = port

		super(RadioStream, self).__init__()

	def ready(self):
		'''
		Ensures that the client is still connected.
		Call this before executing other client commands.
		'''
		while True:
			try:
				status = self.status()
				break
			except mpd.ConnectionError:
				try:
					logging.info(self.__class__.__name__ + "> mpd: Lost connection - reconnect.")
					self.connect(self.rmpd_host, self.rmpd_port)
					time.sleep(1)
				except TypeError:
					logging.error(self.__class__.__name__ + "> mpd: Still can't connect.")
					sys.exit(0)

# End of class RadioStream

class StreamManager():
	streams = []

	active_stream_id = 0

	def __init__(self):
		pass

	def add_stream(self, host, port):
		try:
			stream = RadioStream(host, port)
			self.streams.append(stream)
			stream.stream_id = len(self.streams) - 1
			return stream
		except mpd.ConnectionError:
			return False

	def del_stream(self, stream_id):
		try:
			stream = self.streams[stream_id]
			stream.close()
			return True
		except KeyError:
			return False

	def start_stream(self, stream_id):
		try:
			stream = self.streams[stream_id]
			stream.ready()
			stream.enableoutput(stream.snd_output_id)
			stream.play()
			stream.active = 1
		except KeyError:
			return False
		except mpd.CommandError:
			return False

	def stop_stream(self, stream_id):
		try:
			stream = self.streams[stream_id]
			stream.ready()
			stream.disableoutput(stream.snd_output_id)
			stream.active = 0
		except KeyError:
			return False
		except mpd.CommandError:
			return False

	def switch_stream(self, stream_id):
		old_act_id = self.active_stream_id

		if stream_id == self.active_stream_id:
			if self.streams[self.active_stream_id].active == 1:
				return True
			else:
				self.start_stream(self.active_stream_id)

		self.stop_stream(self.active_stream_id)
		self.start_stream(stream_id)
		self.active_stream_id = stream_id

		return True


	def next_stream(self):
		new_id = self.active_stream_id + 1
		if new_id > len(self.streams) - 1:
			new_id = 0
		if new_id == self.active_stream_id:
			return
		self.switch_stream(new_id)


	def prev_stream(self):
		new_id = self.active_stream_id - 1
		if new_id < 0:
			new_id = len(self.streams) - 1
		if new_id == self.active_stream_id:
			return
		self.switch_stream(new_id)


	def load_playlist(self, stream_id, playlist, shuffle = False):
		try:
			stream = self.streams[stream_id]
			stream.ready()
			stream.clear()
			stream.load(playlist)
			if shuffle:
				stream.shuffle()
			stream.disableoutput(0)
			stream.play()
			
		except KeyError:
			return False
		except mpd.CommandError:
			return False


# End of class StreamManager
