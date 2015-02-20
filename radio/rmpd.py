import mpd, logging, time

"""
CommandError

Pull in the mpd.CommandError exception.
"""
class CommandError(mpd.CommandError):
	pass


"""
StreamServer

This extends the mpd.MPDClient class.

Adds a 'ready' method that ensures that the client is still connected.
"""
class StreamServer(mpd.MPDClient):

	rmpd_host = ''
	rmpd_port = 0

	snd_output_id = 0


	def __init__(self, host, port):
		self.rmpd_host = host
		self.rmpd_port = port

		super(StreamServer, self).__init__()


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

	def play_by_seek(self):
		import time
		cur_hour = time.localtime()[3] - 6
		cur_time = time.localtime()[4]*60
		self.play(cur_hour)
		self.seekcur(cur_time)
	
# End of class StreamServer


"""
class Stream

A basic data-object for a stream.
"""
class Stream():
	name = ''
	playlist = ''
	random = False
	play_func = None

	def __init__(self, name, playlist, random = False, play_func = None):
		self.name = name
		self.playlist = playlist
		self.random = random
		self.play_func = play_func

# End of class Stream
		

"""
class StreamManager

Manages a set of streams (eg. stations)
and a set of servers, and manages the switching between
the streams, spread across the servers.

Either streams of servers can be larger.
"""
class StreamManager():
	num_servers = 2

	active_server = 0
	servers = []

	active_stream = 0
	streams = []

	stream_map_to = {}


	def __init__(self, host, starting_port):
		for i in range(0, self.num_servers):
			self.servers.append(StreamServer(host, starting_port + i))


	def add_stream(self, name, playlist, random = False, play_func = None):
		self.streams.append(Stream(name, playlist, random, play_func))


	def del_stream(self, stream_id):
		try:
			self.streams.pop(stream_id)
			return True
		except IndexError:
			return False


	def load_stream(self, stream_id):
		"""
		Make sure stream_id is not already assigned.
		"""
		if stream_id in self.stream_map_to:
			return

		try:
			"""
			Make sure that this stream exists.
			"""
			stream = self.streams[stream_id]
		except KeyError:
			return False

		"""
		Find an empty server, or at least the inactive one.
		Reverse the stream map to find assigned servers.
		If there are no servers unassigned, find an inactive one.
		If there is no inactive server (when self.num_servers == 1), then
		just load onto that one.
		"""
		assigned_svrs = dict((v,k) for k, v in iter(self.stream_map_to.items()))
		unassigned_svrs = set(range(0, self.num_servers)) - set(assigned_svrs.keys()) - set([self.active_server])
		try:
			svr_id = list(unassigned_svrs)[0]
		except IndexError:
			inactive_svrs = set(range(0, self.num_servers)) - set([self.active_server])
			try:
				svr_id = list(inactive_svrs)[0]
			except IndexError:
				svr_id = 0

		svr = self.servers[svr_id]
		svr.ready()
		svr.clear()
		svr.load(stream.playlist)

		self.stream_map_to[stream_id] = svr_id
		logging.debug("[ StreamManager ] : Putting stream " + str(stream_id) + " on server " + str(svr_id))


	def switch_stream(self, stream_id):
		if stream_id not in self.stream_map_to:
			self.load_stream(stream_id)	

		self.stop_stream(self.active_stream)
		self.start_stream(stream_id)
		self.active_stream = stream_id


	def start_stream(self, stream_id):
		try:
			svr_id = self.stream_map_to[stream_id]
			logging.debug("[ StreamManager ] : Moving to stream " + str(stream_id) + " (SVR: " + str(svr_id) + ")")
			svr = self.servers[svr_id]
			svr.ready()
			svr.enableoutput(svr.snd_output_id)
			try:
				play_func = getattr(svr, str(self.streams[stream_id].play_func))
				svr.play_func()
			except (AttributeError, TypeError):
				svr.play()
			self.active_server = svr_id
		except (KeyError, IndexError):
			return False
		except mpd.CommandError:
			return False


	def stop_stream(self, stream_id):
		try:
			svr_id = self.stream_map_to[stream_id]
			logging.debug("[ StreamManager ] : Moving from stream " + str(stream_id) + " (SVR: " + str(svr_id) + ")")
			svr = self.servers[svr_id]
			svr.ready()
			svr.disableoutput(svr.snd_output_id)
		except (KeyError, IndexError):
			return False
		except mpd.CommandError:
			return False


	def query_server(self, cmd):
		try:
			act_svr = self.servers[self.active_server]
			call = getattr(act_svr, cmd)
			return act_svr.call()
		except (AttributeError, TypeError):
			return False

# End of class StreamManager
