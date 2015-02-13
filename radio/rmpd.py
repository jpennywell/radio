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

