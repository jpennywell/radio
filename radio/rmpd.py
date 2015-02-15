import mpd, logging, time

"""
CommandError

Pull in the mpd.CommandError exception.
"""
class CommandError(mpd.CommandError):
	pass


"""
RadioMPDClient

This extends the mpd.MPDClient class.

Adds a 'ready' method that ensures that the client is still connected.
"""
class RadioMPDClient(mpd.MPDClient):

	def __init__(self, host, port):
		self.rmpd_host = host
		self.rmpd_port = port

		super(RadioMPDClient, self).__init__()

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

# End of class RadioMPDClient

class StreamManager():
	streams = []

	active_stream = 0

	def __init__(self):
		pass

	def add_stream(self, host, port):
		stream = RadioMPDClient(host, port)
		self.streams.append( stream )

	def del_stream(self, stream_id):
		try:
			if stream_id == self.active_stream:
				self.switch_stream()
			stream = self.streams[stream_id]
			stream.close()
		except KeyError:
			return False

	def switch_stream(self, stream_id):
		old_act_id = self.active_stream

		if (stream_id > len(self.streams) - 1) or \
			(stream_id < 0) or \
			(stream_id == self.active_stream):
			return

		self.streams[self.active_stream].disableoutput(0)
		self.streams[stream_id].enableoutput(0)
		self.streams[stream_id].play()
		self.active_stream = stream_id


	def next_stream(self):
		new_id = self.active_stream + 1
		if new_id > len(self.streams) - 1:
			new_id = 0
		if new_id == self.active_stream:
			return
		self.switch_stream(new_id)


	def prev_stream(self):
		new_id = self.active_stream - 1
		if new_id < 0:
			new_id = len(self.streams) - 1
		if new_id == self.active_stream:
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
