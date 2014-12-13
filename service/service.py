import threading, logging
from multiprocessing.connection import Listener, Client

class Service(object):
	svc_keepalive = True

	svc_listener = None

	svc_host = ''
	svc_port = 0

	svc_thread = None

	def __init__(self):
		pass

	def svc_setup(self, host='localhost', port='6000'):
		self.svc_host = host
		self.svc_port = port
		self.svc_listener = Listener(address=(self.svc_host, self.svc_port))

	def svc_cleanup(self):
		self.svc_keepalive = False
		cl = Client(address=(self.svc_host,self.svc_port))
		cl.send('QUIT')
		cl.close()

	def svc_loop(self):
		self.svc_thread = threading.Thread(target=self._svc_loop)
		self.svc_thread.start()

	def _svc_loop(self):
		conn = self.svc_listener.accept()
		while self.svc_keepalive:

			try:
				msg = conn.recv()
			except EOFError:
				logging.warning("EOFError. This is usually because of the end of a received message. Restarting listener.")
				self.svc_listener.close()
				conn.close()
				self.svc_listener = Listener(address=(self.svc_host, self.svc_port))
				conn = self.svc_listener.accept()
				continue

			if msg == 'QUIT':
				conn.close()
				break
			elif isinstance(msg, list):
				ACT = msg[0]
				ARGS = msg[1]
				try:
					func = getattr(self, ACT)
					if callable(func):
						func(ARGS)
				except AttributeError as e:
					logging.error("No callable function '" + ACT + "'")
			else:
				print(">> Incoming: " + str(msg))
				try:
					func = getattr(self, msg)
					if callable(func):
						func()
				except AttributeError as e:
					logging.error("No callable function '" + ACT + "'")
		#endwhile
		self.svc_listener.close()
		return 0


