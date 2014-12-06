import threading
from multiprocessing.connection import Listener, Client

class Service(object):
	svc_keepalive = True

	svc_listener = None

	svc_host = ''
	svc_port = 0
	svc_key = ''

	svc_thread = None

	def __init__(self):
		pass

	def svc_setup(self, host='localhost', port='6000', authkey='secret'):
		self.svc_host = host
		self.svc_port = port
		self.svc_key = authkey
		self.svc_listener = Listener(address=(self.svc_host, self.svc_port), authkey=self.svc_key)

	def svc_cleanup(self):
		self.svc_keepalive = False
		cl = Client(address=(self.svc_host,self.svc_port), authkey=self.svc_key)
		cl.send('QUIT')
		cl.close()

	def svc_loop(self):
		self.svc_thread = threading.Thread(target=self._svc_loop)
		self.svc_thread.start()

	def _svc_loop(self):
                conn = self.svc_listener.accept()
                while self.svc_keepalive:
                        msg = conn.recv()
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
                                except Exception as e:
                                        pass
                        else:
                                try:
                                        func = getattr(self, msg)
                                        if callable(func):
                                                func()
                                except Exception as e:
					pass

                self.svc_listener.close()
                return 0


