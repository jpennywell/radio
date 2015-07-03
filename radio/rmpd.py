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

	def __init__(self, host, port):
		self.rmpd_host = host
		self.rmpd_port = port

		super(StreamServer, self).__init__()

	def output_id(self):
		self.ready()
		return self.outputs()[0]['outputid']

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
	servers = []
	active_server = 0

	streams = []
	stream_map = {}

	def __init__(self, host, starting_port, num_servers):
		for p in range(0, num_servers):
			self.servers.append(StreamServer(host, starting_port + p))

	def register_stream(self, name, playlist, random = False, play_func = None):
		self.streams.append(Stream(name, playlist, random, play_func))

	def find_server(self):
		# Priority: unassigned server, then inactive, then active
		assigned_svrs = dict((v,k) for k,v in iter(self.stream_map.items()))
		unassigned_svrs = set(range(0, len(self.servers))) - set(assigned_svrs.keys())
		inactive_svrs = set(range(0, len(self.servers))) - set([self.active_server])

		if len(unassigned_svrs) > 0:
			svr_id = list(unassigned_svrs)[0]
			logging.debug("[ StreamManager ] : Found an UNASSIGNED server (#" + str(svr_id) + ")")
		elif len(inactive_svrs) > 0:
			svr_id = list(inactive_svrs)[0]
			logging.debug("[ StreamManager ] : Found an INACTIVE server (#" + str(svr_id) + ")")
		else:
			svr_id = self.active_server
			logging.debug("[ StreamManager ] : Found an IN-USE server (#" + str(svr_id) + ")")

		return svr_id


	def preload(self, stream_id):
		if stream_id in self.stream_map:
			logging.debug("[ StreamManager ] : Stream " + str(stream_id) + " already loaded on server " + str(self.stream_map[stream_id]))
			return

		try:
			stream = self.streams[stream_id]
		except IndexError:
			logging.debug("[ StreamManager ] : Stream " + str(stream_id) + " does not exist.")
			return False

		svr_id = self.find_server()
		# Unassign this server
		try:
			assigned_servers = dict((svr_id,stream_id) for stream_id,svr_id in self.stream_map.items())
			old_stream_id = assigned_servers[svr_id]
			self.stream_map.pop(old_stream_id)
		except (KeyError, IndexError):
			pass

		self.stream_map[stream_id] = svr_id

		svr = self.servers[svr_id]
		stream = self.streams[stream_id]
		svr.ready()
		svr.clear()
		try:
			svr.load(stream.playlist)
			logging.debug("[ StreamManager ] : Putting stream {streamid} on {server}".format(streamid = stream_id, server = svr_id))
		except mpd.CommandError:
			logging.debug("[ StreamManager ] : Could not load playlist '" + str(stream.playlist) + "'")


	def activate_stream(self, stream_id):
		if stream_id not in self.stream_map:
			self.preload(stream_id)

		svr_id = self.stream_map[stream_id]
#		if svr_id == self.active_server:
#			return

		old_svr_id = self.active_server
		old_svr = self.servers[old_svr_id]
		old_svr.ready()
		old_svr.pause()
		old_svr.disableoutput(old_svr.output_id())

		svr = self.servers[svr_id]
		svr.ready()
		svr.enableoutput(svr.output_id())
		svr.play()
		self.active_server = svr_id
		logging.debug("[ StreamManager ] : Moving servers: {old_server} ==> {new_server} with stream {streamid}".format(old_server = old_svr_id, new_server = svr_id, streamid = stream_id))


	def query_server(self, cmd):
		try:
			act_svr = self.servers[self.active_server]
			call = getattr(act_svr, cmd)
			return act_svr.call()
		except (AttributeError, TypeError):
			return False

#End of class StreamManager

